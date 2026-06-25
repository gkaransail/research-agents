import re
from agents.base import BaseAgent
from agents.registry import register_agent
from agents.searcher import SearchAgent
from agents.reader import ReaderAgent
from core.llm import llm


@register_agent("regulatory")
class RegulatoryAgent(BaseAgent):
    name = "regulatory"

    async def run(self, task: dict) -> dict:
        asset_name: str = task["asset_name"]
        asset_location: str = task["asset_location"]
        asset_type: str = task.get("asset_type", "real estate")

        await self.emit("searching", f"Checking regulatory status for: {asset_name}")

        queries = [
            f"{asset_location} {asset_type} zoning regulations ownership restrictions",
            f"tokenizing {asset_type} {asset_location} legal regulatory requirements securities",
            f"{asset_name} {asset_location} property rights title encumbrances",
        ]

        searcher = SearchAgent(self.wf)
        search_output = await searcher.run({"queries": queries, "max_results": 6})
        search_results = search_output.get("results", [])

        urls = [r["url"] for r in search_results[:4]]
        reader = ReaderAgent(self.wf)
        read_output = await reader.run({"urls": urls, "max_urls": 4})
        pages = read_output.get("pages", [])

        await self.emit("analyzing", "Assessing regulatory compliance...")

        source_text = _build_source_text(pages, search_results)

        analysis = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a regulatory compliance expert specializing in real-world asset tokenization. "
                        "Assess the regulatory landscape for the given asset. Flag any red flags clearly."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Asset: {asset_name}\nLocation: {asset_location}\nType: {asset_type}\n\n"
                        f"Sources:\n{source_text}\n\n"
                        "Cover:\n"
                        "1. Ownership and title clarity\n"
                        "2. Zoning and permitted use compliance\n"
                        "3. Tokenization regulatory framework in this jurisdiction\n"
                        "4. Known encumbrances, liens, or legal disputes\n"
                        "5. KYC/AML and securities law requirements for token issuance\n"
                        "6. Regulatory risk rating with justification\n\n"
                        "End with: REGULATORY_STATUS: [GREEN|YELLOW|RED]"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        status = "YELLOW"
        m = re.search(r"REGULATORY_STATUS:\s*\[?(GREEN|YELLOW|RED)\]?", analysis)
        if m:
            status = m.group(1)

        await self.emit(
            "completed",
            f"Regulatory check complete — status: {status}",
            {"regulatory_status": status},
        )
        return {
            "analysis": analysis,
            "regulatory_status": status,
            "sources": len(pages),
        }


def _build_source_text(pages: list, search_results: list) -> str:
    parts = []
    for i, page in enumerate(pages, 1):
        parts.append(f"[Source {i}] {page.get('title', page['url'])}\n{page['content'][:1500]}\n")
    if not pages:
        for i, r in enumerate(search_results[:6], 1):
            parts.append(f"[Result {i}] {r.get('title', '')}\n{r.get('snippet', '')}\n")
    return "\n---\n".join(parts)
