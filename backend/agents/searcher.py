import asyncio
from duckduckgo_search import DDGS
from agents.base import BaseAgent
from agents.registry import register_agent
from core.config import settings
from loguru import logger


@register_agent("searcher")
class SearchAgent(BaseAgent):
    name = "searcher"

    async def run(self, task: dict) -> dict:
        queries: list[str] = task.get("queries", [task.get("query", "")])
        max_results = task.get("max_results", settings.MAX_SEARCH_RESULTS)

        await self.emit("searching", f"Searching {len(queries)} queries via DuckDuckGo...")

        all_results: list[dict] = []
        seen_urls: set[str] = set()

        for query in queries:
            await self.emit("searching", f'Searching: "{query}"')
            try:
                results = await asyncio.to_thread(self._search, query, max_results)
                new = [r for r in results if r["url"] not in seen_urls]
                for r in new:
                    seen_urls.add(r["url"])
                all_results.extend(new)
                await self.emit(
                    "info",
                    f'Found {len(new)} results for "{query}"',
                    {"query": query, "count": len(new)},
                )
            except Exception as e:
                logger.error(f"Search error for '{query}': {e}")
                await self.emit("error", f"Search failed for '{query}': {str(e)}")

        await self.emit(
            "completed",
            f"Search complete — {len(all_results)} unique sources found",
            {"total_results": len(all_results)},
        )
        return {"results": all_results}

    def _search(self, query: str, max_results: int) -> list[dict]:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in raw
            if r.get("href")
        ]
