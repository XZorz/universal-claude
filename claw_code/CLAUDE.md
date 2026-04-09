# Claw Code - 主架构（底层运行时）

## 定位
claw-code 是整个架构的底层核心，提供：
- Agent 执行运行时
- 工具注册与执行
- 权限控制系统
- 会话管理
- 钩子机制

## 目录结构
```
claw-code/
├── runtime/           # 核心运行时模块
│   ├── session.py     # 会话管理（历史、压缩）
│   ├── permission.py  # 权限策略
│   ├── tools.py       # 工具注册表
│   ├── hooks.py       # 钩子运行器
│   └── api.py         # API客户端
├── tools/             # 工具实现
└── CLAUDE.md         # 本文件
```

## 核心模块

### runtime/session.py
```python
Session, SessionManager, MessageRole, ConversationMessage
```
- 管理对话历史
- 支持会话压缩（Token超限时）
- 持久化支持

### runtime/permission.py
```python
PermissionMode, PermissionPolicy, TieredPermissionPolicy
```
- ReadOnly / WorkspaceWrite / DangerFullAccess / Prompt / Allow
- 免费用户3次/天，付费用户无限

### runtime/tools.py
```python
ToolRegistry, ToolSpec, ToolResult
```
- 全局工具注册表
- 工具执行与结果封装

### runtime/hooks.py
```python
HookRunner, HookEvent, HookResult
```
- PreToolUse / PostToolUse
- PreCommit / PostCommit

## 使用方式
ECC 等上层架构运行在 claw-code 之上，调用其运行时能力。
