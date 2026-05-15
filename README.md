# Silver Team — Multi-Agent Management System

A production-ready multi-agent team management system built with Python and Claude AI. Each agent represents a specialist in a digital marketing domain. A General Manager orchestrates the whole team.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

> **No API key?** The system still works — agents return mock responses with a warning. All CLI commands, reports, and the dashboard function without a key.

### 3. Run your first command

```bash
python cli.py info                     # System overview
python cli.py agent list               # List all 8 pre-configured agents
python cli.py agent run Sophie "Draft a LinkedIn post about AI in marketing"
python cli.py manager run "Plan a cross-channel campaign for a SaaS product launch"
```

---

## The Silver Team

| Agent | Role | Specialities |
|-------|------|--------------|
| **Sophie** | LinkedIn Manager | B2B outreach, lead gen, personal branding, content creation |
| **Marcus** | Facebook Manager | Paid ads, community management, Meta ecosystem, A/B testing |
| **Léa** | Instagram Manager | Reels, stories, influencer outreach, hashtag strategy |
| **Kai** | TikTok Manager | Viral content, trends, short-form video, TikTok ads |
| **Alex** | SEO Manager | Keyword research, on-page SEO, backlinks, technical SEO |
| **Nora** | Content Manager | Copywriting, blog posts, editorial calendar, brand voice |
| **Dani** | Analytics Manager | KPIs, dashboards, data analysis, ROI, attribution |
| **Eli** | Email Marketing Manager | Campaigns, automation, segmentation, deliverability |

---

## CLI Reference

### Agent Commands

```bash
# List all agents
python cli.py agent list
python cli.py agent list --json-output

# Run a task on a specific agent
python cli.py agent run <name> "<task>"
python cli.py agent run Sophie "Create a 5-post LinkedIn content series about leadership"
python cli.py agent run Alex "Keyword research for 'email marketing automation'"

# Generate an agent's performance report
python cli.py agent report <name>
python cli.py agent report Dani --json-output

# Trigger self-evaluation
python cli.py agent evaluate <name>

# Create a new agent (interactive wizard)
python cli.py agent create
python cli.py agent create --name "Pierre" --role "Pinterest Manager" --skills "visual search,pins,boards,shopping ads"

# Delete an agent
python cli.py agent delete <agent-id>
```

### Manager Commands

```bash
# Run a task through the General Manager (strategic orchestration)
python cli.py manager run "<task>"
python cli.py manager run "Analyse our Q1 performance and suggest Q2 priorities"

# Route a task to the best-suited agent automatically
python cli.py manager run "<task>" --route

# Show team status
python cli.py manager status

# Run team-wide self-improvement analysis
python cli.py manager improve
```

### Report Commands

```bash
# Generate weekly reports for all agents + team summary
python cli.py report weekly

# Print JSON instead of Markdown
python cli.py report weekly --json-output

# List all saved reports
python cli.py report list
```

### MCP Commands

```bash
# List configured MCP servers
python cli.py mcp list

# Add a new MCP server (interactive)
python cli.py mcp add

# Enable/disable an MCP server
python cli.py mcp enable <name>
python cli.py mcp enable <name> --disable
```

### Dashboard

```bash
# Live auto-refreshing dashboard
python cli.py dashboard

# Run for 30 seconds then exit
python cli.py dashboard --duration 30
```

### Scheduler

```bash
# Start background scheduler (weekly reports auto-generated every Monday 09:00 UTC)
python cli.py scheduler start

# List registered jobs
python cli.py scheduler jobs
```

---

## Project Structure

```
/home/user/Agentaumanage/
├── core/
│   ├── __init__.py
│   ├── manager.py          # GeneralManager orchestrator
│   ├── agent_base.py       # BaseAgent class all agents inherit
│   ├── agent_registry.py   # Registry to create/manage agents dynamically
│   ├── memory.py           # Persistent memory (JSON-based)
│   ├── scheduler.py        # Weekly reports, cron-like task scheduler
│   └── mcp_loader.py       # Dynamic MCP/API plugin loader
├── agents/
│   ├── __init__.py
│   ├── linkedin_agent.py   # Sophie
│   ├── facebook_agent.py   # Marcus
│   ├── instagram_agent.py  # Léa
│   ├── tiktok_agent.py     # Kai
│   ├── seo_agent.py        # Alex
│   ├── content_agent.py    # Nora
│   ├── analytics_agent.py  # Dani
│   └── email_agent.py      # Eli
├── reports/
│   ├── __init__.py
│   ├── report_generator.py # Weekly report + stats (Markdown + JSON)
│   └── dashboard.py        # Rich terminal dashboard
├── config/
│   ├── agents.json          # Agent definitions (pre-populated with 8 agents)
│   ├── mcps.json            # MCP server configurations
│   └── settings.json        # Global settings
├── data/
│   ├── memory/              # Per-agent persistent memory (auto-created)
│   └── reports/             # Generated reports (auto-created)
├── cli.py                   # Main CLI entry point
├── requirements.txt
├── .env.example             # Copy to .env and add ANTHROPIC_API_KEY
└── README.md
```

---

## Architecture

### BaseAgent

Every specialist agent inherits from `BaseAgent` (`core/agent_base.py`):

- **Memory**: Each agent has its own JSON memory file in `data/memory/{agent_id}.json`. Task history, stats, and self-evaluations are persisted automatically.
- **API**: Calls Claude (`claude-sonnet-4-6`) via the Anthropic SDK. Falls back to mock responses if no API key is set.
- **Methods**:
  - `execute_task(task)` — runs a task and stores the result
  - `generate_report()` — creates a structured performance report
  - `self_evaluate()` — analyses last 10 tasks and produces a self-evaluation
  - `get_stats()` — returns aggregated performance statistics
  - `update_memory(key, val)` — stores arbitrary data in persistent memory

### GeneralManager

The `GeneralManager` (`core/manager.py`) orchestrates the team:

- **Task routing**: Uses keyword matching + Claude fallback to route tasks to the best agent
- **Weekly reports**: Consolidates all agent reports and adds strategic analysis
- **Self-improvement loop**: Triggers all agent self-evaluations, then produces a company-wide improvement plan
- **Agent spawning**: Can create new agents on the fly via `spawn_agent()`

### AgentRegistry

The `AgentRegistry` (`core/agent_registry.py`) manages agent lifecycle:

- Thread-safe operations with a `threading.Lock`
- Persists agent definitions in `config/agents.json`
- Supports CRUD operations: `create_agent`, `get_agent`, `list_agents`, `delete_agent`, `update_agent`

### Scheduler

The `Scheduler` (`core/scheduler.py`) uses APScheduler for automated tasks:

- Weekly report generation every Monday 09:00 UTC
- Daily stats update every day 23:30 UTC
- Manual trigger support: `run_job(job_id)` and `run_all()`

### MCP Loader

The `MCPLoader` (`core/mcp_loader.py`) manages MCP server plugins:

- Loads configurations from `config/mcps.json`
- Supports runtime registration of new MCP servers
- Resolves `${ENV_VAR}` placeholders from environment
- Injects MCP context into agent system prompts

---

## Adding New Agents

### Via CLI

```bash
python cli.py agent create
```

Follow the interactive wizard.

### Via Python

```python
from core.agent_registry import AgentRegistry

registry = AgentRegistry()
new_agent = registry.create_agent(
    name="Pierre",
    role="Pinterest Manager",
    skills=["visual search", "pin strategy", "shopping ads", "audience insights"],
    description="Pierre specialises in Pinterest visual discovery and shopping campaigns.",
    personality="Visual, creative, and data-driven.",
)
```

### Via Specialist Class

Create a new file in `agents/`:

```python
# agents/pinterest_agent.py
from core.agent_base import BaseAgent

class PinterestAgent(BaseAgent):
    def create_board_strategy(self, niche: str) -> str:
        return self.execute_task(f"Create a Pinterest board strategy for: {niche}")
```

---

## Self-Improvement Loop

The system includes a built-in self-improvement cycle:

1. **Individual evaluation**: Each agent analyses its last 10 tasks using `self_evaluate()`. Produces: strengths, weaknesses, improvement plan, and an overall rating.

2. **Team-level synthesis**: The GeneralManager reads all individual evaluations and produces a company-wide improvement plan via `run_team_self_improvement()`.

3. **Automated via scheduler**: This runs weekly alongside the performance reports.

```bash
# Trigger manually
python cli.py manager improve
```

---

## Configuration

### `config/settings.json`

```json
{
  "claude": {
    "model": "claude-sonnet-4-6",
    "max_tokens": 4096,
    "temperature": 0.7,
    "retry_attempts": 3
  },
  "scheduler": {
    "weekly_report_day": "monday",
    "weekly_report_hour": 9,
    "enabled": true
  }
}
```

### Adding MCP Servers

Edit `config/mcps.json` or use the CLI:

```bash
python cli.py mcp add
```

Then reference MCP servers in an agent's config by adding their names to `mcp_servers: ["brave-search"]`.

---

## Requirements

- Python 3.10+
- `anthropic>=0.40.0`
- `click>=8.1.0`
- `rich>=13.0.0`
- `apscheduler>=3.10.0`
- `python-dotenv>=1.0.0`
- `pydantic>=2.0.0`

---

## License

MIT — See LICENSE for details.
