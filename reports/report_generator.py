"""
ReportGenerator — creates markdown and JSON reports for agents and the team.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"


def _ensure_reports_dir() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ReportGenerator:
    """
    Generates structured reports in Markdown and JSON formats.
    Works standalone or with GeneralManager.
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Agent-level report                                                   #
    # ------------------------------------------------------------------ #

    def generate_agent_report(
        self,
        agent_data: Dict[str, Any],
        save: bool = True,
    ) -> Dict[str, str]:
        """
        Generate both Markdown and JSON reports for a single agent.

        Parameters
        ----------
        agent_data   Output of BaseAgent.generate_report()
        save         Whether to write files to disk

        Returns
        -------
        Dict with keys: 'markdown', 'json', 'markdown_path', 'json_path'
        """
        md = self._agent_to_markdown(agent_data)
        js = json.dumps(agent_data, indent=2, ensure_ascii=False)

        result: Dict[str, str] = {"markdown": md, "json": js}

        if save:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            agent_id = agent_data.get("agent_id", "unknown")
            md_path = self.output_dir / f"{agent_id}_{ts}.md"
            json_path = self.output_dir / f"{agent_id}_{ts}.json"

            md_path.write_text(md, encoding="utf-8")
            json_path.write_text(js, encoding="utf-8")

            result["markdown_path"] = str(md_path)
            result["json_path"] = str(json_path)
            logger.info("Saved agent report: %s", md_path)

        return result

    def _agent_to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert agent report dict to Markdown."""
        lines: List[str] = []
        name = data.get("agent_name", "Unknown")
        role = data.get("role", "")
        generated_at = data.get("report_generated_at", "")
        stats = data.get("stats", {})
        narrative = data.get("narrative_summary", "")
        recent_tasks = data.get("recent_tasks", [])
        evaluation = data.get("self_evaluation")

        lines.append(f"# Performance Report: {name}")
        lines.append(f"**Role:** {role}")
        lines.append(f"**Generated:** {generated_at[:19].replace('T', ' ')} UTC")
        lines.append("")

        # Stats table
        lines.append("## Key Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Tasks Completed | {stats.get('tasks_completed', 0)} |")
        lines.append(f"| Tasks Failed | {stats.get('tasks_failed', 0)} |")
        lines.append(f"| Success Rate | {stats.get('success_rate', 0.0)}% |")
        lines.append(f"| Avg Response Time | {stats.get('avg_response_time_ms', 0.0):.0f} ms |")
        last_active = stats.get("last_active") or "Never"
        if last_active and last_active != "Never":
            last_active = last_active[:19].replace("T", " ")
        lines.append(f"| Last Active | {last_active} |")
        lines.append("")

        # Narrative
        lines.append("## Performance Summary")
        lines.append("")
        lines.append(narrative)
        lines.append("")

        # Recent tasks
        if recent_tasks:
            lines.append("## Recent Tasks")
            lines.append("")
            for task in recent_tasks:
                ts = task.get("timestamp", "")[:10]
                success_icon = "✓" if task.get("success") else "✗"
                task_text = task.get("task", "")[:100]
                lines.append(f"- [{ts}] {success_icon} {task_text}")
            lines.append("")

        # Self-evaluation
        if evaluation:
            lines.append("## Self-Evaluation")
            lines.append("")
            eval_ts = evaluation.get("timestamp", "")[:10]
            lines.append(f"*Last evaluated: {eval_ts}*")
            lines.append("")

            strengths = evaluation.get("strengths", [])
            if strengths:
                lines.append("**Strengths:**")
                for s in strengths:
                    lines.append(f"- {s}")
                lines.append("")

            weaknesses = evaluation.get("weaknesses", [])
            if weaknesses:
                lines.append("**Areas for Improvement:**")
                for w in weaknesses:
                    lines.append(f"- {w}")
                lines.append("")

            plan = evaluation.get("improvement_plan", [])
            if plan:
                lines.append("**Improvement Plan:**")
                for p in plan:
                    lines.append(f"1. {p}")
                lines.append("")

            rating = evaluation.get("overall_rating")
            if rating:
                lines.append(f"**Overall Rating:** {rating}")
                lines.append("")

        lines.append("---")
        lines.append(f"*Report generated by Silver Team Management System*")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Weekly team report                                                   #
    # ------------------------------------------------------------------ #

    def generate_weekly_report(
        self,
        team_report: Dict[str, Any],
        save: bool = True,
    ) -> Dict[str, str]:
        """
        Generate a full team weekly report from GeneralManager.generate_weekly_report().
        """
        md = self._weekly_to_markdown(team_report)
        js = json.dumps(team_report, indent=2, ensure_ascii=False)

        result: Dict[str, str] = {"markdown": md, "json": js}

        if save:
            week_of = team_report.get("week_of", datetime.utcnow().strftime("%Y-W%W"))
            safe_week = week_of.replace("-", "_")
            md_path = self.output_dir / f"weekly_report_{safe_week}.md"
            json_path = self.output_dir / f"weekly_report_{safe_week}.json"

            md_path.write_text(md, encoding="utf-8")
            json_path.write_text(js, encoding="utf-8")

            result["markdown_path"] = str(md_path)
            result["json_path"] = str(json_path)
            logger.info("Saved weekly report: %s", md_path)

        return result

    def _weekly_to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert weekly team report to Markdown."""
        lines: List[str] = []
        week_of = data.get("week_of", "Unknown")
        generated_at = data.get("generated_at", "")
        team_stats = data.get("team_stats", {})
        manager_analysis = data.get("manager_analysis", "")
        agent_reports = data.get("agent_reports", [])

        lines.append("# Silver Team — Weekly Performance Report")
        lines.append(f"**Week:** {week_of}")
        lines.append(f"**Generated:** {generated_at[:19].replace('T', ' ')} UTC")
        lines.append("")

        # Team stats
        lines.append("## Team Overview")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Active Agents | {team_stats.get('active_agents', 0)} |")
        lines.append(f"| Total Tasks | {team_stats.get('total_tasks', 0)} |")
        lines.append(f"| Successful Tasks | {team_stats.get('total_success', 0)} |")
        lines.append(f"| Failed Tasks | {team_stats.get('total_failed', 0)} |")
        lines.append(f"| Team Success Rate | {team_stats.get('team_success_rate', 0.0)}% |")
        lines.append("")

        # Manager analysis
        if manager_analysis:
            lines.append("## Manager's Strategic Analysis")
            lines.append("")
            lines.append(manager_analysis)
            lines.append("")

        # Individual agent summaries
        lines.append("## Agent Performance Summaries")
        lines.append("")

        for report in agent_reports:
            if "error" in report:
                lines.append(f"### {report.get('agent_name', 'Unknown')} ⚠️")
                lines.append(f"*Error: {report['error']}*")
                lines.append("")
                continue

            name = report.get("agent_name", "Unknown")
            role = report.get("role", "")
            stats = report.get("stats", {})
            narrative = report.get("narrative_summary", "No data.")

            lines.append(f"### {name} ({role})")
            lines.append(
                f"Tasks: {stats.get('tasks_completed', 0)} completed | "
                f"{stats.get('success_rate', 0.0)}% success rate"
            )
            lines.append("")
            lines.append(narrative[:500])
            lines.append("")

        lines.append("---")
        lines.append("*Silver Team Management System — Weekly Report*")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Improvement plan report                                             #
    # ------------------------------------------------------------------ #

    def generate_improvement_report(
        self,
        improvement_data: Dict[str, Any],
        save: bool = True,
    ) -> Dict[str, str]:
        """Generate a self-improvement plan report."""
        md = self._improvement_to_markdown(improvement_data)
        js = json.dumps(improvement_data, indent=2, ensure_ascii=False)

        result: Dict[str, str] = {"markdown": md, "json": js}

        if save:
            ts = datetime.utcnow().strftime("%Y%m%d")
            md_path = self.output_dir / f"improvement_plan_{ts}.md"
            json_path = self.output_dir / f"improvement_plan_{ts}.json"

            md_path.write_text(md, encoding="utf-8")
            json_path.write_text(js, encoding="utf-8")

            result["markdown_path"] = str(md_path)
            result["json_path"] = str(json_path)

        return result

    def _improvement_to_markdown(self, data: Dict[str, Any]) -> str:
        lines: List[str] = []
        generated_at = data.get("generated_at", "")
        company_plan = data.get("company_improvement_plan", "")
        evaluations = data.get("individual_evaluations", [])

        lines.append("# Silver Team — Self-Improvement Plan")
        lines.append(f"**Generated:** {generated_at[:19].replace('T', ' ')} UTC")
        lines.append("")

        if company_plan:
            lines.append("## Company-Wide Improvement Plan")
            lines.append("")
            lines.append(company_plan)
            lines.append("")

        if evaluations:
            lines.append("## Individual Agent Evaluations")
            lines.append("")
            for ev in evaluations:
                name = ev.get("agent_name", "Unknown")
                role = ev.get("role", "")
                rating = ev.get("overall_rating", "N/A")
                lines.append(f"### {name} ({role})")
                lines.append(f"**Rating:** {rating}")
                lines.append("")
                strengths = ev.get("strengths", [])
                if strengths:
                    lines.append("**Strengths:** " + " | ".join(strengths))
                weaknesses = ev.get("weaknesses", [])
                if weaknesses:
                    lines.append("**Areas to Improve:** " + " | ".join(weaknesses))
                lines.append("")

        lines.append("---")
        lines.append("*Silver Team Self-Improvement Analysis*")

        return "\n".join(lines)

    def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports in the output directory."""
        reports = []
        for path in sorted(self.output_dir.glob("*.json"), reverse=True):
            stat = path.stat()
            reports.append({
                "filename": path.name,
                "path": str(path),
                "size_kb": round(stat.st_size / 1024, 1),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
        return reports
