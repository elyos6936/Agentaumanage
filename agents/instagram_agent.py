"""
InstagramAgent — Léa, Instagram Manager.
Specialises in visual content strategy, reels, influencer outreach, and hashtags.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class InstagramAgent(BaseAgent):
    """
    Léa — Instagram Manager.

    Extended capabilities:
    - Reel concept and script creation
    - Hashtag research strategies
    - Influencer outreach templates
    - Feed aesthetic planning
    """

    def create_reel_concept(
        self, topic: str, brand_voice: str = "authentic"
    ) -> str:
        """Create a detailed Reel concept with script outline."""
        prompt = (
            f"Create an Instagram Reel concept.\n\n"
            f"Topic: {topic}\n"
            f"Brand voice: {brand_voice}\n\n"
            "Deliver:\n"
            "1. Hook (first 3 seconds) — what viewer sees and hears\n"
            "2. Content arc (15-30 seconds)\n"
            "3. Call-to-action\n"
            "4. On-screen text suggestions\n"
            "5. Audio/music recommendation\n"
            "6. Trending sounds to consider\n"
            "7. Caption (150 words max) + 15-20 hashtags"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "reel_concept", "topic": topic},
        )

    def research_hashtags(self, niche: str, post_type: str = "general") -> str:
        """Research and categorise hashtags for a given niche."""
        prompt = (
            f"Research Instagram hashtags for:\n\n"
            f"Niche: {niche}\n"
            f"Post type: {post_type}\n\n"
            "Provide 30 hashtags grouped into:\n"
            "- Large (1M+ posts): 5 hashtags\n"
            "- Medium (100K-1M posts): 10 hashtags\n"
            "- Small/niche (<100K posts): 10 hashtags\n"
            "- Branded/campaign: 5 hashtags\n"
            "Also explain the ideal mix strategy and when to rotate."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "hashtag_research", "niche": niche},
        )

    def create_influencer_outreach(
        self,
        brand: str,
        campaign_goal: str,
        influencer_tier: str = "micro",
    ) -> str:
        """Create an influencer outreach strategy and message templates."""
        prompt = (
            f"Create an influencer outreach strategy for:\n\n"
            f"Brand: {brand}\n"
            f"Campaign goal: {campaign_goal}\n"
            f"Target influencer tier: {influencer_tier} (nano/micro/macro/mega)\n\n"
            "Include: ideal influencer profile, DM outreach template, "
            "email pitch template, negotiation talking points, "
            "brief template for influencers, and KPIs to track."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "influencer_outreach", "brand": brand},
        )

    def plan_feed_aesthetic(self, brand_identity: str, colour_palette: str) -> str:
        """Plan a cohesive Instagram feed aesthetic."""
        prompt = (
            f"Plan a cohesive Instagram feed aesthetic.\n\n"
            f"Brand identity: {brand_identity}\n"
            f"Colour palette: {colour_palette}\n\n"
            "Provide: visual theme direction, content pillars (3-5), "
            "photo editing style guide, grid layout pattern, "
            "caption style, and 10 post ideas to launch the aesthetic."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "feed_aesthetic"},
        )
