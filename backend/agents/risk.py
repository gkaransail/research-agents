import re
from agents.base import BaseAgent
from agents.registry import register_agent
from agents.searcher import SearchAgent
from agents.reader import ReaderAgent
from core.llm import llm


@register_agent("risk")
class RiskAgent(BaseAgent):
    name = "risk"

    async def run(self, task: dict) -> dict:
        asset_name: str = task["asset_name"]
        asset_location: str = task["asset_location"]
        asset_type: str = task.get("asset_type", "real estate")

        await self.emit("searching", f"Assessing risk profile for: {asset_name}")

        queries = [
            f"{asset_location} {asset_type} market risk outlook 2025",
            f"RWA tokenization risks liquidity secondary market challenges",
            f"{asset_location} economic stability real estate market conditions",
        ]

        searcher = SearchAgent(self.wf)
        search_output = await searcher.run({"queries": queries, "max_results": 6})
        search_results = search_output.get("results", [])

        urls = [r["url"] for r in search_results[:4]]
        reader = ReaderAgent(self.wf)
        read_output = await reader.run({"urls": urls, "max_urls": 4})
        pages = read_output.get("pages", [])

        await self.emit("analyzing", "Computing risk profile...")

        source_text = _build_source_text(pages, search_results)

        analysis = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial risk analyst specializing in alternative assets and tokenized securities. "
                        "Provide a thorough risk assessment. Quantify risks where possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Asset: {asset_name}\nLocation: {asset_location}\nType: {asset_type}\n\n"
                        f"Sources:\n{source_text}\n\n"
                        "Cover:\n"
                        "1. Market risk (price volatility, demand trends)\n"
                        "2. Liquidity risk (ease of exit, secondary market depth)\n"
                        "3. Operational risk (management, maintenance)\n"
                        "4. Macroeconomic risk (rates, currency, inflation)\n"
                        "5. Tokenization-specific risks (smart contract, custody, regulatory change)\n"
                        "6. Overall risk score (1=very low risk, 10=very high risk)\n\n"
                        "End with: RISK_SCORE: [integer 1-10] RISK_LEVEL: [Low|Medium|High]"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        score, level = 5, "Medium"
        m = re.search(r"RISK_SCORE:\s*\[?(\d+)\]?", analysis)
        if m:
            score = min(10, max(1, int(m.group(1))))
        m2 = re.search(r"RISK_LEVEL:\s*\[?(Low|Medium|High)\]?", analysis)
        if m2:
            level = m2.group(1)

        await self.emit(
            "completed",
            f"Risk assessment complete — {score}/10 ({level})",
            {"risk_score": score, "risk_level": level},
        )
        return {
            "analysis": analysis,
            "risk_score": score,
            "risk_level": level,
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
