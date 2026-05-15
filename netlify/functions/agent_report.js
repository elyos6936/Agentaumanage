// POST /api/report — generate a capability & performance report for one agent
// Body: { agent }

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

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
  return (await res.json()).content[0].text;
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: CORS, body: "" };
  if (event.httpMethod !== "POST") return { statusCode: 405, headers: CORS, body: JSON.stringify({ error: "Method not allowed" }) };

  try {
    const { agent, mode = "report" } = JSON.parse(event.body || "{}");
    if (!agent) return { statusCode: 400, headers: CORS, body: JSON.stringify({ error: "agent is required" }) };

    const apiKey = process.env.ANTHROPIC_API_KEY || "";
    if (!apiKey) {
      return {
        statusCode: 200, headers: CORS,
        body: JSON.stringify({
          agent_name: agent.name, mode, success: false,
          result: `⚠️ **Clé API manquante.** Ajoute \`ANTHROPIC_API_KEY\` dans Netlify → Site settings → Environment variables.`,
        }),
      };
    }

    const skills = (agent.skills || []).join(", ");
    const system = `You are ${agent.name}, a specialist ${agent.role} on the Silver Team digital marketing agency.\nSkills: ${skills}\n${agent.description ? "Background: " + agent.description : ""}`;

    let userMsg, reportType;

    if (mode === "evaluate") {
      reportType = "Auto-évaluation";
      userMsg = `Réalise une auto-évaluation professionnelle de ton rôle de ${agent.role}. Structure ta réponse en Markdown avec ces sections exactes :

## Forces
Liste 4-5 compétences clés où tu excelles avec des exemples concrets.

## Axes d'amélioration
Liste 3-4 domaines où tu peux progresser, sois honnête et constructif.

## Plan d'amélioration 30/60/90 jours
- **30 jours :** Actions immédiates
- **60 jours :** Objectifs intermédiaires
- **90 jours :** Vision et résultats attendus

## KPIs de suivi
Liste 5 indicateurs mesurables pour évaluer ta progression.

## Note globale
Attribue-toi une note /10 avec une justification en 2-3 phrases.`;
    } else {
      reportType = "Rapport de performance";
      userMsg = `Génère un rapport de performance hebdomadaire complet pour ton rôle de ${agent.role}. Structure en Markdown :

## Résumé exécutif
2-3 phrases sur ta contribution cette semaine.

## Réalisations clés
Liste 5-7 actions concrètes que tu aurais accomplies cette semaine dans ton rôle.

## Métriques et KPIs
Propose un tableau de métriques typiques pour ton poste avec des valeurs cibles réalistes.

## Insights et recommandations
3-4 recommandations stratégiques basées sur les tendances actuelles de ton domaine.

## Plan de la semaine prochaine
5 priorités claires pour la semaine suivante.

## Ressources nécessaires
Ce dont tu aurais besoin pour performer au maximum.`;
    }

    const start = Date.now();
    const result = await callClaude(system, userMsg, apiKey);
    const elapsed = Date.now() - start;

    return {
      statusCode: 200, headers: CORS,
      body: JSON.stringify({
        agent_name: agent.name, role: agent.role,
        mode, report_type: reportType,
        result, success: true,
        response_time_ms: elapsed,
        timestamp: new Date().toISOString(),
      }),
    };
  } catch (err) {
    return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: err.message }) };
  }
};
