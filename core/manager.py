"""
GeneralManager — the orchestrator for the Silver Team.
Routes tasks to specialist agents, consolidates reports, runs self-improvement loops.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_registry import AgentRegistry
from .agent_base import BaseAgent, _get_claude_client, _mock_response

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"


# -----------------------------------------------------------------------
# Domain → agent role mapping (used for task routing)
# -----------------------------------------------------------------------
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "linkedin": ["linkedin", "b2b", "professional network", "lead gen", "personal brand"],
    "facebook": ["facebook", "meta", "fb", "paid ads", "community management"],
    "instagram": ["instagram", "reels", "stories", "influencer", "hashtag", "visual"],
    "tiktok": ["tiktok", "viral", "short-form video", "trend", "sound"],
    "seo": ["seo", "keyword", "backlink", "search engine", "organic traffic", "on-page", "technical seo"],
    "content": ["content", "copy", "blog", "editorial", "writing", "brand voice", "storytelling"],
    "analytics": ["analytics", "kpi", "dashboard", "data", "metric", "performance", "roi"],
    "email": ["email", "newsletter", "campaign", "automation", "segmentation", "drip", "subscriber"],
}


def _match_domain(task: str) -> Optional[str]:
    """Return the best-matching domain name or None."""
    task_lower = task.lower()
    scores: Dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in task_lower)
        if score > 0:
            scores[domain] = score
    if not scores:
        return None
    return max(scores, key=lambda d: scores[d])


class GeneralManager:
    """
    Orchestrates the Silver Team agents.

    - Routes tasks to the correct specialist
    - Can spawn new agents on demand
    - Consolidates weekly reports
    - Runs team-wide self-improvement analysis
    """

    MODEL = "claude-sonnet-4-6"
    MAX_TOKENS = 4096

    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        self.registry: AgentRegistry = registry or AgentRegistry()
        self._client: Optional[Any] = None
        self._client_checked = False
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get_client(self) -> Optional[Any]:
        if not self._client_checked:
            self._client = _get_claude_client()
            self._client_checked = True
        return self._client

    def _build_system_prompt(self) -> str:
        agents = self.registry.list_agents()
        team_list = "\n".join(
            f"- {a['name']} ({a['role']}): {a['tasks_completed']} tasks completed"
            for a in agents
        )
        return (
            "You are the General Manager of the Silver Team, an elite digital marketing "
            "multi-agent team. Your team consists of:\n\n"
            f"{team_list}\n\n"
            "Your responsibilities:\n"
            "1. Orchestrate team members to complete complex marketing tasks\n"
            "2. Provide strategic direction and cross-channel coordination\n"
            "3. Analyse team performance and drive continuous improvement\n"
            "4. Make data-driven decisions to maximise marketing ROI\n\n"
            "Be strategic, decisive, and always focused on measurable outcomes."
        )

    def _call_claude(self, user_message: str, system_override: Optional[str] = None) -> str:
        client = self._get_client()
        if client is None:
            return _mock_response(user_message, "General Manager", "Team Orchestrator")

        system = system_override or self._build_system_prompt()
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=self.MODEL,
                    max_tokens=self.MAX_TOKENS,
                    system=system,
                    messages=[{"role": "user", "content": user_message}],
                )
                return response.content[0].text
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)

        return f"[API ERROR] General Manager could not complete the task. Last error: {last_exc}"

    # ------------------------------------------------------------------ #
    # Task routing                                                         #
    # ------------------------------------------------------------------ #

    def route_task(self, task: str) -> Dict[str, Any]:
        """
        Intelligently route a task to the best-suited agent.

        Returns a dict with: agent_name, agent_id, domain, result.
        """
        domain = _match_domain(task)
        agent: Optional[BaseAgent] = None

        if domain:
            # Try to find an agent whose role matches the domain
            for candidate in self.registry.get_all_agents():
                if domain in candidate.role.lower() or domain in candidate.id.lower():
                    agent = candidate
                    break

        if agent is None:
            # Fall back: ask Claude to pick
            agents_info = "\n".join(
                f"- {a.name} ({a.role}): skills = {', '.join(a.skills[:4])}"
                for a in self.registry.get_all_agents()
            )
            routing_prompt = (
                f"Given this task: '{task}'\n\n"
                f"And these available agents:\n{agents_info}\n\n"
                "Which agent is best suited? Reply with ONLY the agent's name."
            )
            chosen_name = self._call_claude(routing_prompt).strip()
            agent = self.registry.get_agent(chosen_name)

        if agent is None:
            # Last resort: first active agent
            all_agents = self.registry.get_all_agents()
            agent = next((a for a in all_agents if a.status == "active"), all_agents[0] if all_agents else None)

        if agent is None:
            return {
                "agent_name": "None",
                "agent_id": "none",
                "domain": domain,
                "result": "[ERROR] No agents available to handle this task.",
                "error": True,
            }

        logger.info("Routing task to %s (%s).", agent.name, agent.role)
        result = agent.execute_task(task, metadata={"routed_by": "general_manager", "domain": domain})

        return {
            "agent_name": agent.name,
            "agent_id": agent.id,
            "domain": domain,
            "result": result,
            "error": False,
        }

    def run_task(self, task: str) -> str:
        """
        Manager-level task execution: may coordinate multiple agents.
        Returns a consolidated response.
        """
        # For complex tasks, manager uses its own Claude context to plan
        plan_prompt = (
            f"Task: {task}\n\n"
            "As General Manager, briefly outline how you will coordinate the team "
            "to complete this task. Then provide the consolidated deliverable."
        )
        return self._call_claude(plan_prompt)

    def assign_task_to_agent(self, task: str, agent_name: str) -> str:
        """Assign a task to a specific agent by name or id."""
        agent = self.registry.get_agent(agent_name)
        if agent is None:
            return f"[ERROR] Agent '{agent_name}' not found."
        return agent.execute_task(task)

    # ------------------------------------------------------------------ #
    # Reporting                                                            #
    # ------------------------------------------------------------------ #

    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate a full team weekly report.
        Consolidates individual agent reports + adds manager analysis.
        """
        timestamp = datetime.utcnow().isoformat()
        agent_reports = []

        for agent in self.registry.get_all_agents():
            try:
                report = agent.generate_report()
                agent_reports.append(report)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to get report from %s: %s", agent.name, exc)
                agent_reports.append({
                    "agent_name": agent.name,
                    "role": agent.role,
                    "error": str(exc),
                })

        # Build team summary text for Claude
        summary_parts = []
        for r in agent_reports:
            if "error" not in r:
                stats = r.get("stats", {})
                summary_parts.append(
                    f"**{r['agent_name']}** ({r['role']}): "
                    f"{stats.get('tasks_completed', 0)} tasks, "
                    f"{stats.get('success_rate', 0)}% success rate"
                )

        team_summary_text = "\n".join(summary_parts) if summary_parts else "No data available."

        manager_analysis = self._call_claude(
            f"Weekly performance summary for your team:\n\n{team_summary_text}\n\n"
            "Provide a 5-bullet strategic analysis covering: "
            "top performers, areas of concern, cross-channel opportunities, "
            "recommended priorities for next week, and one innovation suggestion."
        )

        report = {
            "report_type": "weekly",
            "generated_at": timestamp,
            "week_of": datetime.utcnow().strftime("%Y-W%W"),
            "total_agents": len(agent_reports),
            "agent_reports": agent_reports,
            "manager_analysis": manager_analysis,
            "team_stats": self._compute_team_stats(agent_reports),
        }

        # Persist
        self._save_report(report, f"weekly_{datetime.utcnow().strftime('%Y%m%d')}")
        return report

    def _compute_team_stats(self, agent_reports: List[Dict]) -> Dict[str, Any]:
        total_tasks = 0
        total_success = 0
        total_failed = 0
        for r in agent_reports:
            if "stats" in r:
                s = r["stats"]
                total_tasks += s.get("tasks_completed", 0) + s.get("tasks_failed", 0)
                total_success += s.get("tasks_completed", 0)
                total_failed += s.get("tasks_failed", 0)
        return {
            "total_tasks": total_tasks,
            "total_success": total_success,
            "total_failed": total_failed,
            "team_success_rate": round(total_success / total_tasks * 100, 1) if total_tasks > 0 else 0.0,
            "active_agents": sum(
                1 for a in self.registry.get_all_agents() if a.status == "active"
            ),
        }

    def _save_report(self, report: Dict, filename: str) -> Path:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORTS_DIR / f"{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("Report saved: %s", json_path)
        return json_path

    # ------------------------------------------------------------------ #
    # Self-improvement loop                                                #
    # ------------------------------------------------------------------ #

    def run_team_self_improvement(self) -> Dict[str, Any]:
        """
        Trigger self-evaluation on all agents, then produce a company-wide
        improvement plan.
        """
        evaluations: List[Dict] = []

        for agent in self.registry.get_all_agents():
            try:
                evaluation = agent.self_evaluate()
                evaluations.append({
                    "agent_name": agent.name,
                    "role": agent.role,
                    **evaluation,
                })
            except Exception as exc:  # noqa: BLE001
                logger.error("Self-eval failed for %s: %s", agent.name, exc)

        # Summarise for Claude
        eval_text = "\n\n".join(
            f"**{e['agent_name']}** ({e['role']}):\n"
            f"  Strengths: {e.get('strengths', [])}\n"
            f"  Weaknesses: {e.get('weaknesses', [])}\n"
            f"  Rating: {e.get('overall_rating', 'N/A')}"
            for e in evaluations
        )

        company_plan = self._call_claude(
            f"Self-evaluations from all team members:\n\n{eval_text}\n\n"
            "As General Manager, produce a company-wide improvement plan with:\n"
            "1. Top 3 team strengths to leverage\n"
            "2. Top 3 team-wide improvement areas\n"
            "3. 5 concrete action items for the next 30 days\n"
            "4. Any structural changes recommended (new roles, tool additions, etc.)"
        )

        result = {
            "generated_at": datetime.utcnow().isoformat(),
            "individual_evaluations": evaluations,
            "company_improvement_plan": company_plan,
        }

        self._save_report(result, f"improvement_plan_{datetime.utcnow().strftime('%Y%m%d')}")
        return result

    # ------------------------------------------------------------------ #
    # Agent management                                                     #
    # ------------------------------------------------------------------ #

    def spawn_agent(
        self,
        name: str,
        role: str,
        skills: List[str],
        description: str = "",
        personality: str = "",
        api_keys: Optional[Dict] = None,
        mcp_servers: Optional[List[str]] = None,
    ) -> BaseAgent:
        """Spawn a new agent dynamically and register it."""
        agent = self.registry.create_agent(
            name=name,
            role=role,
            skills=skills,
            description=description,
            personality=personality,
            api_keys=api_keys or {},
            mcp_servers=mcp_servers or [],
        )
        logger.info("Spawned new agent: %s (%s).", name, role)
        return agent

    def get_team_status(self) -> Dict[str, Any]:
        """Return a snapshot of the entire team's current status."""
        agents = self.registry.list_agents()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(agents),
            "agents": agents,
            "scheduler_enabled": True,
        }

    def __repr__(self) -> str:
        return f"<GeneralManager agents={self.registry.count()}>"
