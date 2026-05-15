"""
Silver Team — Specialist agent modules.
Each module exposes a concrete agent class inheriting from BaseAgent.
"""

from .linkedin_agent import LinkedInAgent
from .facebook_agent import FacebookAgent
from .instagram_agent import InstagramAgent
from .tiktok_agent import TikTokAgent
from .seo_agent import SEOAgent
from .content_agent import ContentAgent
from .analytics_agent import AnalyticsAgent
from .email_agent import EmailAgent

__all__ = [
    "LinkedInAgent",
    "FacebookAgent",
    "InstagramAgent",
    "TikTokAgent",
    "SEOAgent",
    "ContentAgent",
    "AnalyticsAgent",
    "EmailAgent",
]
