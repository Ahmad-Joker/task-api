import OpenAI from "openai";

import type { Decision } from "@/lib/workflow-types";

function heuristicDecision(prompt: string, input: string): Decision {
  const text = `${prompt} ${input}`.toLowerCase();
  const yesSignals = [
    "support",
    "help",
    "error",
    "bug",
    "issue",
    "broken",
    "refund",
    "invoice",
    "login",
    "cannot",
    "can't",
  ];
  return yesSignals.some((signal) => text.includes(signal)) ? "YES" : "NO";
}

export async function askYesNo(prompt: string, input: string): Promise<Decision> {
  if (process.env.AI_STUB !== "0" || !process.env.OPENAI_API_KEY) {
    return heuristicDecision(prompt, input);
  }

  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const completion = await client.chat.completions.create({
    model: process.env.OPENAI_MODEL || "gpt-4o-mini",
    temperature: 0,
    messages: [
      {
        role: "system",
        content:
          "You are a workflow decision engine. Return exactly one token: YES or NO. Do not explain.",
      },
      {
        role: "user",
        content: JSON.stringify({ prompt, input }),
      },
    ],
  });

  const answer = completion.choices[0]?.message?.content?.trim().toUpperCase();
  return answer === "YES" ? "YES" : "NO";
}
