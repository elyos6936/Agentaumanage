// POST /api/manager — General Manager routes task to relevant agents
// Frontend sends { task, agents } — no file system access needed.

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

const ROUTING_KEYWORDS = {
  linkedin:  ["linkedin", "b2b", "professionnel", "professional", "réseau pro"],
  facebook:  ["facebook", "meta", "fb", "communauté", "community"],
  instagram: ["instagram", "reels", "story", "stories", "visuel", "visual"],
  tiktok:    ["tiktok", "viral", "short video", "courte vidéo", "trending"],
  seo:       ["seo", "référencement", "search", "google", "keyword", "mot-clé"],
  content:   ["blog", "article", "contenu", "content", "copywriting", "rédac"],
  analytics: ["analytics", "statistiques", "kpi", "data", "rapport", "report"],
  email:     ["email", "mail", "newsletter", "campagne", "automation"],
};

function routeTask(task, agents) {
  const lower = task.toLowerCase();
  const matched = agents.filter((a) => {
    const roleKey = a.role.toLowerCase();
    return Object.entries(ROUTING_KEYWORDS).some(
      ([key, words]) => roleKey.includes(key) && words.some((w) => lower.includes(w))
    );
  });
  return matched.length ? matched.slice(0, 4) : agents.slice(0, 3);
}

async function callClaude(system, userMsg, apiKey) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-6",
      max_tokens: 3000,
      system,
      messages: [{ role: "user", content: userMsg }],
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
    const { task, agents = [] } = body;

    if (!task) {
      return { statusCode: 400, headers: CORS, body: JSON.stringify({ error: "task is required" }) };
    }

    const apiKey = process.env.ANTHROPIC_API_KEY || "";
    if (!apiKey) {
      return {
        statusCode: 200,
        headers: CORS,
        body: JSON.stringify({
          task,
          routed_to: [],
          result: `⚠️ **Clé API manquante.** Ajoute \`ANTHROPIC_API_KEY\` dans Netlify → Site settings → Environment variables, puis redéploie.`,
          success: false,
          response_time_ms: 0,
          timestamp: new Date().toISOString(),
        }),
      };
    }

    const routed = routeTask(task, agents);
    const routedNames = routed.map((a) => a.name);

    const teamSummary = agents
      .map((a) => `- ${a.name} (${a.role}): ${(a.skills || []).slice(0, 4).join(", ")}`)
      .join("\n");

    const system = [
      "You are the General Manager of the Silver Team, an elite digital marketing agency.",
      "Your team members are:\n" + teamSummary,
      "",
      "When given a task, you:",
      "1. Analyse the request and identify which team members are most relevant",
      "2. Provide a strategic breakdown of how to approach it",
      "3. Delegate specific sub-tasks to team members with clear instructions",
      "4. Give a consolidated strategic recommendation",
      "",
      "Be decisive, strategic, and actionable. Respond in the same language as the task.",
    ].join("\n");

    const userMsg = [
      `Task to manage: ${task}`,
      `Relevant team members identified: ${routedNames.join(", ")}`,
      "",
      "Provide:",
      "1. **Strategic overview** (2-3 sentences)",
      "2. **Delegation plan** — specific instructions for each relevant team member",
      "3. **Success metrics** — how to measure the outcome",
      "4. **Timeline** — realistic execution timeline",
    ].join("\n");

    const start = Date.now();
    const result = await callClaude(system, userMsg, apiKey);
    const elapsed = Date.now() - start;

    return {
      statusCode: 200,
      headers: CORS,
      body: JSON.stringify({
        task,
        routed_to: routedNames,
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
