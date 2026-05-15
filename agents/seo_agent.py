"""
SEOAgent — Alex, SEO Manager.
Specialises in keyword research, on-page SEO, backlinks, and technical SEO.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent


class SEOAgent(BaseAgent):
    """
    Alex — SEO Manager.

    Extended capabilities:
    - Keyword research and clustering
    - On-page SEO audits
    - Technical SEO checklist
    - Backlink strategy
    - Content gap analysis
    """

    def research_keywords(
        self,
        topic: str,
        target_country: str = "US",
        intent: str = "informational",
    ) -> str:
        """Research SEO keywords for a given topic."""
        prompt = (
            f"Conduct keyword research for:\n\n"
            f"Topic: {topic}\n"
            f"Target country: {target_country}\n"
            f"Search intent: {intent}\n\n"
            "Provide:\n"
            "1. Primary keyword (highest-value target)\n"
            "2. 5 secondary keywords with estimated search volume range\n"
            "3. 10 long-tail keywords (low competition, high intent)\n"
            "4. 5 LSI (Latent Semantic Indexing) terms\n"
            "5. Featured snippet opportunities\n"
            "6. People Also Ask questions to target\n"
            "7. Keyword difficulty assessment (easy/medium/hard)"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "keyword_research", "topic": topic, "country": target_country},
        )

    def audit_on_page_seo(self, url: str, page_content: str) -> str:
        """Perform an on-page SEO audit."""
        prompt = (
            f"Perform an on-page SEO audit.\n\n"
            f"URL: {url}\n"
            f"Page content summary:\n{page_content[:1000]}\n\n"
            "Audit and score (1-10) each element:\n"
            "- Title tag (length, keyword placement)\n"
            "- Meta description\n"
            "- H1 and heading structure\n"
            "- Keyword density and placement\n"
            "- Internal linking\n"
            "- Image alt texts\n"
            "- Page speed considerations\n"
            "- Schema markup recommendations\n"
            "Provide specific rewrite recommendations for each issue found."
        )
        return self.execute_task(
            prompt,
            metadata={"type": "on_page_audit", "url": url},
        )

    def technical_seo_checklist(self, website: str) -> str:
        """Generate a technical SEO checklist and priorities."""
        prompt = (
            f"Create a technical SEO action plan for: {website}\n\n"
            "Cover these areas with specific recommendations:\n"
            "1. Core Web Vitals (LCP, FID, CLS)\n"
            "2. Mobile-first indexing\n"
            "3. Crawlability and robots.txt\n"
            "4. XML sitemap\n"
            "5. HTTPS and security\n"
            "6. Structured data / Schema markup\n"
            "7. Duplicate content and canonical tags\n"
            "8. Site architecture and URL structure\n"
            "Prioritise each item as: Critical / High / Medium / Low"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "technical_seo", "website": website},
        )

    def build_backlink_strategy(
        self, domain: str, industry: str, domain_authority: int = 0
    ) -> str:
        """Build a backlink acquisition strategy."""
        prompt = (
            f"Build a backlink acquisition strategy.\n\n"
            f"Domain: {domain}\n"
            f"Industry: {industry}\n"
            f"Current Domain Authority: {domain_authority}/100\n\n"
            "Provide:\n"
            "1. Top 5 link-building tactics suited to this domain\n"
            "2. Guest posting outreach template\n"
            "3. Types of sites to target (with examples)\n"
            "4. Broken link building approach\n"
            "5. Resource page link opportunities\n"
            "6. Digital PR angles for natural link acquisition\n"
            "7. Monthly backlink targets for 90-day plan"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "backlink_strategy", "domain": domain},
        )

    def analyse_competitors(self, domain: str, competitors: List[str]) -> str:
        """Perform SEO competitor analysis."""
        comp_list = ", ".join(competitors)
        prompt = (
            f"Perform an SEO competitor analysis.\n\n"
            f"Your domain: {domain}\n"
            f"Competitors: {comp_list}\n\n"
            "Analyse:\n"
            "1. Content gaps (topics they rank for, you don't)\n"
            "2. Backlink gap opportunities\n"
            "3. Keyword cannibalisation risks\n"
            "4. Their top-performing content types\n"
            "5. Your competitive advantages\n"
            "6. Quick wins to close the gap in 30 days"
        )
        return self.execute_task(
            prompt,
            metadata={"type": "competitor_analysis", "domain": domain},
        )
