# Universal Claude Code 架构

## 架构层次

```
┌─────────────────────────────────────────────────────────┐
│                    项目层 (projects/)                      │
├─────────────────────────────────────────────────────────┤
│                  Orchestrator (编排层)                      │
│    api.py + agent_loader + agent_executor + llm_client   │
├─────────────────────────────────────────────────────────┤
│              ECC (ecc/) - Agent 层                       │
│         agents / skills / steering / hooks              │
├─────────────────────────────────────────────────────────┤
│           claw_code (claw_code/) - Runtime               │
│      session / permission / tools / hooks                │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

```
~/.hermes/universal-claude/
├── CLAUDE.md                    # 本文件
│
├── orchestrator/                # ⭐ 编排层（核心连接器）
│   ├── __init__.py
│   ├── llm_client.py           # LLM API 客户端 (DeepSeek/Claude)
│   ├── agent_loader.py         # 加载 MD Agent 定义
│   ├── agent_executor.py        # Agent 执行循环
│   ├── main.py                  # CLI 入口
│   └── api.py                   # ⭐ FastAPI HTTP 服务
│
├── claw_code/                   # 主架构（底层运行时）
│   ├── CLAUDE.md
│   └── runtime/                 # 核心运行时
│       ├── session.py           # ✅ 会话管理 + 真正压缩
│       ├── permission.py        # 权限策略 (免费3次/付费无限)
│       ├── tools.py             # ✅ 工具注册表 + 真正处理器
│       └── hooks.py             # 钩子运行器
│
├── ecc/                         # 运行层
│   ├── agents/                  # 16个 Agent (MD)
│   ├── skills/                  # 18个工作流
│   ├── steering/                # 16个规范文件
│   └── hooks/                   # 10个钩子
│
└── configs/                     # 配置文件
    ├── agents.yaml              # Agent 注册表
    ├── providers.yaml           # LLM Provider
    └── tools.yaml               # 工具注册表
```

## 执行流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Orchestrator (编排层)                                     │
│  │                                                        │
│  ├─ AgentLoader.load("mao")                             │
│  │   └─ 读取 ecc/agents/mao.md                           │
│  │                                                        │
│  ├─ AgentExecutor.execute()                               │
│  │   │                                                    │
│  │   ├─ Session (claw_code) ──── 历史 + 压缩             │
│  │   │                                                    │
│  │   ├─ LLMClient.chat() ──────► DeepSeek/Claude API    │
│  │   │     └─ ToolCall.input JSON 解析                   │
│  │   │                                                    │
│  │   ├─ ToolRegistry.execute() ◄── claw_code runtime     │
│  │   │     └─ 真正的工具处理器                            │
│  │   │       └─ read_file, write_file, grep_search      │
│  │   │       └─ bazi_calculation, five_elements         │
│  │   │                                                    │
│  │   └─ HookRunner.run() ◄──── claw_code runtime         │
│  │                                                        │
│  └─ 返回结果                                              │
└─────────────────────────────────────────────────────────┘
```

## 已修复问题

| 问题 | 状态 | 修复内容 |
|------|------|----------|
| HookRunner/ToolResult 重复定义 | ✅ 已修复 | 统一使用 claw_code.runtime |
| tool_registry 为 None | ✅ 已修复 | 真正连接 get_global_registry() |
| permission 未连接 | ✅ 已修复 | 初始化 TieredPermissionPolicy |
| 缺少 HTTP API | ✅ 已修复 | 新增 FastAPI api.py |
| 工具是空壳 | ✅ 已修复 | 实现真正处理器 (read/write/grep/bazi) |
| Session 压缩是空壳 | ✅ 已修复 | 保留系统消息 + 最近对话 |
| LLM tool_call.input 解析错误 | ✅ 已修复 | JSON string → dict |

## 使用方法

### 1. Python 代码

```python
from orchestrator import Orchestrator

orch = Orchestrator()
response = await orch.run("mao", "今天运气如何？")
```

### 2. 命令行

```bash
cd ~/.hermes/universal-claude/orchestrator
python main.py
```

### 3. HTTP API

```bash
cd ~/.hermes/universal-claude/orchestrator
uvicorn orchestrator.api:app --host 0.0.0.0 --port 8000

# 请求示例
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent": "planner", "message": "帮我分析八字癸酉 辛酉 辛丑 戊戌"}'
```

### 4. 直接使用工具

```python
from claw_code.runtime import get_global_registry

registry = get_global_registry()
result = registry.execute("bazi_calculation", {
    "birth_date": "1993-09-17",
    "birth_time": "19:30"
})
print(result.output)
```

## 可用工具

| 工具 | 描述 | 权限 |
|------|------|------|
| read_file | 读取文件 | read_only |
| write_file | 写入文件 | workspace_write |
| glob_search | 文件搜索 | read_only |
| grep_search | 内容搜索 | read_only |
| bazi_calculation | 八字计算 | read_only |
| five_elements_analysis | 五行分析 | read_only |
| fortune_reading | 运势解读 | read_only |

## 来源

- claw_code: `~/.hermes/claw-code/` (16万星 Rust 实现)
- ECC: `~/.hermes/ecc/` (14.5万星)
- Orchestrator: 自主研发，连接层

---

## 扩展点清单

### 新增 Steering 规范
| 文件 | 描述 |
|------|------|
| system-design.md | 系统设计原则 |
| debugging.md | 调试方法论 |
| ai-collaboration.md | 人机协作规范 |

### 新增 Skills
| 目录 | 描述 |
|------|------|
| project-planning | 项目规划 |
| code-refactoring | 代码重构 |
| performance-optimization | 性能优化 |

### 新增通用 Agent
| 文件 | 描述 |
|------|------|
| researcher.md | 研究员 |
| architect.md | 架构师 |
| debugger.md | 调试专家 |
| reviewer.md | 代码审查 |

### 新增通用工具
| 工具 | 描述 |
|------|------|
| web_search | 网络搜索 |
| fetch_url | URL 内容获取 |
| json_format | JSON 格式化 |
| json_query | JSON 查询 |
| calculate | 数学计算 |
| date_now | 当前时间 |
| date_calc | 日期计算 |
| date_diff | 日期差计算 |
| text_count | 文本统计 |
| text_replace | 文本替换 |
| text_extract | 正则提取 |
| encode_base64 | Base64 编码 |
| decode_base64 | Base64 解码 |
| encode_url | URL 编码 |
| hash_md5 | MD5 哈希 |
| hash_sha256 | SHA256 哈希 |
| uuid_generate | UUID 生成 |
| password_generate | 密码生成 |

