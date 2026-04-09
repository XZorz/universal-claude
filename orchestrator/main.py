"""
Orchestrator 入口

统一入口，组合所有组件
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator.llm_client import create_llm_client, LLMClient
from orchestrator.agent_loader import AgentLoader
from orchestrator.agent_executor import AgentExecutor
from claw_code.runtime import (
    ToolRegistry, 
    TieredPermissionPolicy, 
    HookRunner, 
    HookEvent, 
    HookResult,
    SessionManager
)


class Orchestrator:
    """
    统一编排器
    
    组合:
    - LLM 客户端 (DeepSeek/Claude)
    - Agent 加载器
    - Agent 执行器
    - 工具注册表
    - 权限策略
    - 钩子运行器
    - 会话管理器
    """
    
    def __init__(
        self,
        llm_provider: str = "deepseek",
        api_key: str = None,
        agents_dir: str = None,
        is_paid: bool = False,
        storage_path: str = None
    ):
        # 1. LLM 客户端
        self.llm = create_llm_client(provider=llm_provider, api_key=api_key)
        
        # 2. Agent 加载器
        self.agent_loader = AgentLoader(agents_dir=agents_dir)
        
        # 3. ✅ 工具注册表（使用完整八字工具）
        from orchestrator import tools as bazi_tools
        self.tool_registry = self._create_tool_registry(bazi_tools)
        
        # 4. 权限策略
        self.permission = TieredPermissionPolicy(is_paid=is_paid)
        
        # 5. 会话管理器
        self.session_manager = SessionManager(storage_path=storage_path)
        
        # 6. 钩子运行器
        self.hooks = self._create_hooks()
        
        # 7. Agent 执行器
        self.executor = AgentExecutor(
            llm_client=self.llm,
            agent_loader=self.agent_loader,
            permission_policy=self.permission,
            tool_registry=self.tool_registry,
            hook_runner=self.hooks
        )
        # ✅ 连接 SessionManager
        self.executor.set_session_manager(self.session_manager)
        
        self.is_paid = is_paid
    
    def _create_tool_registry(self, bazi_tools) -> ToolRegistry:
        """创建并填充工具注册表"""
        registry = ToolRegistry()
        
        # === 基础工具 ===
        registry.register_function(
            name="read_file",
            description="读取文本文件内容",
            schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            },
            permission="read_only",
            handler=self._handler_read_file
        )
        
        registry.register_function(
            name="write_file",
            description="写入文本文件",
            schema={
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"]
            },
            permission="workspace_write",
            handler=self._handler_write_file
        )
        
        registry.register_function(
            name="glob_search",
            description="按模式搜索文件",
            schema={
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"]
            },
            permission="read_only",
            handler=self._handler_glob
        )
        
        registry.register_function(
            name="grep_search",
            description="正则搜索文件内容",
            schema={
                "type": "object",
                "properties": {"pattern": {"type": "string"}, "path": {"type": "string", "default": "."}},
                "required": ["pattern"]
            },
            permission="read_only",
            handler=self._handler_grep
        )
        
        # === 八字工具（来自 orchestrator/tools.py）===
        registry.register_function(
            name="bazi_calculation",
            description="根据出生日期计算完整八字命盘",
            schema={
                "type": "object",
                "properties": {
                    "birth_date": {"type": "string"},
                    "birth_time": {"type": "string", "default": "00:00"}
                },
                "required": ["birth_date"]
            },
            permission="read_only",
            handler=bazi_tools.bazi_calculation
        )
        
        registry.register_function(
            name="dayun_calculation",
            description="计算大运",
            schema={
                "type": "object",
                "properties": {
                    "birth_date": {"type": "string"},
                    "birth_time": {"type": "string", "default": "00:00"},
                    "target_year": {"type": "integer"}
                },
                "required": ["birth_date"]
            },
            permission="read_only",
            handler=bazi_tools.dayun_calculation
        )
        
        registry.register_function(
            name="fortune_reading",
            description="解读八字运势",
            schema={
                "type": "object",
                "properties": {
                    "bazi": {"type": "string"},
                    "date": {"type": "string"},
                    "birth_date": {"type": "string"},
                    "birth_time": {"type": "string", "default": "00:00"}
                }
            },
            permission="read_only",
            handler=bazi_tools.fortune_reading
        )
        
        registry.register_function(
            name="five_elements_analysis",
            description="五行旺衰分析",
            schema={
                "type": "object",
                "properties": {
                    "bazi": {"type": "string"},
                    "birth_date": {"type": "string"},
                    "birth_time": {"type": "string", "default": "00:00"}
                }
            },
            permission="read_only",
            handler=bazi_tools.five_elements_analysis
        )
        
        registry.register_function(
            name="daily_fortune",
            description="每日运势分析",
            schema={
                "type": "object",
                "properties": {"date": {"type": "string"}}
            },
            permission="read_only",
            handler=bazi_tools.daily_fortune
        )
        
        registry.register_function(
            name="full_analysis",
            description="完整命局分析",
            schema={
                "type": "object",
                "properties": {
                    "birth_date": {"type": "string"},
                    "birth_time": {"type": "string", "default": "00:00"},
                    "target_year": {"type": "integer"}
                },
                "required": ["birth_date"]
            },
            permission="read_only",
            handler=bazi_tools.full_analysis
        )
        
        return registry
    
    # ========== 基础工具处理器 ==========
    
    def _handler_read_file(self, path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as f:
                return {"success": True, "output": f.read()[:5000]}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def _handler_write_file(self, path: str, content: str) -> dict:
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "output": f"写入成功: {path}"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def _handler_glob(self, pattern: str) -> dict:
        import glob
        try:
            matches = glob.glob(pattern, recursive=True)[:50]
            return {"success": True, "output": "\n".join(matches) or "无匹配"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def _handler_grep(self, pattern: str, path: str = ".") -> dict:
        import re
        try:
            results = []
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__']]
                for file in files:
                    if file.endswith(('.py', '.md', '.txt', '.yaml', '.json')):
                        fpath = os.path.join(root, file)
                        try:
                            with open(fpath, encoding="utf-8", errors="ignore") as f:
                                for i, line in enumerate(f, 1):
                                    if re.search(pattern, line):
                                        results.append(f"{fpath}:{i}: {line.rstrip()}")
                        except:
                            pass
            return {"success": True, "output": "\n".join(results[:100]) or "无匹配结果"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    def _create_hooks(self) -> HookRunner:
        hooks = HookRunner()
        
        hooks.register_hook(
            name="pre_tool_logger",
            event=HookEvent.PRE_TOOL_USE,
            handler=lambda ctx: print(f"🔧 执行工具: {ctx.get('tool_name')}") or HookResult()
        )
        
        hooks.register_hook(
            name="post_tool_logger",
            event=HookEvent.POST_TOOL_USE,
            handler=lambda ctx: print(f"✅ {ctx.get('tool_name')}") or HookResult()
        )
        
        return hooks
    
    async def run(self, agent_name: str, user_input: str, session_id: str = "default", user_id: str = None):
        """运行 Agent"""
        return await self.executor.execute(
            agent_name=agent_name,
            user_input=user_input,
            session_id=session_id,
            user_id=user_id
        )
    
    async def run_stream(self, agent_name: str, user_input: str, session_id: str = "default", user_id: str = None):
        """流式运行 Agent"""
        async for chunk in await self.executor.execute(
            agent_name=agent_name,
            user_input=user_input,
            session_id=session_id,
            stream=True,
            user_id=user_id
        ):
            yield chunk
    
    def list_agents(self) -> list:
        return self.agent_loader.list_agents()
    
    def list_tools(self) -> list:
        return self.tool_registry.list_tools()
    
    def get_quota_status(self, user_id: str) -> dict:
        return self.executor.get_quota_status(user_id)
    
    def save_sessions(self):
        self.session_manager.save_to_disk()
    
    async def close(self):
        self.save_sessions()
        if hasattr(self.llm, 'close'):
            await self.llm.close()


class SyncOrchestrator:
    """同步版本"""
    
    def __init__(self, **kwargs):
        self._async = Orchestrator(**kwargs)
    
    def run(self, agent_name: str, user_input: str, session_id: str = "default", user_id: str = None):
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                self._async.run(agent_name, user_input, session_id, user_id)
            )
            return future.result()
    
    def list_agents(self) -> list:
        return self._async.list_agents()
    
    def list_tools(self) -> list:
        return self._async.list_tools()
    
    def get_quota_status(self, user_id: str) -> dict:
        return self._async.get_quota_status(user_id)
    
    def save_sessions(self):
        self._async.save_sessions()
    
    def close(self):
        asyncio.run(self._async.close())


_orchestrator = None


def get_orchestrator(is_paid: bool = False) -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(is_paid=is_paid)
    return _orchestrator


async def run_cli():
    orch = get_orchestrator()
    print("🤖 Universal Claude Orchestrator")
    print(f"可用 Agent: {len(orch.list_agents())} 个")
    print(f"可用工具: {', '.join(orch.list_tools())}")
    print("输入 'quit' 退出\n")
    
    session_id = "cli_session"
    
    while True:
        try:
            user_input = input("你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit", "q"]:
                print("再见!")
                break
            
            print("思考中...")
            response = await orch.run("planner", user_input, session_id)
            print(f"\nAgent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")
    
    await orch.close()


if __name__ == "__main__":
    asyncio.run(run_cli())
