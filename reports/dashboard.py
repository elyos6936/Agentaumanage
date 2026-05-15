"""
Dashboard — live terminal dashboard for Silver Team using the Rich library.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.manager import GeneralManager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.columns import Columns
    from rich.align import Align

    _RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RICH_AVAILABLE = False


SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.json"


def _load_refresh_interval() -> int:
    try:
        import json
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("dashboard", {}).get("refresh_interval_seconds", 5)
    except Exception:
        return 5


class Dashboard:
    """
    Live terminal dashboard showing team stats, agent statuses, and recent activity.
    Requires the `rich` library.
    """

    def __init__(self, manager: "GeneralManager") -> None:
        self.manager = manager
        self.refresh_interval = _load_refresh_interval()
        if _RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None  # type: ignore[assignment]

    # ------------------------------------------------------------------ #
    # Static snapshot (no live refresh)                                   #
    # ------------------------------------------------------------------ #

    def show_snapshot(self) -> None:
        """Print a single-shot dashboard snapshot to the terminal."""
        if not _RICH_AVAILABLE:
            self._fallback_print()
            return

        self.console.print(self._build_header())
        self.console.print(self._build_team_table())
        self.console.print(self._build_stats_panel())

    def _fallback_print(self) -> None:
        """Minimal fallback when Rich is not installed."""
        print("\n=== SILVER TEAM DASHBOARD ===")
        print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        agents = self.manager.registry.list_agents()
        for a in agents:
            status = a["status"].upper()
            tasks = a["tasks_completed"]
            rate = a["success_rate"]
            print(f"  [{status}] {a['name']} ({a['role']})")
            print(f"         Tasks: {tasks} | Success: {rate}%")
        print()

    # ------------------------------------------------------------------ #
    # Live auto-refresh dashboard                                         #
    # ------------------------------------------------------------------ #

    def run_live(self, duration_seconds: Optional[int] = None) -> None:
        """
        Run the live dashboard.

        Parameters
        ----------
        duration_seconds   Run for this many seconds, then exit.
                           None = run until Ctrl-C.
        """
        if not _RICH_AVAILABLE:
            print("[WARNING] rich library not installed. Showing static snapshot.")
            self._fallback_print()
            return

        start = time.monotonic()
        try:
            with Live(
                self._build_layout(),
                console=self.console,
                refresh_per_second=1,
                screen=True,
            ) as live:
                while True:
                    time.sleep(self.refresh_interval)
                    live.update(self._build_layout())
                    if duration_seconds and (time.monotonic() - start) >= duration_seconds:
                        break
        except KeyboardInterrupt:
            pass
        finally:
            self.console.print("\n[bold green]Dashboard closed.[/bold green]")

    # ------------------------------------------------------------------ #
    # Layout builders                                                      #
    # ------------------------------------------------------------------ #

    def _build_layout(self) -> Any:
        """Build the full dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(self._build_header(), name="header", size=5),
            Layout(name="body"),
            Layout(self._build_footer(), name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(self._build_team_table(), name="agents", ratio=3),
            Layout(self._build_stats_panel(), name="stats", ratio=2),
        )
        return layout

    def _build_header(self) -> Panel:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        title = Text("🌟 SILVER TEAM — Management Dashboard", style="bold white on dark_blue")
        sub = Text(f" {ts} | Press Ctrl-C to exit", style="dim")
        return Panel(
            Align.center(title + sub),
            style="bold blue",
            box=box.DOUBLE_EDGE,
        )

    def _build_team_table(self) -> Panel:
        agents = self.manager.registry.list_agents()

        table = Table(
            title="Team Agents",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            expand=True,
        )
        table.add_column("Agent", style="bold", min_width=8)
        table.add_column("Role", style="yellow", min_width=18)
        table.add_column("Status", justify="center", min_width=8)
        table.add_column("Tasks", justify="right", min_width=6)
        table.add_column("Success%", justify="right", min_width=9)
        table.add_column("Last Active", min_width=12)

        status_styles = {
            "active": "[bold green]● active[/bold green]",
            "busy": "[bold yellow]◎ busy[/bold yellow]",
            "inactive": "[dim red]○ inactive[/dim red]",
        }

        for a in agents:
            status_str = status_styles.get(
                a["status"], f"[dim]{a['status']}[/dim]"
            )
            last_active = a.get("last_active") or "never"
            if last_active and last_active != "never":
                last_active = last_active[5:16].replace("T", " ")

            success = a["success_rate"]
            success_style = (
                "bold green" if success >= 90
                else "yellow" if success >= 70
                else "bold red"
            )

            table.add_row(
                a["name"],
                a["role"],
                status_str,
                str(a["tasks_completed"]),
                f"[{success_style}]{success}%[/{success_style}]",
                last_active,
            )

        return Panel(table, title="[bold]Agents[/bold]", border_style="blue")

    def _build_stats_panel(self) -> Panel:
        agents = self.manager.registry.list_agents()

        total_tasks = sum(a["tasks_completed"] for a in agents)
        active_count = sum(1 for a in agents if a["status"] == "active")
        busy_count = sum(1 for a in agents if a["status"] == "busy")
        inactive_count = sum(1 for a in agents if a["status"] == "inactive")

        rates = [a["success_rate"] for a in agents if a["tasks_completed"] > 0]
        avg_rate = round(sum(rates) / len(rates), 1) if rates else 0.0

        lines = [
            f"[bold cyan]Team Stats[/bold cyan]",
            "",
            f"  Total Agents   : [bold]{len(agents)}[/bold]",
            f"  Active         : [bold green]{active_count}[/bold green]",
            f"  Busy           : [bold yellow]{busy_count}[/bold yellow]",
            f"  Inactive       : [dim red]{inactive_count}[/dim red]",
            "",
            f"  Total Tasks    : [bold]{total_tasks}[/bold]",
            f"  Avg Success    : [bold]{avg_rate}%[/bold]",
            "",
            "[bold cyan]Quick Reference[/bold cyan]",
            "",
            "  python cli.py agent list",
            "  python cli.py manager run '<task>'",
            "  python cli.py report weekly",
        ]

        return Panel(
            "\n".join(lines),
            title="[bold]Stats & Help[/bold]",
            border_style="blue",
        )

    def _build_footer(self) -> Panel:
        msg = (
            "[dim]Silver Team v1.0 | "
            "Commands: agent list | agent run | manager run | report weekly | "
            "mcp add | dashboard[/dim]"
        )
        return Panel(Align.center(msg), border_style="dim")
