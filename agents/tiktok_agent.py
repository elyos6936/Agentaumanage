"""
TikTokAgent — Kai, TikTok Manager.
Specialises in viral content creation, trends, short-form video strategy.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class TikTokAgent(BaseAgent):
    """
    Kai — TikTok Manager.

    Extended capabilities:
    - Viral video hooks and scripts
    - Trend analysis and adaptation
    - TikTok ads strategy
    - Duet and stitch strategies
    """

    def create_viral_concept(self, brand: str, trend_topic: str) -> str:
        """Create a viral TikTok video concept."""
        prompt = (
            f"Create a viral TikTok video concept.\n\n"
            f"Brand: {brand}\n"
            f"Trend/Topic to leverage: {trend_topic}\n\n"
            "Deliver:\n"
            "1. Video hook (first 2 seconds — exactly what the viewer sees)\n"
            "2. Full 30-60 second script with timestamps\n"
            "3. Trending sound/audio recommendation\n"
            "4. On-screen text and overlays\n"
            "5. Hashtag strategy (mix of trending + niche)\n"
            "6. Best time to post\n"
            "7. Virality prediction score (1-10) with reasoning"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "viral_concept", "brand": brand, "trend": trend_topic},
        )

    def analyse_trends(self, industry: str, timeframe: str = "this week") -> str:
        """Analyse TikTok trends for a given industry."""
        prompt = (
            f"Analyse TikTok trends relevant to:\n\n"
            f"Industry: {industry}\n"
            f"Timeframe: {timeframe}\n\n"
            "Provide:\n"
            "1. Top 5 trending content formats\n"
            "2. Trending sounds/songs brands should leverage\n"
            "3. Viral challenges to consider joining\n"
            "4. Competitor content analysis\n"
            "5. 3 specific content ideas to implement this week"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "trend_analysis", "industry": industry},
        )

    def write_hooks(self, topic: str, count: int = 10) -> str:
        """Generate multiple TikTok video hook options."""
        prompt = (
            f"Write {count} different TikTok video hooks for this topic: {topic}\n\n"
            "Each hook should:\n"
            "- Be 10 words or fewer\n"
            "- Create immediate curiosity or FOMO\n"
            "- Work as on-screen text and spoken word\n"
            "Rate each hook 1-10 for virality potential with one-line reasoning."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "hooks", "topic": topic},
        )

    def plan_tiktok_ads(
        self,
        product: str,
        target_age_group: str,
        budget: float,
        objective: str = "awareness",
    ) -> str:
        """Create a TikTok ads strategy."""
        prompt = (
            f"Create a TikTok ads strategy.\n\n"
            f"Product/Service: {product}\n"
            f"Target age group: {target_age_group}\n"
            f"Monthly budget: ${budget}\n"
            f"Objective: {objective}\n\n"
            "Include: ad format selection, targeting parameters, "
            "creative brief (script + visuals), bidding strategy, "
            "A/B test variables, and expected KPIs."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "tiktok_ads", "product": product, "budget": budget},
        )
