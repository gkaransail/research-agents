import re
from agents.base import BaseAgent
from agents.registry import register_agent
from agents.searcher import SearchAgent
from agents.reader import ReaderAgent
from core.llm import llm


@register_agent("valuation")
class ValuationAgent(BaseAgent):
    name = "valuation"

    async def run(self, task: dict) -> dict:
        asset_name: str = task["asset_name"]
        asset_location: str = task["asset_location"]
        asset_type: str = task.get("asset_type", "real estate")

        await self.emit("searching", f"Researching market value for: {asset_name}")

        queries = [
            f"{asset_name} {asset_location} market value estimate {asset_type}",
            f"{asset_location} {asset_type} price trends comparable sales 2024 2025",
            f"{asset_type} {asset_location} rental yield income potential",
        ]

        searcher = SearchAgent(self.wf)
        search_output = await searcher.run({"queries": queries, "max_results": 6})
        search_results = search_output.get("results", [])

        urls = [r["url"] for r in search_results[:4]]
        reader = ReaderAgent(self.wf)
        read_output = await reader.run({"urls": urls, "max_urls": 4})
        pages = read_output.get("pages", [])

        await self.emit("analyzing", "Running valuation analysis...")

        source_text = _build_source_text(pages, search_results)

        analysis = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a real estate and financial asset valuation expert. "
                        "Analyze available information and produce a structured valuation assessment. "
                        "Be specific with numbers and ranges."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Asset: {asset_name}\nLocation: {asset_location}\nType: {asset_type}\n\n"
                        f"Sources:\n{source_text}\n\n"
                        "Cover:\n"
                        "1. Estimated current market value (USD range)\n"
                        "2. Key valuation drivers\n"
                        "3. Comparable transactions or market benchmarks\n"
                        "4. Income potential (rental yield, cap rate)\n"
                        "5. Valuation confidence level (High/Medium/Low) and rationale\n\n"
                        "End with: ESTIMATED_VALUE_USD: [single best-estimate integer, e.g. 3500000]"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        estimated_value_usd = _extract_value(analysis)

        await self.emit(
            "completed",
            f"Valuation complete — estimated value: ${estimated_value_usd:,}",
            {"estimated_value_usd": estimated_value_usd},
        )
        return {
            "analysis": analysis,
            "estimated_value_usd": estimated_value_usd,
            "sources": len(pages),
        }


def _extract_value(analysis: str) -> int:
    m = re.search(r"ESTIMATED_VALUE_USD:\s*\[?(\d[\d,]*)\]?", analysis)
    if m:
        return int(m.group(1).replace(",", ""))
    matches = re.findall(r"\$\s*(\d[\d,]+)", analysis)
    for m in matches:
        v = int(m.replace(",", ""))
        if v > 50_000:
            return v
    return 1_000_000


def _build_source_text(pages: list, search_results: list) -> str:
    parts = []
    for i, page in enumerate(pages, 1):
        parts.append(f"[Source {i}] {page.get('title', page['url'])}\n{page['content'][:1500]}\n")
    if not pages:
        for i, r in enumerate(search_results[:6], 1):
            parts.append(f"[Result {i}] {r.get('title', '')}\n{r.get('snippet', '')}\n")
    return "\n---\n".join(parts)
