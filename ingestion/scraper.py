import asyncio
import random
from playwright.async_api import async_playwright

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

EXTRA_WAIT_DOMAINS = ["doordash.com", "ubereats.com"]


class ScraperError(Exception):
    pass


async def fetch_url(url: str) -> str:
    if url.lower().endswith(".pdf"):
        raise ScraperError("PDF URLs must be uploaded directly — use the photo upload endpoint.")

    user_agent = random.choice(USER_AGENTS)
    extra_wait = any(domain in url for domain in EXTRA_WAIT_DOMAINS)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            if extra_wait:
                await asyncio.sleep(5)
            html = await page.content()
            return html
        finally:
            await browser.close()
