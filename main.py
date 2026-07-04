import os
import re
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from services.serper import find_official_website, search_company_info, search_competitors
from services.crawler import crawl_website, combine_page_text
from services.ai_analysis import analyze_company, AVAILABLE_MODELS
from services.pdf_generator import generate_pdf
from services.discord_notify import send_report_to_discord

load_dotenv()

app = FastAPI(title="Company Research AI Assistant")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Simple in-memory config for the Discord bonus feature (no DB required)
DISCORD_CONFIG = {
    "bot_token": os.getenv("DISCORD_BOT_TOKEN", ""),
    "channel_id": os.getenv("DISCORD_CHANNEL_ID", ""),
}

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class ResearchRequest(BaseModel):
    query: str                # company name OR website URL
    model: str = "openai/gpt-4o-mini"
    applicant_name: str | None = None
    applicant_email: str | None = None
    send_to_discord: bool = False


class DiscordConfigRequest(BaseModel):
    bot_token: str
    channel_id: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "models": AVAILABLE_MODELS}
    )


@app.post("/api/discord-config")
async def set_discord_config(payload: DiscordConfigRequest):
    DISCORD_CONFIG["bot_token"] = payload.bot_token
    DISCORD_CONFIG["channel_id"] = payload.channel_id
    return {"status": "saved"}


@app.post("/api/research")
async def research_company(payload: ResearchRequest):
    query = payload.query.strip()

    # Step 1: figure out the website
    if URL_PATTERN.match(query):
        website = query.rstrip("/")
        company_name_guess = website.split("//")[-1].split("/")[0].replace("www.", "").split(".")[0].title()
    else:
        company_name_guess = query
        website = await find_official_website(query)
        if not website:
            return JSONResponse(
                status_code=404,
                content={"error": f"Could not find an official website for '{query}'."},
            )

    # Step 2: crawl the website
    crawl_result = await crawl_website(website)
    crawled_text = combine_page_text(crawl_result["pages"])

    if not crawled_text.strip():
        return JSONResponse(
            status_code=422,
            content={"error": "Could not extract any content from that website. Try a different URL."},
        )

    # Step 3: extra public info + competitor search snippets
    info_results = await search_company_info(company_name_guess)
    competitor_results = await search_competitors(company_name_guess)

    search_snippets = "\n".join(
        f"- {r.get('title', '')}: {r.get('snippet', '')}"
        for r in (info_results + competitor_results)
        if r.get("snippet")
    )[:4000]

    # Step 4: AI analysis
    research = await analyze_company(
        company_name=company_name_guess,
        website=website,
        crawled_text=crawled_text,
        search_snippets=search_snippets,
        model=payload.model,
    )
    research["website"] = research.get("website") or website

    # Step 5: generate PDF
    pdf_path = generate_pdf(research)
    research["pdf_filename"] = os.path.basename(pdf_path)

    # Step 6 (bonus): notify Discord
    discord_result = {"sent": False, "reason": "not requested"}
    if payload.send_to_discord:
        discord_result = await send_report_to_discord(
            bot_token=DISCORD_CONFIG["bot_token"],
            channel_id=DISCORD_CONFIG["channel_id"],
            applicant_name=payload.applicant_name or "Unknown",
            applicant_email=payload.applicant_email or "unknown@example.com",
            company_name=research.get("company_name", company_name_guess),
            company_website=research.get("website", website),
            pdf_path=pdf_path,
        )

    return {
        "research": research,
        "pages_crawled": crawl_result["visited"],
        "discord": discord_result,
    }


@app.get("/api/download/{filename}")
async def download_pdf(filename: str):
    filepath = os.path.join("reports", filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "Report not found"})
    return FileResponse(filepath, media_type="application/pdf", filename=filename)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
