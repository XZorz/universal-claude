"""
钩子系统 - 基于 claw-code hooks.rs
支持PreHook/PostHook自动化
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional
import json


class HookEvent(str, Enum):
    """钩子事件类型"""
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    PRE_COMMIT = "pre_commit"
    POST_COMMIT = "post_commit"
    SESSION_START = "session_start"
    SESSION_STOP = "session_stop"


@dataclass
class HookResult:
    """钩子执行结果"""
    denied: bool = False
    messages: list[str] = field(default_factory=list)
    modified_output: Optional[str] = None


class Hook:
    """单个钩子"""
    
    def __init__(
        self,
        name: str,
        event: HookEvent,
        handler: Callable[[dict], HookResult],
        enabled: bool = True
    ):
        self.name = name
        self.event = event
        self.handler = handler
        self.enabled = enabled


class HookRunner:
    """
    钩子运行器 - 管理所有钩子并执行
    类似claw-code的HookRunner
    """
    
    def __init__(self):
        self._hooks: list[Hook] = []
    
    def register(self, hook: Hook) -> None:
        """注册钩子"""
        self._hooks.append(hook)
    
    def register_hook(
        self,
        name: str,
        event: HookEvent,
        handler: Callable[[dict], HookResult],
        enabled: bool = True
    ) -> None:
        """便捷注册"""
        hook = Hook(name=name, event=event, handler=handler, enabled=enabled)
        self.register(hook)
    
    def run(self, event: HookEvent, context: dict) -> HookResult:
        """执行指定事件的所有钩子"""
        result = HookResult()
        
        for hook in self._hooks:
            if hook.event == event and hook.enabled:
                hook_result = hook.handler(context)
                result.messages.extend(hook_result.messages)
                
                if hook_result.denied:
                    result.denied = True
                
                if hook_result.modified_output:
                    result.modified_output = hook_result.modified_output
        
        return result
    
    def list_hooks(self) -> list[dict]:
        """列出所有钩子"""
        return [
            {
                "name": h.name,
                "event": h.event.value,
                "enabled": h.enabled
            }
            for h in self._hooks
        ]


# 全局钩子运行器
_global_runner: Optional[HookRunner] = None

def get_global_runner() -> HookRunner:
    """获取全局钩子运行器"""
    global _global_runner
    if _global_runner is None:
        _global_runner = HookRunner()
        _register_default_hooks(_global_runner)
    return _global_runner


def _register_default_hooks(runner: HookRunner) -> None:
    """注册默认钩子"""
    
    # PreToolUse钩子 - 工具执行前
    def pre_tool_context_check(context: dict) -> HookResult:
        tool_name = context.get("tool_name", "")
        
        # 检查危险工具
        dangerous = ["bash", "rm", "delete"]
        for dangerous_tool in dangerous:
            if dangerous_tool in tool_name.lower():
                return HookResult(
                    denied=False,
                    messages=[f"⚠️ 注意: 即将执行可能危险的操作: {tool_name}"]
                )
        
        return HookResult()
    
    runner.register_hook(
        name="pre_tool_safety_check",
        event=HookEvent.PRE_TOOL_USE,
        handler=pre_tool_context_check
    )
    
    # PostToolUse钩子 - 工具执行后
    def post_tool_log(context: dict) -> HookResult:
        tool_name = context.get("tool_name", "")
        success = context.get("success", True)
        
        if not success:
            return HookResult(
                messages=[f"❌ 工具 {tool_name} 执行失败"]
            )
        
        return HookResult()
    
    runner.register_hook(
        name="post_tool_logger",
        event=HookEvent.POST_TOOL_USE,
        handler=post_tool_log
    )


# ============ 便捷装饰器 ============

def pre_tool(name: str = ""):
    """PreToolUse钩子装饰器"""
    def decorator(func: Callable[[dict], HookResult]):
        runner = get_global_runner()
        runner.register_hook(
            name=name or func.__name__,
            event=HookEvent.PRE_TOOL_USE,
            handler=func
        )
        return func
    return decorator


def post_tool(name: str = ""):
    """PostToolUse钩子装饰器"""
    def decorator(func: Callable[[dict], HookResult]):
        runner = get_global_runner()
        runner.register_hook(
            name=name or func.__name__,
            event=HookEvent.POST_TOOL_USE,
            handler=func
        )
        return func
    return decorator
