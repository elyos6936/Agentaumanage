"""
FacebookAgent — Marcus, Facebook Manager.
Specialises in paid ads, community management, content scheduling, and Meta ecosystem.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class FacebookAgent(BaseAgent):
    """
    Marcus — Facebook Manager.

    Extended capabilities:
    - Create ad copy and targeting recommendations
    - Plan community engagement strategies
    - Build content calendars for Facebook
    - Analyse ad performance and optimise campaigns
    """

    def create_ad_copy(
        self,
        product: str,
        target_audience: str,
        objective: str,
        budget: Optional[float] = None,
    ) -> str:
        """Create Facebook ad copy with targeting recommendations."""
        budget_line = f"Monthly budget: ${budget}" if budget else "Budget: TBD"
        prompt = (
            f"Create Facebook ad copy for:\n\n"
            f"Product/Service: {product}\n"
            f"Target Audience: {target_audience}\n"
            f"Campaign Objective: {objective}\n"
            f"{budget_line}\n\n"
            "Deliver:\n"
            "1. Primary text (125 chars max)\n"
            "2. Headline (40 chars max)\n"
            "3. Description (30 chars max)\n"
            "4. Call-to-action button recommendation\n"
            "5. Audience targeting parameters (interests, behaviours, demographics)\n"
            "6. Ad format recommendation (image, video, carousel)"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "ad_copy", "product": product, "objective": objective},
        )

    def plan_community_engagement(self, page_niche: str, weekly_goal: str) -> str:
        """Plan a community engagement strategy."""
        prompt = (
            f"Design a Facebook community engagement plan.\n\n"
            f"Page niche: {page_niche}\n"
            f"Weekly goal: {weekly_goal}\n\n"
            "Include: post types and frequency, engagement tactics, "
            "response strategy for comments/messages, group management tips, "
            "and metrics to track."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "community_engagement", "niche": page_niche},
        )

    def create_content_calendar(
        self, brand: str, month: str, post_frequency: int = 5
    ) -> str:
        """Build a monthly Facebook content calendar."""
        prompt = (
            f"Create a Facebook content calendar for {month}.\n\n"
            f"Brand: {brand}\n"
            f"Target posts per week: {post_frequency}\n\n"
            "For each week provide: post topics, content types (image/video/link/story), "
            "best posting times, captions starters, and engagement hooks."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "content_calendar", "brand": brand, "month": month},
        )

    def analyse_ad_performance(self, metrics: Dict[str, Any]) -> str:
        """Analyse Facebook ad performance data and provide recommendations."""
        metrics_text = "\n".join(f"  {k}: {v}" for k, v in metrics.items())
        prompt = (
            f"Analyse these Facebook ad performance metrics:\n\n"
            f"{metrics_text}\n\n"
            "Provide: performance verdict, key issues, 5 specific optimisation "
            "recommendations, and projected improvement if recommendations are applied."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "performance_analysis"},
        )
