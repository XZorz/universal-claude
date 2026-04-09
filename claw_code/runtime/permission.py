"""
权限系统 - 基于 claw-code permissions.rs
管理Agent和用户对工具的访问权限
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PermissionMode(str, Enum):
    """权限模式"""
    READ_ONLY = "read_only"           # 只读
    WORKSPACE_WRITE = "workspace_write"  # 可写工作区
    DANGER_FULL_ACCESS = "danger_full_access"  # 完全访问
    PROMPT = "prompt"                 # 每次询问
    ALLOW = "allow"                  # 允许


@dataclass
class PermissionRequest:
    """权限请求"""
    tool_name: str
    input_data: str
    session_id: str
    user_id: Optional[str] = None


@dataclass
class PermissionResult:
    """权限结果"""
    allowed: bool
    reason: str
    mode_used: PermissionMode


class PermissionPolicy:
    """
    权限策略 - 决定是否允许工具调用
    类似claw-code的PermissionPolicy
    """
    
    # 工具所需权限映射
    TOOL_REQUIREMENTS = {
        # 只读工具
        "read_file": PermissionMode.READ_ONLY,
        "glob_search": PermissionMode.READ_ONLY,
        "grep_search": PermissionMode.READ_ONLY,
        "web_fetch": PermissionMode.READ_ONLY,
        "web_search": PermissionMode.READ_ONLY,
        "bazi_calculation": PermissionMode.READ_ONLY,
        "fortune_reading": PermissionMode.READ_ONLY,
        
        # 需要写权限的工具
        "write_file": PermissionMode.WORKSPACE_WRITE,
        "edit_file": PermissionMode.WORKSPACE_WRITE,
        
        # 危险工具 - 需要完全访问
        "bash": PermissionMode.DANGER_FULL_ACCESS,
        "agent": PermissionMode.DANGER_FULL_ACCESS,
        "subagent": PermissionMode.DANGER_FULL_ACCESS,
    }
    
    def __init__(self, mode: PermissionMode = PermissionMode.READ_ONLY):
        self.active_mode = mode
    
    def set_mode(self, mode: PermissionMode) -> None:
        """设置权限模式"""
        self.active_mode = mode
    
    def get_required_permission(self, tool_name: str) -> PermissionMode:
        """获取工具所需的权限"""
        return self.TOOL_REQUIREMENTS.get(tool_name, PermissionMode.READ_ONLY)
    
    def authorize(self, tool_name: str, input_data: str = "") -> PermissionResult:
        """
        授权检查 - 类似claw-code的authorize逻辑
        """
        required = self.get_required_permission(tool_name)
        
        # 权限等级：READ_ONLY < WORKSPACE_WRITE < DANGER_FULL_ACCESS < PROMPT < ALLOW
        mode_hierarchy = {
            PermissionMode.READ_ONLY: 0,
            PermissionMode.WORKSPACE_WRITE: 1,
            PermissionMode.DANGER_FULL_ACCESS: 2,
            PermissionMode.PROMPT: 3,
            PermissionMode.ALLOW: 4,
        }
        
        user_level = mode_hierarchy.get(self.active_mode, 0)
        required_level = mode_hierarchy.get(required, 0)
        
        if user_level >= required_level:
            return PermissionResult(
                allowed=True,
                reason=f"Mode {self.active_mode.value} >= required {required.value}",
                mode_used=self.active_mode
            )
        else:
            return PermissionResult(
                allowed=False,
                reason=f"Mode {self.active_mode.value} < required {required.value}",
                mode_used=self.active_mode
            )


class TieredPermissionPolicy(PermissionPolicy):
    """
    分层权限策略 - 免费用户3次/天，付费用户无限
    """
    
    # 免费用户配额
    FREE_DAILY_LIMIT = 3
    
    def __init__(self, mode: PermissionMode = PermissionMode.READ_ONLY, is_paid: bool = False):
        super().__init__(mode)
        self.is_paid = is_paid
        self.daily_usage: dict[str, int] = {}  # session_id -> 使用次数
    
    def check_quota(self, session_id: str) -> PermissionResult:
        """检查配额"""
        if self.is_paid:
            return PermissionResult(allowed=True, reason="Paid user", mode_used=self.active_mode)
        
        usage = self.daily_usage.get(session_id, 0)
        if usage >= self.FREE_DAILY_LIMIT:
            return PermissionResult(
                allowed=False,
                reason=f"Free tier limit reached ({self.FREE_DAILY_LIMIT}/day)",
                mode_used=self.active_mode
            )
        
        return PermissionResult(allowed=True, reason=f"Quota available ({self.FREE_DAILY_LIMIT - usage} left)", mode_used=self.active_mode)
    
    def record_usage(self, session_id: str) -> None:
        """记录使用"""
        self.daily_usage[session_id] = self.daily_usage.get(session_id, 0) + 1
    
    def reset_daily(self) -> None:
        """重置每日配额"""
        self.daily_usage.clear()
