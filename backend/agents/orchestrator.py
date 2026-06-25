import json
from agents.base import BaseAgent
from agents.registry import register_agent
from agents.searcher import SearchAgent
from agents.reader import ReaderAgent
from agents.analyzer import AnalyzerAgent
from agents.writer import WriterAgent
from core.llm import llm


@register_agent("orchestrator")
class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    async def run(self, task: dict) -> dict:
        query: str = task["query"]
        depth: int = task.get("depth", 2)
        max_urls = {1: 3, 2: 5, 3: 8}.get(depth, 5)

        await self.emit("planning", f'Planning research for: "{query}"')

        queries = await self._plan_queries(query, depth)
        await self.emit("planning", f"Generated {len(queries)} search queries", {"queries": queries})

        search_output = await SearchAgent(self.wf).run({"queries": queries, "max_results": 6})
        search_results = search_output.get("results", [])

        if not search_results:
            await self.emit("error", "No search results found. Check connectivity.")
            return {"error": "no_results"}

        urls = [r["url"] for r in search_results[:max_urls]]
        read_output = await ReaderAgent(self.wf).run({"urls": urls, "max_urls": max_urls})
        pages = read_output.get("pages", [])

        analysis_output = await AnalyzerAgent(self.wf).run({
            "query": query,
            "pages": pages,
            "search_results": search_results,
        })

        write_output = await WriterAgent(self.wf).run({
            "query": query,
            "analysis": analysis_output.get("analysis", ""),
            "pages": pages,
            "search_results": search_results,
        })

        await self.emit("completed", "Research complete! Report saved.", {"output_file": write_output.get("output_file")})
        return write_output

    async def _plan_queries(self, query: str, depth: int) -> list[str]:
        n = {1: 2, 2: 3, 3: 5}.get(depth, 3)
        try:
            resp = await llm.fast_chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a research strategist. Generate targeted web search queries. "
                            f"Return exactly {n} queries as a JSON array of strings. No explanation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Generate {n} diverse search queries to thoroughly research: {query}",
                    },
                ],
                temperature=0.5,
                max_tokens=256,
            )
            start = resp.find("[")
            end = resp.rfind("]") + 1
            if start >= 0 and end > start:
                queries = json.loads(resp[start:end])
                if isinstance(queries, list) and queries:
                    return [str(q) for q in queries[:n]]
        except Exception:
            pass
        return [query, f"{query} overview", f"{query} analysis"][:n]
