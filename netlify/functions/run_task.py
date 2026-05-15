"""POST /api/run — run a task on a specific agent via Claude API."""

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


def _load_agent(agent_id: str) -> dict | None:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for agent in data.get("agents", []):
        if agent["id"] == agent_id or agent["name"].lower() == agent_id.lower():
            return agent
    return None


def _build_system_prompt(agent: dict) -> str:
    skills = ", ".join(agent.get("skills", []))
    description = agent.get("description", "")
    personality = agent.get("personality", "")
    return (
        f"You are {agent['name']}, a specialist {agent['role']} on a digital marketing "
        f"team called the Silver Team.\n\n"
        f"Your core skills: {skills}\n\n"
        f"{'Background: ' + description if description else ''}\n"
        f"{'Personality: ' + personality if personality else ''}\n\n"
        "Always respond in the language used in the task. Be concise, actionable, "
        "and professional. When you provide recommendations, be specific and include "
        "measurable outcomes where possible."
    )


def _call_claude(agent: dict, task: str) -> tuple[str, bool]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return (
            f"⚠️ **No API key configured.** Set ANTHROPIC_API_KEY in your "
            f"Netlify environment variables to enable {agent['name']} to work.\n\n"
            f"Task received: *{task[:200]}*",
            False,
        )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=_build_system_prompt(agent),
            messages=[{"role": "user", "content": task}],
        )
        return response.content[0].text, True
    except Exception as exc:
        return f"❌ API error: {exc}", False


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS_HEADERS, "body": ""}

    if event.get("httpMethod") != "POST":
        return {"statusCode": 405, "headers": CORS_HEADERS, "body": json.dumps({"error": "Method not allowed"})}

    try:
        body = json.loads(event.get("body") or "{}")
        agent_id = body.get("agent_id", "").strip()
        task = body.get("task", "").strip()

        if not agent_id or not task:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "agent_id and task are required"}),
            }

        agent = _load_agent(agent_id)
        if agent is None:
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Agent '{agent_id}' not found"}),
            }

        start = time.monotonic()
        result, success = _call_claude(agent, task)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "role": agent["role"],
                "task": task,
                "result": result,
                "success": success,
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
