# Universal Claude

A general-purpose AI agent orchestration framework built on claw_code + ECC, supporting multi-agent collaboration, tool calling, and extensible workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Project Layer (projects/)               │
├─────────────────────────────────────────────────────────────┤
│                   Orchestrator (编排层)                      │
│         api.py + agent_loader + agent_executor              │
├─────────────────────────────────────────────────────────────┤
│              ECC (Agent Business Layer)                     │
│              agents / skills / steering / hooks             │
├─────────────────────────────────────────────────────────────┤
│                claw_code (Runtime Engine)                    │
│           session / permission / tools / hooks               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 19 Agents

| Agent | Role | Description |
|-------|------|-------------|
| planner | 规划专家 | Task decomposition and planning |
| researcher | 研究员 | Information gathering and analysis |
| architect | 架构师 | System design and architecture |
| debugger | 调试专家 | Problem diagnosis and fixing |
| reviewer | 代码审查 | Code review and improvement |
| code-reviewer | 代码审查 | Quality/security/performance review |
| tdd-guide | TDD指导 | Test-driven development guidance |
| chief-of-staff | 首席顾问 | Coordination and management |
| build-error-resolver | 构建修复 | Build error resolution |
| database-reviewer | 数据库审查 | Database review |
| doc-updater | 文档更新 | Documentation maintenance |
| e2e-runner | E2E测试 | End-to-end testing |
| go-build-resolver | Go构建修复 | Go build issues |
| go-reviewer | Go审查 | Go code review |
| harness-optimizer | Harness优化 | Test harness optimization |
| loop-operator | 循环操作 | Loop task execution |
| python-reviewer | Python审查 | Python code review |
| refactor-cleaner | 重构清理 | Code refactoring |
| security-reviewer | 安全审查 | Security vulnerability review |

### 19 Steering Specifications

| File | Description |
|------|-------------|
| ai-collaboration.md | Human-AI collaboration guidelines |
| coding-style.md | Coding style and best practices |
| debugging.md | Debugging methodology |
| dev-mode.md | Development mode |
| development-workflow.md | Development workflow |
| git-workflow.md | Git workflow |
| golang-patterns.md | Go patterns |
| lessons-learned.md | Lessons learned |
| patterns.md | Design patterns |
| performance.md | Performance optimization |
| python-patterns.md | Python patterns |
| research-mode.md | Research mode |
| review-mode.md | Review mode |
| security.md | Security guidelines |
| swift-patterns.md | Swift patterns |
| system-design.md | System design principles |
| testing.md | Testing guidelines |
| typescript-patterns.md | TypeScript patterns |
| typescript-security.md | TypeScript security |

### 21 Skills

| Skill | Description |
|-------|-------------|
| agentic-engineering | Agent development workflow |
| api-design | API design patterns |
| backend-patterns | Backend development |
| code-refactoring | Code refactoring |
| coding-standards | Coding standards |
| database-migrations | Database migrations |
| deployment-patterns | Deployment strategies |
| docker-patterns | Docker best practices |
| e2e-testing | End-to-end testing |
| frontend-patterns | Frontend development |
| golang-patterns | Go development |
| golang-testing | Go testing |
| performance-optimization | Performance tuning |
| postgres-patterns | PostgreSQL patterns |
| project-planning | Project planning |
| python-patterns | Python development |
| python-testing | Python testing |
| search-first | Search-first development |
| security-review | Security review |
| tdd-workflow | Test-driven development |
| verification-loop | Verification workflow |

### 28 Tools

**File Operations (4)**
| Tool | Description |
|------|-------------|
| read_file | Read file content |
| write_file | Write file content |
| glob_search | File pattern search |
| grep_search | Content search |

**Web/Network (2)**
| Tool | Description |
|------|-------------|
| web_search | Web search (DuckDuckGo) |
| fetch_url | Fetch URL content |

**JSON/Text (5)**
| Tool | Description |
|------|-------------|
| json_format | Format JSON string |
| json_query | JSONPath query |
| text_count | Text pattern count |
| text_replace | Text replacement |
| text_extract | Regex extraction |

**Date/Time (3)**
| Tool | Description |
|------|-------------|
| date_now | Current datetime |
| date_calc | Date calculation |
| date_diff | Date difference |

**Encoding/Security (6)**
| Tool | Description |
|------|-------------|
| encode_base64 | Base64 encode |
| decode_base64 | Base64 decode |
| encode_url | URL encode |
| hash_md5 | MD5 hash |
| hash_sha256 | SHA256 hash |
| password_generate | Password generation |

**Utils (2)**
| Tool | Description |
|------|-------------|
| calculate | Math expression evaluation |
| uuid_generate | UUID generation |

**Bazi (6) - Optional**
| Tool | Description |
|------|-------------|
| bazi_calculation | Eight characters calculation |
| dayun_calculation | Fortune cycle calculation |
| fortune_reading | Fortune reading |
| five_elements_analysis | Five elements analysis |
| daily_fortune | Daily fortune |
| full_analysis | Full analysis |

## Execution Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator                            │
│                                                             │
│  ├─ AgentLoader.load("researcher")                         │
│  │     └─ Loads agent.md definition                        │
│                                                             │
│  ├─ AgentExecutor.execute()                                 │
│  │     │                                                   │
│  │     ├─ Session ─────── History + Compression            │
│  │     │                                                   │
│  │     ├─ LLMClient ──────► DeepSeek/Claude API           │
│  │     │      └─ ToolCall parsing                          │
│  │     │                                                   │
│  │     ├─ ToolRegistry ────► Execute tool                  │
│  │     │      └─ read/write/search/calculate/etc          │
│  │     │                                                   │
│  │     └─ HookRunner ─────── Hook triggers                 │
│                                                             │
│  └─ Return response                                        │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Clone the repository
git clone https://github.com/XZorz/universal-claude.git
cd universal-claude

# Install dependencies
pip install -r requirements.txt  # If exists

# Or install directly
pip install fastapi uvicorn sxtwl
```

## Usage

### Python API

```python
from orchestrator import Orchestrator

orch = Orchestrator(
    llm_provider="deepseek",
    api_key="your-api-key",
    is_paid=False
)

# Run an agent with a task
response = await orch.run("researcher", "Research AI agent trends")
response = await orch.run("architect", "Design an e-commerce system")
response = await orch.run("debugger", "Fix this bug: ...")
```

### HTTP API

```bash
cd orchestrator
uvicorn orchestrator.api:app --host 0.0.0.0 --port 8000

# Request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent": "planner", "message": "Plan a new project"}'
```

### Direct Tool Usage

```python
from orchestrator.tools import bazi_calculation, web_search

# Use tools directly
result = web_search("LLM trends 2026", limit=5)
result = bazi_calculation("1993-09-17", "19:30")
```

## Extending

### Add New Agent
Create `ecc/agents/your-agent.md`:
```markdown
# Your Agent Name

## Role
...

## Capabilities
...

## Workflow
...
```

### Add New Tool
Add to `orchestrator/tools.py`:
```python
def your_tool(param1: str) -> str:
    """Tool description"""
    return result

registry.register_function("your_tool", your_tool, "Description")
```

### Add New Skill
Create `ecc/skills/your-skill/SKILL.md`

### Add New Steering
Create `ecc/steering/your-steering.md`

## Project Structure

```
universal-claude/
├── CLAUDE.md                    # Architecture documentation
├── README.md                    # This file
├── install.sh                   # Installation script
│
├── orchestrator/                # ⭐ Orchestration layer
│   ├── __init__.py
│   ├── main.py                  # Main entry
│   ├── api.py                   # FastAPI HTTP service
│   ├── agent_loader.py          # Load MD agent definitions
│   ├── agent_executor.py        # Agent execution loop
│   ├── llm_client.py            # LLM API client
│   ├── tools.py                 # Tool registry
│   └── bazi.py                  # Bazi (Eight Characters) tools
│
├── claw_code/                   # Runtime engine
│   ├── CLAUDE.md
│   └── runtime/
│       ├── session.py           # Session management
│       ├── permission.py        # Permission policy
│       ├── tools.py             # Tool registry
│       └── hooks.py             # Hook runner
│
├── ecc/                         # ECC layer
│   ├── CLAUDE.md
│   ├── agents/                  # 19 agent definitions
│   ├── skills/                  # 21 workflow templates
│   ├── steering/                # 19 behavior specs
│   └── hooks/                   # 10 hooks
│
├── configs/                     # Configuration
│   ├── agents.yaml              # Agent registry
│   ├── providers.yaml           # LLM providers
│   └── tools.yaml               # Tool registry
│
└── projects/                    # Example projects
```

## License

MIT

## Credits

- **claw_code**: [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) - 160k stars Rust implementation
- **ECC**: [ecc/](https://github.com/) - 145k stars agent framework
- **Orchestrator**: Custom implementation
