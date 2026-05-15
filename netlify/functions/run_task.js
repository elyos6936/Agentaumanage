// POST /api/run — execute a task on a specific agent via Claude API
// The frontend sends the full agent object so no file system access is needed.

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

function buildSystemPrompt(agent) {
  const skills = (agent.skills || []).join(", ");
  return [
    `You are ${agent.name}, a specialist ${agent.role} on a digital marketing team called the Silver Team.`,
    `Your core skills: ${skills}`,
    agent.description ? `Background: ${agent.description}` : "",
    agent.personality ? `Personality: ${agent.personality}` : "",
    "",
    "Always respond in the language used in the task. Be concise, actionable, and professional.",
    "When you provide recommendations, be specific and include measurable outcomes where possible.",
  ].filter(Boolean).join("\n");
}

async function callClaude(systemPrompt, userMessage, apiKey) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-6",
      max_tokens: 2048,
      system: systemPrompt,
      messages: [{ role: "user", content: userMessage }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API ${res.status}: ${err.slice(0, 200)}`);
  }

  const data = await res.json();
  return data.content[0].text;
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: CORS, body: "" };
  }
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers: CORS, body: JSON.stringify({ error: "Method not allowed" }) };
  }

  try {
    const body = JSON.parse(event.body || "{}");
    const { agent, task } = body;

    if (!agent || !task) {
      return {
        statusCode: 400,
        headers: CORS,
        body: JSON.stringify({ error: "agent and task are required" }),
      };
    }

    const apiKey = process.env.ANTHROPIC_API_KEY || "";
    if (!apiKey) {
      return {
        statusCode: 200,
        headers: CORS,
        body: JSON.stringify({
          agent_name: agent.name,
          role: agent.role,
          task,
          result: `⚠️ **Clé API manquante.** Ajoute \`ANTHROPIC_API_KEY\` dans Netlify → Site settings → Environment variables, puis redéploie.\n\nTâche reçue : *${task.slice(0, 200)}*`,
          success: false,
          response_time_ms: 0,
          timestamp: new Date().toISOString(),
        }),
      };
    }

    const start = Date.now();
    const result = await callClaude(buildSystemPrompt(agent), task, apiKey);
    const elapsed = Date.now() - start;

    return {
      statusCode: 200,
      headers: CORS,
      body: JSON.stringify({
        agent_id: agent.id,
        agent_name: agent.name,
        role: agent.role,
        task,
        result,
        success: true,
        response_time_ms: elapsed,
        timestamp: new Date().toISOString(),
      }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      headers: CORS,
      body: JSON.stringify({ error: err.message }),
    };
  }
};
