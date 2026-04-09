# Universal Claude

A general-purpose AI agent orchestration framework built on claw_code + ECC, supporting multi-agent collaboration, tool calling, and extensible workflows.

## What is This?

Universal Claude is a **development foundation** for building AI-powered applications. It provides:

- **19 specialized Agents** for different tasks (research, architecture, debugging, etc.)
- **28 integrated Tools** for file operations, web search, date handling, encoding, etc.
- **21 reusable Skills** for common workflows (TDD, code review, deployment)
- **19 Steering specs** for consistent behavior and best practices
- **Runtime engine** with session management, permissions, and hooks

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Project Layer (projects/)               │
├─────────────────────────────────────────────────────────────┤
│                   Orchestrator (编排层)                      │
│              api.py + agent_loader + agent_executor          │
├─────────────────────────────────────────────────────────────┤
│              ECC (Agent Business Layer)                     │
│              agents / skills / steering / hooks              │
├─────────────────────────────────────────────────────────────┤
│                claw_code (Runtime Engine)                    │
│           session / permission / tools / hooks              │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Runtime** | session.py | History management, message compression |
| **Runtime** | permission.py | Free tier (3 calls/day) / Paid tier |
| **Runtime** | tools.py | Tool registry and execution |
| **Runtime** | hooks.py | Hook event triggers |
| **Agent** | agents/*.md | 19 role definitions |
| **Agent** | skills/*/ | 21 workflow templates |
| **Agent** | steering/*.md | 19 behavior specifications |
| **Orchestrator** | agent_loader | Load MD agent definitions |
| **Orchestrator** | agent_executor | Execution loop + tool calls |
| **Orchestrator** | llm_client | DeepSeek/Claude API wrapper |
| **Orchestrator** | api.py | FastAPI HTTP interface |

---

## Installation

### Prerequisites

- Python 3.10+
- pip or pip3
- API key for LLM provider (DeepSeek, Claude, OpenAI, etc.)

### Step 1: Clone the Repository

```bash
git clone https://github.com/XZorz/universal-claude.git
cd universal-claude
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows
```

### Step 3: Install Dependencies

```bash
# Core dependencies
pip install fastapi uvicorn pyyaml

# Optional: Enhanced tools
pip install duckduckgo-search  # For web_search tool
pip install sxtwl              # For bazi/eight-characters tools

# All at once
pip install fastapi uvicorn pyyaml duckduckgo-search sxtwl
```

### Step 4: Configure LLM Provider

Create `configs/local.yaml` or set environment variables:

```bash
# DeepSeek (default, recommended)
export DEEPSEEK_API_KEY="sk-your-deepseek-key"

# Or Claude
export ANTHROPIC_API_KEY="sk-ant-your-claude-key"

# Or OpenAI
export OPENAI_API_KEY="sk-your-openai-key"
```

Or edit `configs/providers.yaml`:

```yaml
providers:
  deepseek:
    name: "DeepSeek"
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"
    default: true
```

### Step 5: Verify Installation

```bash
cd orchestrator
python -c "
from orchestrator import Orchestrator
print('✅ Universal Claude installed successfully')
print('Available agents:', ['planner', 'researcher', 'architect', 'debugger'])
"
```

---

## Quick Start

### Python API

```python
from orchestrator import Orchestrator

# Initialize
orch = Orchestrator(
    llm_provider="deepseek",
    api_key="sk-your-deepseek-key",
    is_paid=False  # Free tier: 3 calls/day
)

# Run a task with an agent
async def main():
    # Research task
    result = await orch.run("researcher", "What are the latest AI trends in 2026?")
    print(result)
    
    # Architecture task
    result = await orch.run("architect", "Design a microservices architecture for an e-commerce platform")
    print(result)
    
    # Debugging task
    result = await orch.run("debugger", "Fix this error: TypeError: Cannot read property 'x' of undefined")
    print(result)

# Run
import asyncio
asyncio.run(main())
```

### HTTP API

```bash
# Start server
cd orchestrator
uvicorn orchestrator.api:app --host 0.0.0.0 --port 8000

# Make requests
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "planner",
    "message": "Create a task list for building a blog website"
  }'
```

### CLI Mode

```bash
cd orchestrator
python main.py
# Enter your message when prompted
```

---

## 19 Agents

Each agent is a specialized role with specific capabilities:

| # | Agent | Role | Tools Available |
|---|-------|------|-----------------|
| 1 | planner | 规划专家 | read_file, glob_search |
| 2 | researcher | 研究员 | web_search, fetch_url |
| 3 | architect | 架构师 | read_file, write_file |
| 4 | debugger | 调试专家 | read_file, grep_search |
| 5 | reviewer | 代码审查 | read_file, grep_search |
| 6 | code-reviewer | 代码审查 | read_file, grep_search |
| 7 | tdd-guide | TDD指导 | read_file, write_file |
| 8 | chief-of-staff | 首席顾问 | all tools |
| 9 | build-error-resolver | 构建修复 | read_file, grep_search |
| 10 | database-reviewer | 数据库审查 | read_file, grep_search |
| 11 | doc-updater | 文档更新 | read_file, write_file |
| 12 | e2e-runner | E2E测试 | read_file, write_file |
| 13 | go-build-resolver | Go构建修复 | read_file, grep_search |
| 14 | go-reviewer | Go审查 | read_file, grep_search |
| 15 | harness-optimizer | Harness优化 | read_file, write_file |
| 16 | loop-operator | 循环操作 | read_file, write_file |
| 17 | python-reviewer | Python审查 | read_file, grep_search |
| 18 | refactor-cleaner | 重构清理 | read_file, write_file |
| 19 | security-reviewer | 安全审查 | read_file, grep_search |

### Creating a Custom Agent

Create `ecc/agents/my-agent.md`:

```markdown
# My Custom Agent

## Role
You are a [describe role].

## Capabilities
- Capability 1
- Capability 2

## Workflow
1. Step 1: Understand the task
2. Step 2: Gather information
3. Step 3: Execute
4. Step 4: Present result

## Output Format
```markdown
# Result

## Summary
...

## Details
...
```
```

---

## 28 Tools

### File Operations (4)

| Tool | Description | Example |
|------|-------------|---------|
| read_file | Read file content | `read_file("path/to/file.py")` |
| write_file | Write content to file | `write_file("file.md", "# Title")` |
| glob_search | Find files by pattern | `glob_search("**/*.py")` |
| grep_search | Search file contents | `grep_search("def main", "*.py")` |

### Web/Network (2)

| Tool | Description | Example |
|------|-------------|---------|
| web_search | Search the web | `web_search("AI trends 2026", limit=5)` |
| fetch_url | Get URL content | `fetch_url("https://example.com")` |

### JSON/Text (5)

| Tool | Description | Example |
|------|-------------|---------|
| json_format | Format JSON | `json_format('{"a":1}')` |
| json_query | Query JSON | `json_query('{"user":{"name":"John"}}', "user.name")` |
| text_count | Count patterns | `text_count("hello world", "o")` |
| text_replace | Replace text | `text_replace("hello", "hello", "hi")` |
| text_extract | Regex extract | `text_extract("abc123", "[0-9]+")` |

### Date/Time (3)

| Tool | Description | Example |
|------|-------------|---------|
| date_now | Current time | `date_now("%Y-%m-%d")` |
| date_calc | Add/subtract days | `date_calc("2026-01-01", 30)` |
| date_diff | Days between | `date_diff("2026-01-01", "2026-02-01")` |

### Encoding/Security (6)

| Tool | Description | Example |
|------|-------------|---------|
| encode_base64 | Base64 encode | `encode_base64("hello")` |
| decode_base64 | Base64 decode | `decode_base64("aGVsbG8=")` |
| encode_url | URL encode | `encode_url("hello world")` |
| hash_md5 | MD5 hash | `hash_md5("hello")` |
| hash_sha256 | SHA256 hash | `hash_sha256("hello")` |
| password_generate | Generate password | `password_generate(16, complex=True)` |

### Utils (2)

| Tool | Description | Example |
|------|-------------|---------|
| calculate | Math evaluation | `calculate("2 + 2 * 3")` |
| uuid_generate | Generate UUID | `uuid_generate(5)` |

### Bazi (6) - Optional

Requires: `pip install sxtwl`

| Tool | Description |
|------|-------------|
| bazi_calculation | Eight characters birth chart |
| dayun_calculation | 10-year fortune cycles |
| fortune_reading | Fortune interpretation |
| five_elements_analysis | Five elements analysis |
| daily_fortune | Daily fortune |
| full_analysis | Complete birth analysis |

---

## 21 Skills

Reusable workflow templates:

| Skill | Description |
|-------|-------------|
| agentic-engineering | Building autonomous agents |
| api-design | RESTful API design |
| backend-patterns | Backend development patterns |
| code-refactoring | Systematic refactoring |
| coding-standards | Code quality standards |
| database-migrations | DB migration strategies |
| deployment-patterns | Deployment best practices |
| docker-patterns | Docker containerization |
| e2e-testing | End-to-end testing |
| frontend-patterns | Frontend development |
| golang-patterns | Go programming |
| golang-testing | Go testing strategies |
| performance-optimization | Performance tuning |
| postgres-patterns | PostgreSQL optimization |
| project-planning | Project planning |
| python-patterns | Python best practices |
| python-testing | Python testing |
| search-first | Search-driven development |
| security-review | Security audit |
| tdd-workflow | Test-driven development |
| verification-loop | Iterative verification |

---

## 19 Steering Specifications

Behavior guidelines loaded with agents:

| Steering | Purpose |
|----------|---------|
| ai-collaboration.md | Human-AI collaboration |
| coding-style.md | Code style (immutability, error handling) |
| debugging.md | Debugging methodology |
| dev-mode.md | Development mode |
| development-workflow.md | Development workflow |
| git-workflow.md | Git practices |
| golang-patterns.md | Go patterns |
| lessons-learned.md | Historical lessons |
| patterns.md | Design patterns |
| performance.md | Performance optimization |
| python-patterns.md | Python patterns |
| research-mode.md | Research methodology |
| review-mode.md | Code review process |
| security.md | Security guidelines |
| swift-patterns.md | Swift patterns |
| system-design.md | System design principles |
| testing.md | Testing strategy |
| typescript-patterns.md | TypeScript patterns |
| typescript-security.md | TS security |

---

## Execution Flow (Deep Dive)

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                            │
│                      "Research AI trends"                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│                                                                 │
│  1. AgentLoader.load("researcher")                               │
│     └─ Reads ecc/agents/researcher.md                           │
│     └─ Injects steering files                                    │
│                                                                 │
│  2. SessionManager.prepare()                                     │
│     ├─ Loads conversation history                                │
│     ├─ Applies message compression if needed                    │
│     └─ Injects system prompt                                     │
│                                                                 │
│  3. AgentExecutor.execute()                                      │
│     │                                                           │
│     ├─ LLMClient.chat()                                          │
│     │     │                                                     │
│     │     ├─ Sends: system prompt + history + user message     │
│     │     └─ Receives: text response OR tool_call              │
│     │                                                           │
│     ├─ If tool_call detected:                                   │
│     │     │                                                     │
│     │     ├─ ToolRegistry.execute(tool_name, params)            │
│     │     │     └─ Runs: web_search / read_file / etc          │
│     │     │                                                     │
│     │     ├─ HookRunner.run("post_tool")                        │
│     │     │                                                     │
│     │     └─ LLMClient.chat() with tool result                 │
│     │                                                           │
│     └─ If text response:                                        │
│           └─ Return to user                                     │
│                                                                 │
│  4. HookRunner.run("post_response")                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
universal-claude/
│
├── CLAUDE.md                    # Architecture documentation
├── README.md                    # This file
├── install.sh                   # Installation script
│
├── orchestrator/                # ⭐ Core orchestration layer
│   ├── __init__.py             # Package init
│   ├── main.py                 # CLI entry point
│   ├── api.py                  # FastAPI HTTP endpoints
│   ├── agent_loader.py         # Loads .md agent definitions
│   ├── agent_executor.py       # Execution loop
│   ├── llm_client.py           # LLM API wrapper
│   ├── tools.py                # Tool registry + implementations
│   └── bazi.py                 # Bazi (Chinese astrology) tools
│
├── claw_code/                   # Runtime engine (from claw-code)
│   ├── CLAUDE.md
│   └── runtime/
│       ├── __init__.py         # Exports ToolRegistry, SessionManager, etc.
│       ├── session.py          # Session + message compression
│       ├── permission.py       # TieredPermissionPolicy
│       ├── tools.py            # GlobalToolRegistry
│       └── hooks.py            # HookRunner
│
├── ecc/                         # ECC layer (agent definitions)
│   ├── CLAUDE.md
│   ├── agents/                 # 19 agent .md files
│   │   ├── planner.md
│   │   ├── researcher.md
│   │   ├── architect.md
│   │   └── ... (16 more)
│   ├── skills/                 # 21 skill directories
│   │   ├── project-planning/SKILL.md
│   │   ├── tdd-workflow/SKILL.md
│   │   └── ... (19 more)
│   ├── steering/               # 19 behavior .md files
│   │   ├── coding-style.md
│   │   ├── debugging.md
│   │   └── ... (17 more)
│   └── hooks/                  # 10 hook files
│       └── *.hook
│
├── configs/                    # Configuration files
│   ├── agents.yaml             # Agent registry
│   ├── providers.yaml          # LLM provider configs
│   └── tools.yaml              # Tool registry
│
└── projects/                   # Example projects
    └── .gitkeep
```

---

## Configuration

### Agent Configuration (configs/agents.yaml)

```yaml
agents:
  - name: "researcher"
    display_name: "研究员"
    description: "Information gathering and analysis"
    provider: "deepseek"
    model: "deepseek-chat"
    temperature: 0.5
    tools:
      - web_search
      - fetch_url

  - name: "architect"
    display_name: "架构师"
    description: "System design and architecture"
    provider: "deepseek"
    model: "deepseek-chat"
    temperature: 0.6
    tools:
      - read_file
      - write_file
```

### Tool Permissions (configs/tools.yaml)

```yaml
tools:
  - name: "read_file"
    permission: "read_only"
    description: "Read file content"
    
  - name: "write_file"
    permission: "workspace_write"
    description: "Write files to workspace"
```

### Permission Tiers (claw_code/runtime/permission.py)

```python
class TieredPermissionPolicy:
    FREE_TIER = {
        "daily_tool_calls": 3,
        "max_file_size_kb": 100,
        "allowed_tools": ["read_file", "web_search", "calculate"]
    }
    
    PAID_TIER = {
        "daily_tool_calls": float("inf"),
        "max_file_size_kb": 10000,
        "allowed_tools": "all"
    }
```

---

## Extending the Framework

### Add a New Agent

1. Create `ecc/agents/my-agent.md`:
```markdown
# My Agent

## Role
You are a [description].

## Workflow
1. [Step 1]
2. [Step 2]

## Output Format
[Describe expected output]
```

2. Register in `configs/agents.yaml`:
```yaml
  - name: "my-agent"
    display_name: "My Agent"
    description: "..."
    provider: "deepseek"
    model: "deepseek-chat"
    temperature: 0.7
    tools:
      - read_file
```

### Add a New Tool

1. Add function to `orchestrator/tools.py`:
```python
def my_tool(param1: str, param2: int) -> str:
    """Tool description"""
    # Implementation
    return result

# Register
registry.register_function("my_tool", my_tool, "Description")
```

2. Update `configs/tools.yaml`

### Add a New Skill

Create directory `ecc/skills/my-skill/SKILL.md`:
```markdown
# My Skill

## Goal
[What this skill accomplishes]

## Steps
1. [Step 1]
2. [Step 2]

## Template
[Output template]
```

### Add a New Steering

Create `ecc/steering/my-steering.md`:
```markdown
# My Steering

## inclusion: auto

## Content
[Rules and guidelines]
```

---

## Troubleshooting

### ImportError: No module named 'orchestrator'

```bash
# Make sure you're in the right directory
cd universal-claude
export PYTHONPATH=$PWD:$PYTHONPATH
```

### API Key Not Found

```bash
# Set environment variable
export DEEPSEEK_API_KEY="sk-your-key"

# Or create config
echo "DEEPSEEK_API_KEY=sk-your-key" > .env
```

### Tool Not Found

Check that the tool is registered in:
1. `orchestrator/tools.py` (function exists)
2. `configs/tools.yaml` (registered)

### Rate Limit Exceeded

```python
# Switch to paid tier
orch = Orchestrator(is_paid=True)

# Or add delay between calls
import time
time.sleep(1)
```

---

## License

MIT

## Credits

| Component | Source | Stars |
|-----------|--------|-------|
| claw_code | [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) | 160k |
| ECC | [ecc/](https://github.com/) | 145k |
| Orchestrator | Custom implementation | - |

---

## Contributing

Contributions welcome! Areas to improve:

- More agents (data engineer, DevOps, etc.)
- More tools (database, cloud APIs, etc.)
- More skills (mobile development, blockchain, etc.)
- Better documentation
- Performance optimization
