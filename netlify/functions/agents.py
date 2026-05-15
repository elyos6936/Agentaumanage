"""GET /api/agents — returns all agent definitions from config/agents.json."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = ROOT / "config" / "agents.json"

AGENT_EMOJIS = {
    "linkedin": "💼",
    "facebook": "📘",
    "instagram": "📸",
    "tiktok": "🎵",
    "seo": "🔍",
    "content": "✍️",
    "analytics": "📊",
    "email": "📧",
}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Content-Type": "application/json",
}


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        agents = data.get("agents", [])
        api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

        for agent in agents:
            role_lower = agent.get("role", "").lower()
            for keyword, emoji in AGENT_EMOJIS.items():
                if keyword in role_lower:
                    agent["emoji"] = emoji
                    break
            else:
                agent["emoji"] = "🤖"

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "agents": agents,
                "api_key_configured": api_key_set,
                "total": len(agents),
            }),
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(exc)}),
        }
