"""POST /api/manager — General Manager routes task to relevant agents."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = ROOT / "config" / "agents.json"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json",
}

MODEL = "claude-sonnet-4-6"

ROUTING_KEYWORDS = {
    "linkedin": ["linkedin", "b2b", "professional", "réseau pro", "connexion"],
    "facebook": ["facebook", "meta", "fb", "communauté", "community"],
    "instagram": ["instagram", "reels", "story", "stories", "visuel", "visual"],
    "tiktok": ["tiktok", "viral", "short video", "courte vidéo", "trending"],
    "seo": ["seo", "référencement", "search", "google", "keyword", "mot-clé"],
    "content": ["blog", "article", "contenu", "content", "copywriting", "rédac"],
    "analytics": ["analytics", "statistiques", "kpi", "data", "rapport", "report"],
    "email": ["email", "mail", "newsletter", "campagne", "automation", "drip"],
}


def _load_agents() -> list[dict]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("agents", [])


def _route_task(task: str, agents: list[dict]) -> list[dict]:
    task_lower = task.lower()
    matched = []
    for agent in agents:
        role_lower = agent["role"].lower()
        for role_key, keywords in ROUTING_KEYWORDS.items():
            if role_key in role_lower:
                if any(kw in task_lower for kw in keywords):
                    matched.append(agent)
                    break
    # If no keyword match, pick top 3 most relevant by role order
    if not matched:
        matched = agents[:3]
    return matched[:4]  # max 4 agents per manager task


def _call_claude(system: str, user_msg: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return (
            "⚠️ **No API key configured.** Set ANTHROPIC_API_KEY in Netlify "
            "environment variables to enable the Silver Team to work."
        )
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text
    except Exception as exc:
        return f"❌ API error: {exc}"


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}

    if event.get("httpMethod") != "POST":
        return {"statusCode": 405, "headers": CORS_HEADERS, "body": json.dumps({"error": "Method not allowed"})}

    try:
        body = json.loads(event.get("body") or "{}")
        task = body.get("task", "").strip()
        if not task:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "task is required"}),
            }

        agents = _load_agents()
        routed_agents = _route_task(task, agents)

        # Build manager system prompt
        team_summary = "\n".join(
            f"- {a['name']} ({a['role']}): {', '.join(a['skills'][:4])}"
            for a in agents
        )
        manager_system = (
            "You are the General Manager of the Silver Team, an elite digital marketing agency. "
            "Your team members are:\n\n"
            f"{team_summary}\n\n"
            "When given a task, you:\n"
            "1. Analyse the request and identify which team members are most relevant\n"
            "2. Provide a strategic breakdown of how to approach it\n"
            "3. Delegate specific sub-tasks to team members with clear instructions\n"
            "4. Give a consolidated strategic recommendation\n\n"
            "Be decisive, strategic, and actionable. Respond in the same language as the task."
        )

        routed_names = [a["name"] for a in routed_agents]
        delegation_prompt = (
            f"Task to manage: {task}\n\n"
            f"Relevant team members identified: {', '.join(routed_names)}\n\n"
            "Provide:\n"
            "1. **Strategic overview** (2-3 sentences)\n"
            "2. **Delegation plan** — specific instructions for each relevant team member\n"
            "3. **Success metrics** — how to measure the outcome\n"
            "4. **Timeline** — realistic execution timeline"
        )

        start = time.monotonic()
        result = _call_claude(manager_system, delegation_prompt)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "task": task,
                "routed_to": routed_names,
                "result": result,
                "response_time_ms": elapsed_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(exc)}),
        }
