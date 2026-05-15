"""
LinkedInAgent — Sophie, LinkedIn Manager.
Specialises in B2B outreach, content creation, lead generation, and personal branding.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class LinkedInAgent(BaseAgent):
    """
    Sophie — LinkedIn Manager.

    Extended capabilities:
    - Draft LinkedIn posts and articles
    - Create outreach message sequences
    - Analyse LinkedIn profile and suggest improvements
    - Build connection strategies
    """

    def draft_post(self, topic: str, tone: str = "professional") -> str:
        """Draft a LinkedIn post on a given topic."""
        prompt = (
            f"Draft a LinkedIn post about: {topic}\n\n"
            f"Tone: {tone}\n"
            "Requirements:\n"
            "- Hook in the first line\n"
            "- 150-300 words\n"
            "- 3-5 relevant hashtags\n"
            "- Clear call-to-action\n"
            "- Formatted for LinkedIn (line breaks, emojis sparingly)"
        )
        return self.execute_task(prompt, metadata={"type": "draft_post", "topic": topic})

    def create_outreach_sequence(
        self, target_persona: str, value_proposition: str, num_messages: int = 3
    ) -> str:
        """Create a multi-step outreach sequence."""
        prompt = (
            f"Create a {num_messages}-message LinkedIn outreach sequence.\n\n"
            f"Target persona: {target_persona}\n"
            f"Value proposition: {value_proposition}\n\n"
            "For each message provide:\n"
            "- Message number and timing (e.g., Day 1, Day 5)\n"
            "- Subject/opening line\n"
            "- Full message body (under 300 characters each)\n"
            "- Follow-up trigger"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "outreach_sequence", "persona": target_persona},
        )

    def audit_profile(self, profile_data: Dict[str, Any]) -> str:
        """Audit a LinkedIn profile and suggest improvements."""
        profile_text = "\n".join(f"{k}: {v}" for k, v in profile_data.items())
        prompt = (
            f"Audit this LinkedIn profile and provide specific improvements:\n\n"
            f"{profile_text}\n\n"
            "Cover: headline optimisation, about section, experience bullets, "
            "featured section, skills endorsements, and overall profile strength score (1-10)."
        )
        return self.execute_task(prompt, metadata={"type": "profile_audit"})

    def suggest_connection_strategy(self, goal: str, industry: str) -> str:
        """Suggest a LinkedIn connection strategy."""
        prompt = (
            f"Design a LinkedIn connection strategy.\n\n"
            f"Goal: {goal}\n"
            f"Industry: {industry}\n\n"
            "Include: target connection types, personalised message templates, "
            "weekly activity schedule, and 30-day growth targets."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "connection_strategy", "goal": goal},
        )
