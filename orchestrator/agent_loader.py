"""
Agent 加载器 - 从 MD 文件加载 Agent 定义
"""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AgentDefinition:
    """Agent 定义"""
    name: str
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    metadata: dict = field(default_factory=dict)


class AgentLoader:
    """
    加载 MD 格式的 Agent 定义
    
    支持两种格式:
    1. YAML Frontmatter (ECC 格式)
    2. 纯文本系统提示词
    """
    
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )
    
    def __init__(self, agents_dir: str = None):
        self.agents_dir = agents_dir or self._default_agents_dir()
    
    def _default_agents_dir(self) -> str:
        """获取默认 agents 目录"""
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "ecc", "agents"
        )
    
    def load(self, name: str) -> AgentDefinition:
        """加载指定的 Agent"""
        path = self._find_agent_path(name)
        if not path:
            raise FileNotFoundError(f"Agent '{name}' not found")
        
        return self._parse_file(path)
    
    def _find_agent_path(self, name: str) -> Optional[str]:
        """查找 Agent 文件路径"""
        # 支持多种后缀
        for suffix in [".md", ".json", ""]:
            path = os.path.join(self.agents_dir, f"{name}{suffix}")
            if os.path.exists(path):
                return path
        return None
    
    def _parse_file(self, path: str) -> AgentDefinition:
        """解析 Agent 文件"""
        with open(path, encoding="utf-8") as f:
            content = f.read()
        
        # 尝试解析 frontmatter
        match = self.FRONTMATTER_PATTERN.match(content)
        
        if match:
            return self._parse_frontmatter(match.group(1), match.group(2))
        else:
            # 无 frontmatter，整个内容作为 system prompt
            name = Path(path).stem
            return AgentDefinition(
                name=name,
                description=f"Agent: {name}",
                system_prompt=content
            )
    
    def _parse_frontmatter(self, frontmatter: str, body: str) -> AgentDefinition:
        """解析 YAML frontmatter"""
        import yaml
        
        data = yaml.safe_load(frontmatter) or {}
        
        # 解析 allowed_tools
        allowed_tools = data.get("allowedTools", [])
        if isinstance(allowed_tools, str):
            allowed_tools = [allowed_tools]
        
        return AgentDefinition(
            name=data.get("name", ""),
            description=data.get("description", ""),
            allowed_tools=allowed_tools,
            system_prompt=body.strip(),
            metadata=data
        )
    
    def list_agents(self) -> list[str]:
        """列出所有可用的 Agent"""
        if not os.path.exists(self.agents_dir):
            return []
        
        agents = []
        for f in os.listdir(self.agents_dir):
            if f.endswith((".md", ".json")) and not f.startswith("_"):
                name = f.rsplit(".", 1)[0]
                agents.append(name)
        
        return sorted(set(agents))
    
    def load_all(self) -> dict[str, AgentDefinition]:
        """加载所有 Agent"""
        return {
            name: self.load(name)
            for name in self.list_agents()
        }
