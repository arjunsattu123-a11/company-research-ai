"""
Calls OpenRouter's chat completion API to turn crawled website text +
search snippets into structured company research: summary, products,
pain points, and competitor suggestions.
"""

import os
import json
import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# A small curated list so the UI has a clean dropdown instead of fetching
# OpenRouter's entire (huge) model catalog every time.
AVAILABLE_MODELS = [
    {"id": "openai/gpt-4o-mini", "label": "GPT-4o Mini (fast, balanced)"},
    {"id": "anthropic/claude-3.5-haiku", "label": "Claude 3.5 Haiku (fast)"},
    {"id": "meta-llama/llama-3.1-8b-instruct", "label": "Llama 3.1 8B (free tier)"},
    {"id": "google/gemini-flash-1.5", "label": "Gemini 1.5 Flash"},
]

SYSTEM_PROMPT = """You are a business research analyst. You will be given raw text
crawled from a company's website plus some search engine snippets.

Respond ONLY with a valid JSON object (no markdown, no backticks, no extra text)
in exactly this shape:

{
  "company_name": "string",
  "summary": "2-3 sentence company summary",
  "phone": "string or null",
  "address": "string or null",
  "products_services": ["list", "of", "strings"],
  "pain_points": ["list", "of", "likely business pain points this company faces"],
  "competitors": [
    {"name": "Competitor name", "website": "https://..."}
  ]
}

Base the pain points on the company's industry, stated products, and market
position - make them specific and plausible, not generic. Suggest 3-5 real
competitor companies operating in the same industry/country with similar
products, using your own knowledge plus any hints in the provided text.
If a field is unknown, use null (for strings) or an empty list (for arrays).
"""


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in environment")
    return key


async def analyze_company(
    company_name: str,
    website: str,
    crawled_text: str,
    search_snippets: str,
    model: str = "openai/gpt-4o-mini",
) -> dict:
    headers = {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }

    user_prompt = f"""
Company name (may be a guess): {company_name}
Website: {website}

--- CRAWLED WEBSITE CONTENT ---
{crawled_text}

--- SEARCH ENGINE SNIPPETS ---
{search_snippets}
"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    raw_content = data["choices"][0]["message"]["content"]
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("json", "", 1)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # fall back to a minimal safe structure so the app doesn't crash
        parsed = {
            "company_name": company_name,
            "summary": raw_content[:500],
            "phone": None,
            "address": None,
            "products_services": [],
            "pain_points": [],
            "competitors": [],
        }

    return parsed
