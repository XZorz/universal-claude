"""
LLM 客户端 - 对接 DeepSeek / Claude 等 API
"""
import os
import json
import httpx
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator, Any
from abc import ABC, abstractmethod


@dataclass
class LLMMessage:
    role: str  # system / user / assistant
    content: str
    name: Optional[str] = None


@dataclass  
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    content: str
    tool_calls: Optional[list[ToolCall]] = None
    usage: dict = field(default_factory=dict)


class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: list[dict] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        pass


class DeepSeekClient(LLMClient):
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(
        self,
        messages: list[LLMMessage],
        model: str = "deepseek-chat",
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """发送对话请求"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content, "name": m.name}
                for m in messages
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            payload["tools"] = tools
        
        response = await self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 解析响应
        choice = data["choices"][0]
        message = choice["message"]
        
        tool_calls = self._parse_tool_calls(message)
        
        return LLMResponse(
            content=message.get("content", "") or "",
            tool_calls=tool_calls,
            usage=data.get("usage", {})
        )
    
    def _parse_tool_calls(self, message: dict) -> Optional[list[ToolCall]]:
        """解析工具调用"""
        if "tool_calls" not in message:
            return None
        
        tool_calls = []
        for tc in message["tool_calls"]:
            # 解析 function arguments（可能是 string 或 dict）
            args = tc.get("function", {}).get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            
            tool_calls.append(ToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                input=args
            ))
        
        return tool_calls if tool_calls else None
    
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str = "deepseek-chat",
        tools: list[dict] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """流式响应"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content, "name": m.name}
                for m in messages
            ],
            "temperature": temperature,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = tools
        
        async with self._client.stream("POST", url, json=payload, headers=headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    if line == "data: [DONE]":
                        break
                    data = json.loads(line[6:])
                    delta = data["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
    
    async def close(self):
        await self._client.aclose()


class ClaudeClient(LLMClient):
    """Anthropic Claude API 客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=60.0)
    
    async def chat(
        self,
        messages: list[LLMMessage],
        model: str = "claude-sonnet-4-6",
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Claude 使用 messages API"""
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # 分离 system 消息
        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})
        
        payload: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        if tools:
            payload["tools"] = tools
        
        response = await self._client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # 解析 tool_calls
        tool_calls = None
        if "tool_calls" in data:
            tool_calls = []
            for tc in data["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    input=tc.get("input", {})
                ))
        
        # 解析 content
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content = block.get("text", "")
                break
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=data.get("usage", {})
        )
    
    async def stream(self, messages, model, tools=None, temperature=0.7):
        # Claude 流式实现较复杂，暂不支持
        raise NotImplementedError("Claude stream not implemented")
    
    async def close(self):
        await self._client.aclose()


# 客户端工厂
def create_llm_client(provider: str = "deepseek", **kwargs) -> LLMClient:
    """创建 LLM 客户端"""
    if provider == "deepseek":
        return DeepSeekClient(**kwargs)
    elif provider == "claude":
        return ClaudeClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
