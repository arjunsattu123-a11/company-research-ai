# Company Research AI Assistant

An AI-powered application that researches any company by name or website URL.
It crawls the company's website, gathers public information via search, uses
AI to summarize the business and identify pain points, finds competitors, and
generates a downloadable PDF report — all through a ChatGPT-style chat interface.

## Features

- **Dual input**: search by company name or paste a website URL directly.
- **Website crawler**: discovers About/Products/Services/Solutions/Contact/
  Pricing pages, skips login/cart/duplicate pages, and extracts clean text.
- **Search integration**: uses Serper.dev to find the official website and
  enrich research with public info and competitor leads.
- **AI analysis**: uses OpenRouter (model selectable in the UI) to produce a
  company summary, products/services list, pain points, and competitor
  suggestions.
- **PDF report generation**: one-click downloadable PDF with all research and
  competitor data.
- **Chat-style UI**: clean, responsive interface with progress indicators.
- **Bonus — Discord integration**: automatically sends the applicant details,
  company info, and generated PDF to a configured Discord channel.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Crawling**: httpx + BeautifulSoup
- **Search**: Serper.dev API
- **AI**: OpenRouter API
- **PDF**: ReportLab
- **Frontend**: Server-rendered HTML/CSS/vanilla JS (Jinja2 templates)

## Project Structure

```
company-research-ai/
├── main.py                    # FastAPI app & API routes
├── services/
│   ├── serper.py               # Serper.dev search + official-site lookup
│   ├── crawler.py               # Website crawler & text extraction
│   ├── ai_analysis.py           # OpenRouter integration
│   ├── pdf_generator.py         # PDF report builder
│   └── discord_notify.py        # Discord bonus integration
├── templates/
│   └── index.html               # Chat UI
├── static/
│   ├── style.css
│   └── app.js
├── reports/                     # Generated PDFs (temporary, gitignored)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd company-research-ai
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```
SERPER_API_KEY=your_serper_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
DISCORD_BOT_TOKEN=            # optional, can also be set from the UI
DISCORD_CHANNEL_ID=           # optional, can also be set from the UI
```

### 3. Run locally

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000`.

## Environment Variable Documentation

| Variable | Required | Description |
|---|---|---|
| `SERPER_API_KEY` | Yes | API key from [serper.dev](https://serper.dev) used for all web search calls. |
| `OPENROUTER_API_KEY` | Yes | API key from [openrouter.ai](https://openrouter.ai) used for AI analysis. |
| `DISCORD_BOT_TOKEN` | No (bonus) | Discord bot token; can alternatively be entered in the app's settings panel at runtime. |
| `DISCORD_CHANNEL_ID` | No (bonus) | Target Discord channel ID for report notifications. |
| `PORT` | No | Port to run the server on (defaults to 8000; most hosting platforms set this automatically). |

## Deployment

This app is deployed as a single unified service (FastAPI serves both the
API and the frontend). It can be deployed on any platform that supports a
Python web service, e.g. Render, Railway, or Fly.io:

1. Push the repository to GitHub.
2. Create a new Web Service on your chosen platform, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add the environment variables listed above in the platform's dashboard.

**Live deployment:** `<add your deployed URL here>`

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves the chat UI |
| `/api/research` | POST | Runs the full research pipeline for a company name/URL |
| `/api/discord-config` | POST | Saves Discord bot token + channel ID |
| `/api/download/{filename}` | GET | Downloads a generated PDF report |
| `/health` | GET | Health check |

## Notes

- No authentication, user accounts, or persistent database are used, per
  assignment requirements — generated PDFs are stored temporarily in `reports/`.
- The AI model can be changed per-request from the dropdown in the UI; any
  OpenRouter-supported chat model ID can be added to `AVAILABLE_MODELS` in
  `services/ai_analysis.py`.
- Discord integration is optional per request via a checkbox in the settings
  panel; it will only fire if a bot token and channel ID are configured.
