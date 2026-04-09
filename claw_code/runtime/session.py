"""
会话管理 - 基于 claw-code session 管理
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ConversationMessage:
    """对话消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Session:
    """
    单个会话
    
    管理对话历史，支持压缩
    """
    session_id: str
    messages: list[ConversationMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)
    
    # 压缩配置
    MAX_MESSAGES: int = 100  # 超过此数量触发压缩
    MAX_TOKENS: int = 6000   # 目标 token 数（估算）
    
    def add_message(self, role: MessageRole, content: str, **kwargs) -> None:
        """添加消息"""
        msg = ConversationMessage(
            role=role,
            content=content,
            **kwargs
        )
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
    
    def add_user_message(self, content: str) -> None:
        self.add_message(MessageRole.USER, content)
    
    def add_assistant_message(self, content: str, **kwargs) -> None:
        self.add_message(MessageRole.ASSISTANT, content, **kwargs)
    
    def add_system_message(self, content: str) -> None:
        self.add_message(MessageRole.SYSTEM, content)
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, content: str) -> None:
        self.add_message(
            MessageRole.TOOL,
            content,
            tool_call_id=tool_call_id,
            tool_call_name=tool_name
        )
    
    def should_compress(self) -> bool:
        """检查是否需要压缩"""
        return len(self.messages) > self.MAX_MESSAGES
    
    def compress(self, keep_last: int = 10) -> list[ConversationMessage]:
        """
        压缩会话历史
        
        策略：保留系统消息 + 最近 N 条对话
        """
        if not self.should_compress():
            return self.messages
        
        # 分离系统消息和其他消息
        system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]
        
        # 保留最近的 keep_last 条
        kept_msgs = system_msgs + other_msgs[-keep_last:]
        
        # 记录压缩
        compressed_count = len(self.messages) - len(kept_msgs)
        if compressed_count > 0:
            self.messages = kept_msgs
            # 添加压缩标记
            self.messages.insert(
                len(system_msgs),
                ConversationMessage(
                    role=MessageRole.SYSTEM,
                    content=f"[{len(self.messages)} 条消息已压缩]"
                )
            )
        
        return self.messages
    
    def get_context_prompt(self) -> str:
        """获取上下文提示（用于构建 system prompt）"""
        lines = [f"会话历史 ({len(self.messages)} 条消息):"]
        
        for msg in self.messages[-20:]:  # 最近 20 条
            role_str = msg.role.value
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            lines.append(f"- [{role_str}] {content}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """序列化为 dict"""
        return {
            "session_id": self.session_id,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "name": m.name,
                    "tool_call_id": m.tool_call_id,
                    "tool_call_name": m.tool_call_name,
                    "timestamp": m.timestamp
                }
                for m in self.messages
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """从 dict 反序列化"""
        messages = [
            ConversationMessage(
                role=MessageRole(m["role"]),
                content=m["content"],
                name=m.get("name"),
                tool_call_id=m.get("tool_call_id"),
                tool_call_name=m.get("tool_call_name"),
                timestamp=m.get("timestamp", datetime.now().isoformat())
            )
            for m in data.get("messages", [])
        ]
        
        return cls(
            session_id=data["session_id"],
            messages=messages,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class SessionManager:
    """
    会话管理器
    
    管理多个会话，支持持久化
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self._sessions: dict[str, Session] = {}
        self.storage_path = storage_path
        self._load_from_disk()
    
    def get_or_create(self, session_id: str) -> Session:
        """获取或创建会话"""
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
        return self._sessions[session_id]
    
    def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def delete(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> list[str]:
        """列出所有会话 ID"""
        return list(self._sessions.keys())
    
    def _load_from_disk(self):
        """从磁盘加载会话"""
        if not self.storage_path:
            return
        
        import os
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
            
            for session_data in data.get("sessions", []):
                session = Session.from_dict(session_data)
                self._sessions[session.session_id] = session
        except Exception as e:
            print(f"Failed to load sessions: {e}")
    
    def save_to_disk(self):
        """保存会话到磁盘"""
        if not self.storage_path:
            return
        
        import os
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        
        data = {
            "sessions": [
                s.to_dict() for s in self._sessions.values()
            ]
        }
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def compress_all(self):
        """压缩所有会话"""
        for session in self._sessions.values():
            if session.should_compress():
                session.compress()
