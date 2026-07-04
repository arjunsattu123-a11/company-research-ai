"""
Lightweight website crawler.

Goal: starting from a homepage URL, discover a handful of important pages
(about, products, services, solutions, contact, pricing), avoid duplicates
and junk pages (login/signup/cart/etc), and pull out clean visible text
for the AI step to analyze.
"""

import re
import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

IMPORTANT_KEYWORDS = [
    "about", "product", "service", "solution",
    "contact", "pricing", "plans",
]

SKIP_KEYWORDS = [
    "login", "signin", "sign-in", "signup", "sign-up", "register",
    "cart", "checkout", "account", "wp-admin", "privacy", "terms",
    "cookie", "career", "jobs",
]

MAX_PAGES = 6
TIMEOUT = 15


def _normalize_url(url: str) -> str:
    """Strip fragments/query params and trailing slash so we can dedupe cleanly."""
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return normalized.rstrip("/")


def _is_same_domain(base: str, target: str) -> bool:
    return urlparse(base).netloc.replace("www.", "") == urlparse(target).netloc.replace("www.", "")


def _looks_relevant(url: str) -> bool:
    lower = url.lower()
    if any(skip in lower for skip in SKIP_KEYWORDS):
        return False
    return True


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Drop noisy tags that rarely help the AI understand the business
    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:6000]  # keep prompt size manageable


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception:
        return None
    return None


async def crawl_website(homepage_url: str) -> dict:
    """
    Crawl a company's website starting at the homepage.
    Returns: {"pages": {url: extracted_text}, "visited": [urls]}
    """
    visited: set[str] = set()
    pages: dict[str, str] = {}

    headers = {"User-Agent": "Mozilla/5.0 (compatible; CompanyResearchBot/1.0)"}

    async with httpx.AsyncClient(headers=headers) as client:
        homepage_url = homepage_url.rstrip("/")
        html = await _fetch(client, homepage_url)
        if not html:
            return {"pages": pages, "visited": list(visited)}

        home_norm = _normalize_url(homepage_url)
        visited.add(home_norm)
        pages[home_norm] = _extract_text(html)

        # discover candidate internal links from homepage
        soup = BeautifulSoup(html, "lxml")
        candidates = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(homepage_url, href)
            if not _is_same_domain(homepage_url, full_url):
                continue
            if not _looks_relevant(full_url):
                continue

            norm = _normalize_url(full_url)
            if norm in visited:
                continue

            link_text = (a.get_text() or "").lower()
            haystack = f"{full_url.lower()} {link_text}"
            if any(kw in haystack for kw in IMPORTANT_KEYWORDS):
                candidates.append((norm, full_url))

        # dedupe candidates while preserving order
        seen = set()
        unique_candidates = []
        for norm, full_url in candidates:
            if norm not in seen:
                seen.add(norm)
                unique_candidates.append((norm, full_url))

        for norm, full_url in unique_candidates[:MAX_PAGES]:
            page_html = await _fetch(client, full_url)
            if page_html:
                visited.add(norm)
                pages[norm] = _extract_text(page_html)

    return {"pages": pages, "visited": list(visited)}


def combine_page_text(pages: dict[str, str]) -> str:
    """Merge crawled page texts into one block for the AI prompt, with light labels."""
    chunks = []
    for url, text in pages.items():
        chunks.append(f"[PAGE: {url}]\n{text}")
    combined = "\n\n".join(chunks)
    return combined[:15000]  # keep total prompt size sane
