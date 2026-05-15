"""
ContentAgent — Nora, Content Manager.
Specialises in copywriting, blog posts, editorial calendars, and brand voice.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class ContentAgent(BaseAgent):
    """
    Nora — Content Manager.

    Extended capabilities:
    - Blog post outlines and full drafts
    - Editorial calendar planning
    - Brand voice guidelines
    - Content repurposing strategies
    """

    def write_blog_post(
        self,
        title: str,
        target_keyword: str,
        word_count: int = 1200,
        audience: str = "general",
    ) -> str:
        """Write a full SEO-optimised blog post."""
        prompt = (
            f"Write an SEO-optimised blog post.\n\n"
            f"Title: {title}\n"
            f"Target keyword: {target_keyword}\n"
            f"Target word count: {word_count}\n"
            f"Target audience: {audience}\n\n"
            "Structure:\n"
            "- Compelling intro (hook + thesis)\n"
            "- 4-6 H2 sections with H3 sub-points\n"
            "- Data points and statistics (cite sources)\n"
            "- Practical takeaways\n"
            "- Strong conclusion with CTA\n"
            "- Meta description (155 chars)\n"
            "- 5 internal link anchor text suggestions"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "blog_post", "title": title, "keyword": target_keyword},
        )

    def create_editorial_calendar(
        self,
        brand: str,
        month: str,
        channels: List[str],
        themes: Optional[List[str]] = None,
    ) -> str:
        """Build a monthly editorial calendar across multiple channels."""
        channels_str = ", ".join(channels)
        themes_str = ", ".join(themes) if themes else "brand story, education, entertainment, promotion"
        prompt = (
            f"Build a monthly editorial calendar for {month}.\n\n"
            f"Brand: {brand}\n"
            f"Channels: {channels_str}\n"
            f"Content themes: {themes_str}\n\n"
            "For each week provide:\n"
            "- Content theme / campaign\n"
            "- Specific topics per channel\n"
            "- Content format (blog/video/infographic/podcast)\n"
            "- Publication dates and times\n"
            "- Key messages and CTAs\n"
            "- Resources needed (design, video, etc.)"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "editorial_calendar", "brand": brand, "month": month},
        )

    def define_brand_voice(
        self,
        company: str,
        industry: str,
        values: List[str],
        target_audience: str,
    ) -> str:
        """Define or refine brand voice guidelines."""
        values_str = ", ".join(values)
        prompt = (
            f"Define brand voice guidelines.\n\n"
            f"Company: {company}\n"
            f"Industry: {industry}\n"
            f"Core values: {values_str}\n"
            f"Target audience: {target_audience}\n\n"
            "Produce a brand voice document with:\n"
            "1. Brand personality traits (4-6 adjectives with explanations)\n"
            "2. Tone variations per channel\n"
            "3. Words to use / words to avoid\n"
            "4. Sentence structure guidelines\n"
            "5. Sample approved copy vs. off-brand copy examples\n"
            "6. Checklist for content creators"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "brand_voice", "company": company},
        )

    def repurpose_content(
        self, original_content: str, source_format: str, target_formats: List[str]
    ) -> str:
        """Plan and draft content repurposing from one format to others."""
        targets = ", ".join(target_formats)
        prompt = (
            f"Repurpose content from {source_format} to: {targets}\n\n"
            f"Original content:\n{original_content[:2000]}\n\n"
            "For each target format provide:\n"
            "- Adapted version of the content\n"
            "- Format-specific optimisations\n"
            "- Platform-specific adjustments\n"
            "- Engagement hook tailored to each channel"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "content_repurposing", "source": source_format, "targets": target_formats},
        )

    def write_copy(
        self,
        copy_type: str,
        product_or_service: str,
        cta: str,
        word_limit: int = 100,
    ) -> str:
        """Write short-form marketing copy."""
        prompt = (
            f"Write {copy_type} copy.\n\n"
            f"Product/Service: {product_or_service}\n"
            f"Call-to-action: {cta}\n"
            f"Word limit: {word_limit}\n\n"
            "Provide 3 variations (A/B/C) with a brief rationale for each. "
            "Include: headline, body copy, and CTA button text."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "copy", "copy_type": copy_type},
        )
