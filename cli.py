#!/usr/bin/env python3
"""
Silver Team — CLI entry point.
Usage: python cli.py [COMMAND] [OPTIONS]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env before any imports that might need API keys
from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

import click  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.prompt import Prompt, Confirm  # noqa: E402
from rich.text import Text  # noqa: E402
from rich import box  # noqa: E402

from core.agent_registry import AgentRegistry  # noqa: E402
from core.manager import GeneralManager  # noqa: E402
from core.mcp_loader import MCPLoader  # noqa: E402
from reports.report_generator import ReportGenerator  # noqa: E402

console = Console()


def _get_manager() -> GeneralManager:
    return GeneralManager()


def _get_registry() -> AgentRegistry:
    return AgentRegistry()


def _success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def _error(msg: str) -> None:
    console.print(f"[bold red]✗[/bold red] {msg}")


def _info(msg: str) -> None:
    console.print(f"[bold blue]ℹ[/bold blue] {msg}")


def _warn(msg: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")


# ---------------------------------------------------------------------------
# Top-level group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="1.0.0", prog_name="Silver Team")
def cli() -> None:
    """
    \b
    ╔═══════════════════════════════════════╗
    ║   SILVER TEAM — Agent Management CLI  ║
    ╚═══════════════════════════════════════╝

    Multi-agent digital marketing team system.
    """


# ---------------------------------------------------------------------------
# agent group
# ---------------------------------------------------------------------------

@cli.group()
def agent() -> None:
    """Manage individual agents."""


@agent.command("list")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def agent_list(json_output: bool) -> None:
    """List all agents with their current status."""
    registry = _get_registry()
    agents = registry.list_agents()

    if json_output:
        click.echo(json.dumps(agents, indent=2))
        return

    table = Table(
        title="Silver Team Agents",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="bold", min_width=10)
    table.add_column("Role", style="yellow", min_width=20)
    table.add_column("Status", justify="center", min_width=10)
    table.add_column("Tasks", justify="right", min_width=6)
    table.add_column("Success%", justify="right", min_width=9)
    table.add_column("Last Active", min_width=12)

    status_colours = {
        "active": "bold green",
        "busy": "bold yellow",
        "inactive": "dim red",
    }

    for a in agents:
        colour = status_colours.get(a["status"], "white")
        last = a.get("last_active") or "never"
        if last and last != "never":
            last = last[5:16].replace("T", " ")
        table.add_row(
            a["name"],
            a["role"],
            f"[{colour}]{a['status']}[/{colour}]",
            str(a["tasks_completed"]),
            f"{a['success_rate']}%",
            last,
        )

    console.print(table)
    console.print(f"\n[dim]Total agents: {len(agents)}[/dim]")


@agent.command("create")
@click.option("--name", default=None, help="Agent name")
@click.option("--role", default=None, help="Agent role/title")
@click.option("--skills", default=None, help="Comma-separated list of skills")
@click.option("--description", default="", help="Agent description")
@click.option("--personality", default="", help="Agent personality notes")
def agent_create(
    name: str,
    role: str,
    skills: str,
    description: str,
    personality: str,
) -> None:
    """Create a new agent (interactive wizard if options omitted)."""
    console.print(Panel("[bold cyan]Create New Agent[/bold cyan]", box=box.ROUNDED))

    if not name:
        name = Prompt.ask("[bold]Agent name[/bold]")
    if not role:
        role = Prompt.ask("[bold]Role / title[/bold]")
    if not skills:
        skills_raw = Prompt.ask("[bold]Skills[/bold] (comma-separated)")
    else:
        skills_raw = skills

    skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]

    # Only prompt for optional fields if running interactively
    is_interactive = sys.stdin.isatty()
    if not description and is_interactive:
        description = Prompt.ask(
            "[bold]Description[/bold] (optional, press Enter to skip)", default=""
        )
    if not personality and is_interactive:
        personality = Prompt.ask(
            "[bold]Personality notes[/bold] (optional, press Enter to skip)", default=""
        )

    # Confirm
    console.print(f"\n[bold]Preview:[/bold]")
    console.print(f"  Name       : {name}")
    console.print(f"  Role       : {role}")
    console.print(f"  Skills     : {', '.join(skills_list)}")
    console.print(f"  Description: {description or '(none)'}")

    if is_interactive and not Confirm.ask("\nCreate this agent?", default=True):
        _warn("Cancelled.")
        return

    try:
        registry = _get_registry()
        new_agent = registry.create_agent(
            name=name,
            role=role,
            skills=skills_list,
            description=description,
            personality=personality,
        )
        _success(f"Agent '{new_agent.name}' created with id: [bold]{new_agent.id}[/bold]")
    except ValueError as exc:
        _error(str(exc))


@agent.command("run")
@click.argument("name")
@click.argument("task")
@click.option("--verbose", is_flag=True, help="Show full response")
def agent_run(name: str, task: str, verbose: bool) -> None:
    """Run a task on a specific agent.

    \b
    NAME  Agent name or ID
    TASK  Natural-language task description
    """
    registry = _get_registry()
    ag = registry.get_agent(name)
    if ag is None:
        _error(f"Agent '{name}' not found.")
        raise SystemExit(1)

    with console.status(f"[bold yellow]{ag.name} is working on the task...[/bold yellow]"):
        result = ag.execute_task(task)

    console.print(Panel(
        result if verbose else result[:2000] + ("..." if len(result) > 2000 else ""),
        title=f"[bold cyan]{ag.name}[/bold cyan] ({ag.role})",
        border_style="green",
    ))


@agent.command("report")
@click.argument("name")
@click.option("--save", is_flag=True, default=True, help="Save report to disk (default: True)")
@click.option("--json-output", is_flag=True, help="Print JSON instead of Markdown")
def agent_report(name: str, save: bool, json_output: bool) -> None:
    """Generate a performance report for an agent.

    \b
    NAME  Agent name or ID
    """
    registry = _get_registry()
    ag = registry.get_agent(name)
    if ag is None:
        _error(f"Agent '{name}' not found.")
        raise SystemExit(1)

    with console.status(f"[bold yellow]Generating report for {ag.name}...[/bold yellow]"):
        report_data = ag.generate_report()

    rg = ReportGenerator()
    output = rg.generate_agent_report(report_data, save=save)

    if json_output:
        click.echo(output["json"])
    else:
        console.print(output["markdown"])
        if save and "markdown_path" in output:
            _success(f"Report saved: {output['markdown_path']}")


@agent.command("delete")
@click.argument("agent_id")
def agent_delete(agent_id: str) -> None:
    """Delete an agent by ID.

    \b
    AGENT_ID  Agent ID (see agent list for IDs)
    """
    if not Confirm.ask(f"Delete agent [bold red]{agent_id}[/bold red]?", default=False):
        _warn("Cancelled.")
        return

    registry = _get_registry()
    deleted = registry.delete_agent(agent_id)
    if deleted:
        _success(f"Agent '{agent_id}' deleted.")
    else:
        _error(f"Agent '{agent_id}' not found.")


@agent.command("evaluate")
@click.argument("name")
def agent_evaluate(name: str) -> None:
    """Trigger self-evaluation for an agent.

    \b
    NAME  Agent name or ID
    """
    registry = _get_registry()
    ag = registry.get_agent(name)
    if ag is None:
        _error(f"Agent '{name}' not found.")
        raise SystemExit(1)

    with console.status(f"[bold yellow]{ag.name} is self-evaluating...[/bold yellow]"):
        evaluation = ag.self_evaluate()

    console.print(Panel(
        json.dumps(evaluation, indent=2),
        title=f"[bold cyan]{ag.name}[/bold cyan] Self-Evaluation",
        border_style="blue",
    ))


# ---------------------------------------------------------------------------
# manager group
# ---------------------------------------------------------------------------

@cli.group()
def manager() -> None:
    """General Manager commands — orchestrates the whole team."""


@manager.command("run")
@click.argument("task")
@click.option("--route", is_flag=True, help="Route to best agent instead of manager thinking")
def manager_run(task: str, route: bool) -> None:
    """Run a task through the General Manager.

    \b
    TASK  Natural-language task description
    """
    gm = _get_manager()

    with console.status("[bold yellow]General Manager is thinking...[/bold yellow]"):
        if route:
            result_data = gm.route_task(task)
            agent_name = result_data["agent_name"]
            result = result_data["result"]
            _info(f"Routed to: [bold]{agent_name}[/bold]")
        else:
            result = gm.run_task(task)

    console.print(Panel(
        result,
        title="[bold cyan]General Manager[/bold cyan]",
        border_style="green",
    ))


@manager.command("status")
def manager_status() -> None:
    """Show the current team status."""
    gm = _get_manager()
    status = gm.get_team_status()
    console.print(Panel(
        json.dumps(status, indent=2),
        title="[bold]Team Status[/bold]",
        border_style="blue",
    ))


@manager.command("improve")
def manager_improve() -> None:
    """Run the team-wide self-improvement analysis."""
    gm = _get_manager()
    rg = ReportGenerator()

    with console.status("[bold yellow]Running team self-improvement analysis...[/bold yellow]"):
        result = gm.run_team_self_improvement()

    output = rg.generate_improvement_report(result, save=True)
    console.print(output["markdown"])
    if "markdown_path" in output:
        _success(f"Report saved: {output['markdown_path']}")


# ---------------------------------------------------------------------------
# report group
# ---------------------------------------------------------------------------

@cli.group()
def report() -> None:
    """Report generation commands."""


@report.command("weekly")
@click.option("--no-save", is_flag=True, help="Don't save reports to disk")
@click.option("--json-output", is_flag=True, help="Print JSON output")
def report_weekly(no_save: bool, json_output: bool) -> None:
    """Generate all weekly reports for every agent + team summary."""
    gm = _get_manager()
    rg = ReportGenerator()

    with console.status("[bold yellow]Generating weekly reports...[/bold yellow]"):
        team_report = gm.generate_weekly_report()

    output = rg.generate_weekly_report(team_report, save=not no_save)

    if json_output:
        click.echo(output["json"])
    else:
        console.print(output["markdown"])
        if not no_save and "markdown_path" in output:
            _success(f"Weekly report saved: {output['markdown_path']}")


@report.command("list")
def report_list() -> None:
    """List all saved reports."""
    rg = ReportGenerator()
    reports = rg.list_reports()

    if not reports:
        _info("No reports found. Run 'python cli.py report weekly' to generate one.")
        return

    table = Table(title="Saved Reports", box=box.ROUNDED)
    table.add_column("Filename", style="cyan", min_width=30)
    table.add_column("Size", justify="right")
    table.add_column("Created", min_width=19)

    for r in reports:
        table.add_row(
            r["filename"],
            f"{r['size_kb']} KB",
            r["created"][:19].replace("T", " "),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# mcp group
# ---------------------------------------------------------------------------

@cli.group()
def mcp() -> None:
    """MCP (Model Context Protocol) server management."""


@mcp.command("list")
def mcp_list() -> None:
    """List all configured MCP servers."""
    loader = MCPLoader()
    servers = loader.list_servers()

    table = Table(title="MCP Servers", box=box.ROUNDED)
    table.add_column("Name", style="bold", min_width=15)
    table.add_column("Description", min_width=30)
    table.add_column("Enabled", justify="center")
    table.add_column("Available", justify="center")

    for srv in servers:
        enabled_str = "[green]yes[/green]" if srv.enabled else "[dim]no[/dim]"
        available_str = "[green]yes[/green]" if srv.is_available() else "[dim]no[/dim]"
        table.add_row(srv.name, srv.description, enabled_str, available_str)

    console.print(table)


@mcp.command("add")
@click.option("--name", default=None)
@click.option("--description", default="")
@click.option("--command", default=None)
@click.option("--args", default=None, help="Comma-separated args")
def mcp_add(name: str, description: str, command: str, args: str) -> None:
    """Add a new MCP server configuration."""
    console.print(Panel("[bold cyan]Add MCP Server[/bold cyan]", box=box.ROUNDED))

    if not name:
        name = Prompt.ask("[bold]Server name[/bold]")
    if not description:
        description = Prompt.ask("[bold]Description[/bold]", default="")
    if not command:
        command = Prompt.ask("[bold]Command[/bold] (e.g. npx)")
    if not args:
        args_raw = Prompt.ask("[bold]Args[/bold] (comma-separated, e.g. -y,@mcp/server-name)", default="")
    else:
        args_raw = args

    args_list = [a.strip() for a in args_raw.split(",") if a.strip()]

    env_vars_raw = Prompt.ask(
        "[bold]Env vars[/bold] (format: KEY=VALUE,KEY2=VALUE2, or press Enter to skip)",
        default="",
    )
    env_vars: dict = {}
    for pair in env_vars_raw.split(","):
        pair = pair.strip()
        if "=" in pair:
            k, v = pair.split("=", 1)
            env_vars[k.strip()] = v.strip()

    loader = MCPLoader()
    server = loader.add_server(
        name=name,
        description=description,
        command=command,
        args=args_list,
        env_vars=env_vars,
        enabled=True,
    )
    _success(f"MCP server '[bold]{server.name}[/bold]' added.")


@mcp.command("enable")
@click.argument("name")
@click.option("--disable", is_flag=True, help="Disable instead of enable")
def mcp_enable(name: str, disable: bool) -> None:
    """Enable or disable an MCP server.

    \b
    NAME  MCP server name
    """
    loader = MCPLoader()
    ok = loader.enable_server(name, enabled=not disable)
    if ok:
        action = "disabled" if disable else "enabled"
        _success(f"MCP server '{name}' {action}.")
    else:
        _error(f"MCP server '{name}' not found.")


# ---------------------------------------------------------------------------
# dashboard command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--duration", default=None, type=int, help="Run for N seconds then exit")
def dashboard(duration: int) -> None:
    """Launch the live stats dashboard (press Ctrl-C to exit)."""
    from reports.dashboard import Dashboard

    gm = _get_manager()
    dash = Dashboard(gm)

    if duration:
        _info(f"Running dashboard for {duration} seconds...")
        dash.run_live(duration_seconds=duration)
    else:
        dash.run_live()


# ---------------------------------------------------------------------------
# scheduler command
# ---------------------------------------------------------------------------

@cli.group()
def scheduler() -> None:
    """Task scheduler management."""


@scheduler.command("start")
def scheduler_start() -> None:
    """Start the background scheduler (weekly reports, daily stats)."""
    from core.scheduler import Scheduler

    gm = _get_manager()
    sched = Scheduler()

    def run_weekly() -> None:
        rg = ReportGenerator()
        report = gm.generate_weekly_report()
        rg.generate_weekly_report(report, save=True)
        console.print("[green]Weekly report generated.[/green]")

    def run_daily_stats() -> None:
        for ag in gm.registry.get_all_agents():
            ag.get_stats()

    sched.register_weekly_report(run_weekly)
    sched.register_daily_stats(run_daily_stats)

    started = sched.start()
    if started:
        _success("Scheduler started. Weekly reports on Monday 09:00 UTC.")
        _info("Press Ctrl-C to stop.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sched.stop()
            _info("Scheduler stopped.")
    else:
        _warn("Scheduler could not start (APScheduler may not be installed or scheduler is disabled).")
        _info("You can still run 'python cli.py report weekly' manually.")


@scheduler.command("jobs")
def scheduler_jobs() -> None:
    """List scheduled jobs."""
    from core.scheduler import Scheduler

    sched = Scheduler()
    jobs = sched.list_jobs()

    if not jobs:
        _info("No jobs registered. Start the scheduler first.")
        return

    for job in jobs:
        console.print(f"  [cyan]{job['job_id']}[/cyan]: {job['name']}")


# ---------------------------------------------------------------------------
# info command
# ---------------------------------------------------------------------------

@cli.command()
def info() -> None:
    """Show system information and configuration."""
    try:
        import anthropic
        anthropic_ver = anthropic.__version__
    except ImportError:
        anthropic_ver = "not installed"

    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    registry = _get_registry()

    console.print(Panel(
        f"""[bold cyan]Silver Team Management System[/bold cyan]
Version    : 1.0.0
Python     : {sys.version.split()[0]}
Anthropic  : {anthropic_ver}
API Key    : {'[green]set[/green]' if api_key_set else '[red]NOT SET[/red] — add to .env file'}
Agents     : {registry.count()} configured
Data Dir   : {PROJECT_ROOT / 'data'}
Config Dir : {PROJECT_ROOT / 'config'}

[dim]Run 'python cli.py --help' for all commands.[/dim]""",
        title="[bold]System Info[/bold]",
        border_style="blue",
    ))

    if not api_key_set:
        console.print(
            "\n[yellow]To enable real AI responses, create a .env file:[/yellow]\n"
            "  ANTHROPIC_API_KEY=sk-ant-...\n"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
