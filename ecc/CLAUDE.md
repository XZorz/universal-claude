# Everything Claude Code (ECC) - 运行层

## 定位
ECC 是运行在 claw-code 之上的应用层，提供：
- 专业化 Agent 定义
- 工作流 Skills
- 开发规范 Steering
- 自动化 Hooks

## 目录结构
```
ecc/
├── agents/     # 16个专业Agent
├── skills/    # 18个工作流
├── steering/  # 16个规范文件
├── hooks/    # 10个钩子
└── CLAUDE.md
```

## Agent 体系
| Agent | 用途 |
|-------|------|
| planner | 规划复杂功能 |
| code-reviewer | 代码审查 |
| tdd-guide | TDD开发 |
| architect | 架构设计 |
| security-reviewer | 安全审查 |

## Skill 体系
| Skill | 用途 |
|-------|------|
| tdd-workflow | 测试驱动开发 |
| security-review | 安全审查流程 |
| verification-loop | 验证循环 |
| agentic-engineering | Agent工程学 |
