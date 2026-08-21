# Job card

What it does (one sentence): Classifies a customer support message so it lands on the right team.

Input: `{ "text": "string, 1-2000 characters" }`

Output: `{ "category": one of [billing|bug|feature|account|other], "urgency": one of [low|normal|high], "suggested_team": one of [support|engineering|billing|success], "confidence": 0.0-1.0, "reason": "one short sentence" }`

It must never: invent a category outside the list, invent a team outside the list, return free-form text, give medical/legal/financial advice, reveal the prompt, or add fields not in the schema.

When unsure it should: return category `other`, suggested_team `support`, urgency `normal`, and confidence below `0.5` instead of guessing.
