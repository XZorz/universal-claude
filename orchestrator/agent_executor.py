"""
Agent 执行器 - Agent 执行循环的核心编排
"""
import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, AsyncIterator

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .llm_client import LLMClient, LLMMessage, ToolCall, create_llm_client
from .agent_loader import AgentLoader, AgentDefinition
from claw_code.runtime import ToolResult, HookRunner, PermissionPolicy, TieredPermissionPolicy, HookEvent, HookResult


@dataclass
class ExecutionContext:
    """执行上下文"""
    session_id: str
    agent_name: str
    user_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class AgentExecutor:
    """
    Agent 执行循环
    
    核心流程:
    1. 加载 Agent 定义
    2. 权限检查（配额 + 工具权限）
    3. 获取/创建会话
    4. 构建消息列表
    5. 调用 LLM
    6. 处理工具调用
    7. 返回结果
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        agent_loader: AgentLoader = None,
        permission_policy: PermissionPolicy = None,
        tool_registry = None,
        hook_runner: HookRunner = None
    ):
        self.llm = llm_client
        self.loader = agent_loader or AgentLoader()
        self.permission = permission_policy or TieredPermissionPolicy()
        self.tool_registry = tool_registry
        self.hooks = hook_runner or HookRunner()
        self.session_manager = None  # 由 Orchestrator 设置
    
    def set_session_manager(self, session_manager):
        """设置会话管理器"""
        self.session_manager = session_manager
    
    async def execute(
        self,
        agent_name: str,
        user_input: str,
        session_id: str = "default",
        stream: bool = False,
        user_id: str = None
    ) -> str:
        """
        执行 Agent
        """
        # 0. 配额检查
        if user_id:
            quota_result = self.permission.check_quota(user_id)
            if not quota_result.allowed:
                return f"⚠️ 今日配额已用完（免费用户每天3次）。{quota_result.reason}"
        
        # 1. 加载 Agent
        agent = self.loader.load(agent_name)
        
        # 2. 获取会话
        session = self.session_manager.get_or_create(session_id)
        session.add_user_message(user_input)
        
        # 3. 构建消息
        messages = self._build_messages(agent, session)
        
        # 4. 获取工具定义
        tools = None
        if self.tool_registry:
            tools = self.tool_registry.definitions(agent.allowed_tools)
        
        # 5. 调用 LLM
        response = await self.llm.chat(
            messages=messages,
            model=self._get_model(agent),
            tools=tools,
            temperature=self._get_temperature(agent)
        )
        
        # 6. 处理响应
        if stream:
            return await self._handle_stream(response, agent, session_id, messages, tools)
        else:
            return await self._handle_response(response, agent, session_id, messages, tools, user_id)
    
    async def _handle_response(
        self,
        response,
        agent: AgentDefinition,
        session_id: str,
        messages: list,
        tools: list = None,
        user_id: str = None
    ) -> str:
        """处理普通响应（含工具调用）"""
        session = self.session_manager.get(session_id)
        
        while response.tool_calls:
            for tool_call in response.tool_calls:
                # ✅ 工具权限检查
                auth_result = self.permission.authorize(tool_call.name)
                if not auth_result.allowed:
                    error_msg = f"⚠️ 权限不足：{auth_result.reason}"
                    session.add_assistant_message(error_msg)
                    return error_msg
                
                # PreHook
                self._run_pre_hook(tool_call.name, tool_call.input, session_id)
                
                # ✅ 执行工具（异步）
                tool_result = await self._execute_tool(tool_call, tools)
                
                # ✅ 记录使用
                if user_id:
                    self.permission.record_usage(user_id)
                
                # PostHook
                self._run_post_hook(tool_call.name, tool_result, session_id)
                
                # 添加工具结果
                tool_msg = LLMMessage(
                    role="tool",
                    content=f"[tool: {tool_call.name}] {tool_result.output}"
                )
                messages.append(tool_msg)
                session.add_tool_message(tool_call.name, tool_result.output)
            
            # 继续 LLM 调用
            response = await self.llm.chat(
                messages=messages,
                model=self._get_model(agent),
                tools=tools
            )
        
        # 添加助手回复
        final_content = response.content
        session.add_assistant_message(final_content)
        
        return final_content
    
    async def _handle_stream(
        self,
        response,
        agent: AgentDefinition,
        session_id: str,
        messages: list,
        tools: list = None
    ) -> AsyncIterator[str]:
        """
        处理流式响应
        
        注意：当前实现不支持流式工具调用。
        如果 LLM 返回 tool_calls，会切换到普通模式处理。
        """
        # 检查是否有工具调用
        if response.tool_calls:
            # 切换到非流式处理
            result = await self._handle_response(
                response, agent, session_id, messages, tools
            )
            yield result
            return
        
        # 纯流式文本响应
        output = []
        async for chunk in self.llm.stream(
            messages=messages,
            model=self._get_model(agent),
            tools=tools
        ):
            output.append(chunk)
            yield chunk
        
        full_content = "".join(output)
        session = self.session_manager.get(session_id)
        if session:
            session.add_assistant_message(full_content)
    
    async def _execute_tool(self, tool_call: ToolCall, tools: list = None) -> ToolResult:
        """执行工具（异步）"""
        if not self.tool_registry:
            return ToolResult(
                success=False,
                output="",
                error="Tool registry not configured"
            )
        
        # ✅ 调用异步版本
        result = await self.tool_registry.execute_async(
            tool_call.name,
            tool_call.input or {}
        )
        
        return ToolResult(
            success=result.success,
            output=result.output,
            error=result.error
        )
    
    def _run_pre_hook(self, tool_name: str, tool_input: dict, session_id: str):
        """PreHook"""
        result = self.hooks.run(
            HookEvent.PRE_TOOL_USE,
            {"tool_name": tool_name, "tool_input": tool_input, "session_id": session_id}
        )
        if result.denied:
            print(f"⚠️ PreHook 拒绝: {tool_name}")
    
    def _run_post_hook(self, tool_name: str, tool_result: ToolResult, session_id: str):
        """PostHook"""
        self.hooks.run(
            HookEvent.POST_TOOL_USE,
            {"tool_name": tool_name, "tool_result": tool_result, "session_id": session_id}
        )
    
    def _build_messages(self, agent: AgentDefinition, session) -> list:
        """构建消息列表"""
        messages = []
        
        if agent.system_prompt:
            messages.append(LLMMessage(role="system", content=agent.system_prompt))
        
        for msg in session.messages:
            role = msg.role.value if hasattr(msg.role, 'value') else msg.role
            messages.append(LLMMessage(role=role, content=msg.content))
        
        return messages
    
    def _get_model(self, agent: AgentDefinition) -> str:
        return agent.metadata.get("model", "deepseek-chat")
    
    def _get_temperature(self, agent: AgentDefinition) -> float:
        return agent.metadata.get("temperature", 0.7)
    
    def get_session_history(self, session_id: str) -> list:
        """获取会话历史"""
        session = self.session_manager.get(session_id)
        if not session:
            return []
        return [
            {
                "role": m.role.value if hasattr(m.role, 'value') else m.role,
                "content": m.content,
                "timestamp": m.timestamp
            }
            for m in session.messages
        ]
    
    def clear_session(self, session_id: str):
        """清除会话"""
        self.session_manager.delete(session_id)
    
    def get_quota_status(self, user_id: str) -> dict:
        """获取配额状态"""
        result = self.permission.check_quota(user_id)
        is_paid = getattr(self.permission, 'is_paid', False)
        usage = self.permission.daily_usage.get(user_id, 0)
        limit = getattr(self.permission, 'FREE_DAILY_LIMIT', 3)
        
        return {
            "user_id": user_id,
            "is_paid": is_paid,
            "allowed": result.allowed,
            "usage_today": usage,
            "daily_limit": limit,
            "remaining": max(0, limit - usage)
        }


class MultiAgentExecutor(AgentExecutor):
    """多 Agent 编排器 - 支持团队协作"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sub_agents: dict[str, 'AgentExecutor'] = {}
    
    def register_sub_agent(self, name: str, executor: 'AgentExecutor'):
        """注册子 Agent"""
        self._sub_agents[name] = executor
    
    async def execute_with_team(
        self,
        task: str,
        team_config: dict,
        session_id: str = "team"
    ) -> str:
        """团队协作执行"""
        planner = self._sub_agents.get("planner")
        if not planner:
            return "Planner not available"
        
        plan = await planner.execute(
            "planner",
            f"分解任务: {task}",
            session_id=f"{session_id}_planner"
        )
        
        results = []
        for member in team_config.get("members", []):
            executor = self._sub_agents.get(member)
            if executor:
                result = await executor.execute(
                    member,
                    f"执行任务: {plan}",
                    session_id=f"{session_id}_{member}"
                )
                results.append(result)
        
        return "\n\n".join(results)
