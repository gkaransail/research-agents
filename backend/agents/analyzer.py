from agents.base import BaseAgent
from agents.registry import register_agent
from core.llm import llm


@register_agent("analyzer")
class AnalyzerAgent(BaseAgent):
    name = "analyzer"

    async def run(self, task: dict) -> dict:
        query: str = task["query"]
        pages: list[dict] = task.get("pages", [])
        search_results: list[dict] = task.get("search_results", [])

        await self.emit("analyzing", f"Synthesizing {len(pages)} sources for: {query}")

        source_text = self._build_source_text(pages, search_results)

        await self.emit("thinking", "Running analysis with Groq LLM...")

        analysis = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert research analyst. Given sources, produce a structured analysis. "
                        "Be factual, cite specific details from sources, and identify key themes and insights."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Research query: {query}\n\n"
                        f"Sources:\n{source_text}\n\n"
                        "Provide a thorough analysis covering:\n"
                        "1. Key findings\n"
                        "2. Important facts and data points\n"
                        "3. Trends and patterns\n"
                        "4. Conflicting information or uncertainties\n"
                        "5. Gaps in the available information"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        await self.emit(
            "completed",
            "Analysis complete",
            {"analysis_length": len(analysis)},
        )
        return {"analysis": analysis, "sources_used": len(pages)}

    def _build_source_text(self, pages: list[dict], search_results: list[dict]) -> str:
        parts = []
        for i, page in enumerate(pages, 1):
            parts.append(f"[Source {i}] {page.get('title', page['url'])}\nURL: {page['url']}\n{page['content']}\n")

        if not pages and search_results:
            for i, r in enumerate(search_results[:10], 1):
                parts.append(f"[Result {i}] {r.get('title', '')}\nURL: {r['url']}\n{r.get('snippet', '')}\n")

        return "\n---\n".join(parts)
