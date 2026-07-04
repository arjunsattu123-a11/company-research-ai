"""
Bonus feature: after a report is generated, send applicant + research
details plus the PDF to a configured Discord channel using the Discord
Bot HTTP API (no discord.py dependency needed - a plain REST call is
enough for a one-off file + message send).
"""

import httpx

DISCORD_API_BASE = "https://discord.com/api/v10"


async def send_report_to_discord(
    bot_token: str,
    channel_id: str,
    applicant_name: str,
    applicant_email: str,
    company_name: str,
    company_website: str,
    pdf_path: str,
) -> dict:
    if not bot_token or not channel_id:
        return {"sent": False, "reason": "Discord bot token or channel id not configured"}

    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}

    message_content = (
        f"**New Company Research Report Generated**\n"
        f"Applicant: {applicant_name} ({applicant_email})\n"
        f"Company: {company_name}\n"
        f"Website: {company_website}\n"
    )

    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.split("/")[-1], f, "application/pdf")}
        data = {"content": message_content}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, data=data, files=files)

    if resp.status_code in (200, 201):
        return {"sent": True}
    return {"sent": False, "reason": f"Discord API error: {resp.status_code} {resp.text}"}
