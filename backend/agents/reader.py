import asyncio
import httpx
from agents.base import BaseAgent
from agents.registry import register_agent
from core.config import settings
from loguru import logger

JINA_BASE = "https://r.jina.ai/"
MAX_CONTENT_CHARS = 6000  # per page, to stay within Groq context limits


@register_agent("reader")
class ReaderAgent(BaseAgent):
    name = "reader"

    async def run(self, task: dict) -> dict:
        urls: list[str] = task.get("urls", [])
        max_urls = task.get("max_urls", settings.MAX_READ_URLS)
        urls = urls[:max_urls]

        await self.emit("reading", f"Reading {len(urls)} pages via Jina AI Reader...")

        results = await asyncio.gather(*[self._read(url) for url in urls], return_exceptions=True)

        pages = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                await self.emit("error", f"Failed to read {url}: {str(result)}")
            else:
                pages.append(result)
                await self.emit(
                    "reading",
                    f"Read: {result['title'] or url} ({len(result['content'])} chars)",
                    {"url": url, "title": result["title"]},
                )

        await self.emit(
            "completed",
            f"Read {len(pages)}/{len(urls)} pages successfully",
            {"pages_read": len(pages)},
        )
        return {"pages": pages}

    async def _read(self, url: str) -> dict:
        jina_url = f"{JINA_BASE}{url}"
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(
                jina_url,
                headers={"Accept": "text/plain", "X-Return-Format": "text"},
            )
            resp.raise_for_status()
            content = resp.text[:MAX_CONTENT_CHARS]

        title = self._extract_title(content)
        return {"url": url, "title": title, "content": content}

    def _extract_title(self, text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Title:"):
                return line.replace("Title:", "").strip()
            if line and not line.startswith("http"):
                return line[:100]
        return ""
