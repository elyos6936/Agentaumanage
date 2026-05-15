"""
BaseAgent — all specialist agents inherit from this class.
Uses the Anthropic SDK (claude-sonnet-4-6).
Gracefully degrades to mock responses when no API key is set.
"""

from __future__ import annotations

import os
import time
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

from .memory import AgentMemory


# ---------------------------------------------------------------------------
# Optional Anthropic import
# ---------------------------------------------------------------------------
try:
    import anthropic  # type: ignore

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    warnings.warn(
        "anthropic package not installed. Agents will use mock responses.",
        stacklevel=2,
    )


def _get_claude_client() -> Optional[Any]:
    """Return an Anthropic client if possible, else None."""
    if not _ANTHROPIC_AVAILABLE:
        return None
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return None


def _mock_response(prompt: str, agent_name: str, role: str) -> str:
    """Return a plausible mock response when the Claude API is unavailable."""
    return (
        f"[MOCK — no ANTHROPIC_API_KEY] {agent_name} ({role}) received task:\n"
        f'"{prompt[:200]}"\n\n'
        "Mock response: Task acknowledged and logged. Set ANTHROPIC_API_KEY "
        "in your .env file to enable real AI responses."
    )


# ---------------------------------------------------------------------------
# BaseAgent
# ---------------------------------------------------------------------------

class BaseAgent:
    """
    Base class for all Silver-Team agents.

    Attributes
    ----------
    id          Unique stable identifier (slug format).
    name        Human-readable name.
    role        Job title / specialisation.
    skills      List of competency strings.
    status      'active' | 'inactive' | 'busy'
    created_at  ISO timestamp.
    api_keys    Dict of service-specific API keys (not Anthropic).
    mcp_servers List of MCP server names this agent can access.
    """

    MODEL = "claude-sonnet-4-6"
    MAX_TOKENS = 4096

    def __init__(
        self,
        id: str,
        name: str,
        role: str,
        skills: List[str],
        status: str = "active",
        created_at: Optional[str] = None,
        api_keys: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[str]] = None,
        description: str = "",
        personality: str = "",
        **kwargs: Any,
    ) -> None:
        self.id = id
        self.name = name
        self.role = role
        self.skills: List[str] = skills
        self.status = status
        self.created_at: str = created_at or datetime.utcnow().isoformat()
        self.api_keys: Dict[str, str] = api_keys or {}
        self.mcp_servers: List[str] = mcp_servers or []
        self.description = description
        self.personality = personality

        # Persistent memory
        self.memory = AgentMemory(agent_id=self.id)

        # Lazy Claude client (shared per process — thread-safe reads)
        self._client: Optional[Any] = None
        self._client_checked = False

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get_client(self) -> Optional[Any]:
        if not self._client_checked:
            self._client = _get_claude_client()
            self._client_checked = True
        return self._client

    def _build_system_prompt(self) -> str:
        skills_str = ", ".join(self.skills)
        return (
            f"You are {self.name}, a specialist {self.role} on a digital marketing team "
            f"called the Silver Team.\n\n"
            f"Your core skills: {skills_str}\n\n"
            f"{('Background: ' + self.description) if self.description else ''}\n"
            f"{('Personality: ' + self.personality) if self.personality else ''}\n\n"
            "Always respond in the language used in the task. Be concise, actionable, "
            "and professional. When you provide recommendations, be specific and include "
            "measurable outcomes where possible."
        )

    def _call_claude(
        self,
        user_message: str,
        system_override: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call Claude API or fall back to mock."""
        client = self._get_client()
        if client is None:
            return _mock_response(user_message, self.name, self.role)

        system = system_override or self._build_system_prompt()
        tokens = max_tokens or self.MAX_TOKENS

        from dotenv import load_dotenv  # noqa: PLC0415

        load_dotenv()

        # Retry logic
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=self.MODEL,
                    max_tokens=tokens,
                    system=system,
                    messages=[{"role": "user", "content": user_message}],
                )
                return response.content[0].text
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)

        return (
            f"[API ERROR] {self.name} could not complete the task. "
            f"Last error: {last_exc}"
        )

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def execute_task(self, task: str, metadata: Optional[Dict] = None) -> str:
        """
        Execute a task and persist the result.

        Parameters
        ----------
        task     Natural-language task description.
        metadata Optional dict stored alongside the task record.

        Returns
        -------
        Agent's response as a string.
        """
        if self.status == "inactive":
            return f"[SKIPPED] {self.name} is currently inactive."

        self.status = "busy"
        start_ms = time.monotonic() * 1000

        try:
            result = self._call_claude(task)
            success = not result.startswith("[API ERROR]")
        except Exception as exc:  # noqa: BLE001
            result = f"[EXCEPTION] {exc}"
            success = False
        finally:
            self.status = "active"

        elapsed_ms = time.monotonic() * 1000 - start_ms
        self.memory.add_task_record(
            task=task,
            result=result,
            success=success,
            response_time_ms=elapsed_ms,
            metadata=metadata or {},
        )
        return result

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a structured performance report for this agent.

        Returns a dict that can be serialised to JSON / rendered as Markdown.
        """
        stats = self.get_stats()
        history = self.memory.get_task_history(last_n=10)
        evaluation = self.memory.get_self_evaluation()

        # Ask Claude to write a narrative summary
        if history:
            recent_tasks = "\n".join(
                f"- [{r['timestamp'][:10]}] {r['task'][:150]}"
                for r in history[-5:]
            )
            prompt = (
                f"Based on these recent tasks you have handled:\n{recent_tasks}\n\n"
                "Write a brief (3-5 bullet points) performance summary covering: "
                "key actions taken, outcomes achieved, and any patterns observed."
            )
            narrative = self._call_claude(prompt)
        else:
            narrative = "No tasks completed yet."

        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "role": self.role,
            "report_generated_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "narrative_summary": narrative,
            "recent_tasks": history[-5:] if history else [],
            "self_evaluation": evaluation,
        }

    def self_evaluate(self) -> Dict[str, Any]:
        """
        Ask the agent to analyse its last 10 tasks and produce a self-evaluation.
        Result is stored in memory under 'self_evaluation'.
        """
        history = self.memory.get_task_history(last_n=10)
        if not history:
            evaluation = {
                "strengths": ["Agent is freshly configured and ready to work."],
                "weaknesses": ["No task history to evaluate yet."],
                "improvement_plan": ["Complete at least 10 tasks before evaluation."],
                "overall_rating": "N/A",
            }
            self.memory.set_self_evaluation(evaluation)
            return evaluation

        tasks_text = "\n".join(
            f"{i+1}. [{r['timestamp'][:10]}] Task: {r['task'][:200]}\n"
            f"   Success: {r['success']} | Time: {r['response_time_ms']:.0f}ms\n"
            f"   Result excerpt: {r['result'][:300]}"
            for i, r in enumerate(history)
        )

        prompt = (
            f"You are performing a self-evaluation as {self.name}, {self.role}.\n\n"
            f"Here are your last {len(history)} task records:\n\n{tasks_text}\n\n"
            "Produce a JSON self-evaluation with these exact keys:\n"
            '- "strengths": list of 3 specific strengths demonstrated\n'
            '- "weaknesses": list of 2-3 areas needing improvement\n'
            '- "improvement_plan": list of 3 concrete actions to improve\n'
            '- "overall_rating": a rating from 1-10 with one sentence justification\n\n'
            "Respond ONLY with valid JSON, no markdown fences."
        )

        raw = self._call_claude(prompt)

        # Try to parse JSON; fall back to structured dict
        import json  # noqa: PLC0415

        try:
            evaluation = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            evaluation = {
                "strengths": ["Unable to parse structured evaluation."],
                "weaknesses": [],
                "improvement_plan": [],
                "overall_rating": raw[:200],
            }

        self.memory.set_self_evaluation(evaluation)
        return evaluation

    def update_memory(self, key: str, value: Any) -> None:
        """Store an arbitrary key-value pair in custom memory."""
        self.memory.set_custom(key, value)

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregated performance statistics."""
        stats = self.memory.get_stats()
        stats["agent_id"] = self.id
        stats["agent_name"] = self.name
        stats["role"] = self.role
        stats["status"] = self.status
        return stats

    def to_dict(self) -> Dict[str, Any]:
        """Serialise agent config (not memory) to a dict."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "skills": self.skills,
            "status": self.status,
            "created_at": self.created_at,
            "api_keys": self.api_keys,
            "mcp_servers": self.mcp_servers,
            "description": self.description,
            "personality": self.personality,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id!r} name={self.name!r} role={self.role!r}>"
