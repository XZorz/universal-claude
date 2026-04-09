"""
工具注册表 - 基于 claw-code tools/lib.rs
管理Agent可用的工具集
"""
from dataclasses import dataclass
from typing import Any, Callable, Optional
import json


@dataclass
class ToolSpec:
    """工具规格定义"""
    name: str
    description: str
    input_schema: dict
    required_permission: str
    handler: Optional[Callable] = None


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None


class ToolRegistry:
    """
    工具注册表
    管理所有可用工具，类似 claw-code 的 GlobalToolRegistry
    """
    
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._aliases: dict[str, str] = {
            "read": "read_file",
            "write": "write_file",
            "edit": "edit_file",
            "glob": "glob_search",
            "grep": "grep_search",
        }
    
    def register(self, spec: ToolSpec) -> None:
        """注册工具"""
        self._tools[spec.name] = spec
    
    def register_function(
        self,
        name: str,
        description: str,
        schema: dict,
        permission: str,
        handler: Callable
    ) -> None:
        """便捷注册函数"""
        spec = ToolSpec(
            name=name,
            description=description,
            input_schema=schema,
            required_permission=permission,
            handler=handler
        )
        self.register(spec)
    
    def get(self, name: str) -> Optional[ToolSpec]:
        """获取工具规格"""
        resolved = self._aliases.get(name, name)
        return self._tools.get(resolved)
    
    def mcp_specs(self, allowed_tools: Optional[set] = None) -> list[dict]:
        """
        获取 MCP 协议格式的工具定义
        用于暴露给 LLM API
        """
        specs = []
        for name, spec in self._tools.items():
            if allowed_tools is not None and name not in allowed_tools:
                continue
            specs.append({
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.input_schema
                }
            })
        return specs
    
    def definitions(self, allowed_tools: Optional[set] = None) -> list[dict]:
        """兼容旧接口，同 mcp_specs"""
        return self.mcp_specs(allowed_tools)
    
    async def execute_async(self, name: str, input_data: dict) -> ToolResult:
        """异步执行工具"""
        spec = self.get(name)
        
        if not spec:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' not found"
            )
        
        if not spec.handler:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' has no handler"
            )
        
        try:
            # 调用处理器
            import asyncio
            if asyncio.iscoroutinefunction(spec.handler):
                result = await spec.handler(**input_data)
            else:
                result = spec.handler(**input_data)
            
            # 处理返回结果
            if isinstance(result, dict):
                output = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                output = str(result)
            
            return ToolResult(success=True, output=output)
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution failed: {str(e)}"
            )
    
    def execute(self, name: str, input_data: dict) -> ToolResult:
        """同步执行工具（兼容旧接口，内部调用异步版本）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在运行中，创建 task
                future = asyncio.ensure_future(self.execute_async(name, input_data))
                return asyncio.run_coroutine_threadsafe(future, loop).result()
            else:
                return asyncio.run(self.execute_async(name, input_data))
        except RuntimeError:
            # 没有事件循环
            return asyncio.run(self.execute_async(name, input_data))
    
    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self._tools.keys())


# === 全局注册表（仅基础工具，不含八字）===

_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册表（懒加载）"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        _register_default_tools(_global_registry)
    return _global_registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """注册默认工具（基础文件操作）"""
    
    def read_file_handler(path: str, offset: int = 1, limit: int = 500) -> dict:
        """读取文件"""
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
            total = len(lines)
            lines = lines[offset-1:offset-1+limit]
            return {"content": "".join(lines), "total_lines": total}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_function(
        name="read_file",
        description="读取文本文件内容",
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "default": 1},
                "limit": {"type": "integer", "default": 500}
            },
            "required": ["path"]
        },
        permission="read_only",
        handler=read_file_handler
    )
    
    def write_file_handler(path: str, content: str) -> str:
        """写入文件"""
        import os
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件已写入: {path}"
    
    registry.register_function(
        name="write_file",
        description="写入文本文件",
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        },
        permission="workspace_write",
        handler=write_file_handler
    )
    
    def glob_search_handler(pattern: str, path: str = ".") -> list:
        """按模式搜索文件"""
        import os
        import fnmatch
        matches = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__']]
            for f in files:
                if fnmatch.fnmatch(f, pattern):
                    matches.append(os.path.join(root, f))
        return matches[:50]
    
    registry.register_function(
        name="glob_search",
        description="按文件名模式搜索文件",
        schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."}
            },
            "required": ["pattern"]
        },
        permission="read_only",
        handler=glob_search_handler
    )
    
    def grep_search_handler(pattern: str, path: str = ".") -> list:
        """正则搜索文件内容"""
        import os
        import re
        matches = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__']]
            for f in files:
                if f.endswith(('.py', '.md', '.txt', '.yaml', '.json')):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, encoding="utf-8", errors="ignore") as file:
                            for i, line in enumerate(file, 1):
                                if re.search(pattern, line):
                                    matches.append(f"{fp}:{i}: {line.rstrip()}")
                    except:
                        pass
        return matches[:50]
    
    registry.register_function(
        name="grep_search",
        description="正则搜索文件内容",
        schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."}
            },
            "required": ["pattern"]
        },
        permission="read_only",
        handler=grep_search_handler
    )
