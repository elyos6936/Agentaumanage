"""
EmailAgent — Eli, Email Marketing Manager.
Specialises in campaigns, automation, segmentation, and A/B testing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class EmailAgent(BaseAgent):
    """
    Eli — Email Marketing Manager.

    Extended capabilities:
    - Email sequence creation
    - Subject line A/B testing
    - Segmentation strategies
    - Deliverability optimisation
    - Automation workflow design
    """

    def write_email_sequence(
        self,
        sequence_type: str,
        product_or_service: str,
        audience_segment: str,
        num_emails: int = 5,
    ) -> str:
        """Write a complete email sequence."""
        prompt = (
            f"Write a {num_emails}-email {sequence_type} sequence.\n\n"
            f"Product/Service: {product_or_service}\n"
            f"Audience segment: {audience_segment}\n\n"
            f"For each of the {num_emails} emails provide:\n"
            "- Email number and send timing (e.g., Day 1, Day 3, Day 7)\n"
            "- Subject line + preview text\n"
            "- Full email body (personalisation tokens where relevant)\n"
            "- Primary CTA\n"
            "- A/B test suggestion for this email\n"
            "- Success metric to track"
        )
        return self.execute_task(
            prompt,
            metadata={
                "type": "email_sequence",
                "sequence_type": sequence_type,
                "num_emails": num_emails,
            },
        )

    def generate_subject_lines(
        self,
        email_topic: str,
        audience: str,
        count: int = 10,
    ) -> str:
        """Generate and score subject line options."""
        prompt = (
            f"Generate {count} email subject lines for:\n\n"
            f"Email topic: {email_topic}\n"
            f"Audience: {audience}\n\n"
            "For each subject line provide:\n"
            "- The subject line (max 50 characters)\n"
            "- Preview text (max 90 characters)\n"
            "- Psychological trigger used\n"
            "- Predicted open rate range\n"
            "Categorise them by type: curiosity, urgency, benefit, personalisation, social proof."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "subject_lines", "topic": email_topic},
        )

    def design_automation_workflow(
        self,
        trigger_event: str,
        goal: str,
        audience: str,
    ) -> str:
        """Design an email automation workflow."""
        prompt = (
            f"Design an email automation workflow.\n\n"
            f"Trigger event: {trigger_event}\n"
            f"Goal: {goal}\n"
            f"Audience: {audience}\n\n"
            "Produce:\n"
            "1. Workflow diagram description (step-by-step)\n"
            "2. Each email's purpose and timing\n"
            "3. Branching conditions (if/then logic)\n"
            "4. Exit conditions\n"
            "5. Re-engagement path for non-openers\n"
            "6. Suppression rules\n"
            "7. KPIs to measure workflow effectiveness"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "automation_workflow", "trigger": trigger_event},
        )

    def create_segmentation_strategy(
        self,
        list_size: int,
        available_data_points: List[str],
        business_goals: List[str],
    ) -> str:
        """Build an email list segmentation strategy."""
        data_points = ", ".join(available_data_points)
        goals = ", ".join(business_goals)
        prompt = (
            f"Build an email list segmentation strategy.\n\n"
            f"List size: {list_size:,} subscribers\n"
            f"Available data points: {data_points}\n"
            f"Business goals: {goals}\n\n"
            "Define:\n"
            "1. Primary segments (4-6) with criteria and estimated sizes\n"
            "2. Behavioural segments based on engagement\n"
            "3. RFM (Recency/Frequency/Monetary) segmentation approach\n"
            "4. Personalisation opportunities per segment\n"
            "5. Send frequency recommendations per segment\n"
            "6. Re-engagement strategy for cold subscribers"
        )
        return self.execute_task(
            prompt,
            metadata={
                "type": "segmentation_strategy",
                "list_size": list_size,
            },
        )

    def optimise_deliverability(
        self,
        current_open_rate: float,
        bounce_rate: float,
        spam_rate: float,
        esp: str = "generic",
    ) -> str:
        """Provide email deliverability optimisation recommendations."""
        prompt = (
            f"Optimise email deliverability.\n\n"
            f"Current metrics:\n"
            f"  Open rate: {current_open_rate}%\n"
            f"  Bounce rate: {bounce_rate}%\n"
            f"  Spam complaint rate: {spam_rate}%\n"
            f"  ESP platform: {esp}\n\n"
            "Diagnose issues and provide:\n"
            "1. Deliverability health score (1-10)\n"
            "2. Critical issues to fix immediately\n"
            "3. Technical setup checklist (SPF, DKIM, DMARC)\n"
            "4. List hygiene recommendations\n"
            "5. Content and sending practice improvements\n"
            "6. 30-day recovery plan with expected metric improvements"
        )
        return self.execute_task(
            prompt,
            metadata={
                "type": "deliverability_optimisation",
                "open_rate": current_open_rate,
                "bounce_rate": bounce_rate,
            },
        )
