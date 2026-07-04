"""
Handles all calls to Serper.dev for web search.
Used to:
 - find a company's official website from its name
 - gather extra public info about a company
 - help discover competitors
"""

import os
import httpx

SERPER_URL = "https://google.serper.dev/search"


def _get_api_key() -> str:
    key = os.getenv("SERPER_API_KEY")
    if not key:
        raise RuntimeError("SERPER_API_KEY is not set in environment")
    return key


async def serper_search(query: str, num_results: int = 10) -> dict:
    """Run a raw search query against Serper.dev and return the JSON response."""
    headers = {
        "X-API-KEY": _get_api_key(),
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num_results}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(SERPER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def find_official_website(company_name: str) -> str | None:
    """
    Given a company name, try to find its most likely official website.
    Simple heuristic: take the first organic result whose link doesn't
    belong to a known non-official domain (wikipedia, linkedin, etc).
    """
    data = await serper_search(f"{company_name} official website")
    blocked_domains = [
        "wikipedia.org", "linkedin.com", "facebook.com", "twitter.com",
        "x.com", "instagram.com", "youtube.com", "crunchbase.com",
        "glassdoor.com", "indeed.com",
    ]

    for result in data.get("organic", []):
        link = result.get("link", "")
        if link and not any(bad in link for bad in blocked_domains):
            return link

    return None


async def search_company_info(company_name: str) -> list[dict]:
    """General search to enrich company info (phone, address, news, etc)."""
    data = await serper_search(f"{company_name} contact address phone")
    return data.get("organic", [])


async def search_competitors(company_name: str, industry_hint: str = "") -> list[dict]:
    """Search for competitor companies."""
    query = f"{company_name} top competitors {industry_hint}".strip()
    data = await serper_search(query)
    return data.get("organic", [])
