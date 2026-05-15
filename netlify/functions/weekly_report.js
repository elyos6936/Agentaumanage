// POST /api/weekly — generate a team-wide weekly strategic report
// Body: { agents }

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
      max_tokens: 4000,
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
    const { agents = [] } = JSON.parse(event.body || "{}");

    const apiKey = process.env.ANTHROPIC_API_KEY || "";
    if (!apiKey) {
      return {
        statusCode: 200, headers: CORS,
        body: JSON.stringify({
          success: false,
          result: `⚠️ **Clé API manquante.** Ajoute \`ANTHROPIC_API_KEY\` dans Netlify → Site settings → Environment variables.`,
        }),
      };
    }

    const teamList = agents.map(a =>
      `- **${a.name}** (${a.role}): ${(a.skills || []).slice(0, 5).join(", ")}`
    ).join("\n");

    const now = new Date();
    const weekNum = Math.ceil((now - new Date(now.getFullYear(), 0, 1)) / 604800000);

    const system = `Tu es le Manager Général de la Silver Team, une agence de marketing digital d'élite.
Ton équipe : ${agents.length} spécialistes couvrant LinkedIn, Facebook, Instagram, TikTok, SEO, Content, Analytics et Email Marketing.
Tu es stratégique, orienté résultats et tu inspires ton équipe.`;

    const userMsg = `Génère le rapport hebdomadaire complet de l'équipe Silver Team pour la semaine ${weekNum} de ${now.getFullYear()}.

**Composition de l'équipe :**
${teamList}

Structure le rapport en Markdown avec ces sections :

# 📊 Rapport Hebdomadaire — Semaine ${weekNum} / ${now.getFullYear()}

## 🎯 Résumé Exécutif
Bilan stratégique de la semaine en 3-4 phrases percutantes.

## 🏆 Performances par Pôle
Pour chaque membre de l'équipe (tous les ${agents.length}), donne :
- Une action clé de la semaine
- Une métrique / résultat chiffré (réaliste)
- Un point d'attention

## 📈 Métriques Globales
Tableau récapitulatif avec KPIs clés pour l'ensemble de la présence digitale.

## 💡 Insights Marché
3-4 tendances importantes observées cette semaine dans le digital marketing.

## ⚡ Priorités Semaine Prochaine
Top 5 des actions prioritaires pour l'équipe, avec responsable assigné.

## 🔧 Points de blocage & solutions
Identifie 2-3 obstacles potentiels et propose des solutions concrètes.

## 🌟 Focus Amélioration Continue
1 initiative d'amélioration collective à mettre en place ce mois-ci.`;

    const start = Date.now();
    const result = await callClaude(system, userMsg, apiKey);
    const elapsed = Date.now() - start;

    return {
      statusCode: 200, headers: CORS,
      body: JSON.stringify({
        week: weekNum,
        year: now.getFullYear(),
        team_size: agents.length,
        result, success: true,
        response_time_ms: elapsed,
        timestamp: new Date().toISOString(),
      }),
    };
  } catch (err) {
    return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: err.message }) };
  }
};
