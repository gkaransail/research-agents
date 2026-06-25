import re
import json
from datetime import datetime, timezone
from pathlib import Path
from agents.base import BaseAgent
from agents.registry import register_agent
from core.llm import llm
from core.config import settings


@register_agent("dd_writer")
class DDWriterAgent(BaseAgent):
    name = "dd_writer"

    async def run(self, task: dict) -> dict:
        asset_name: str = task["asset_name"]
        asset_description: str = task.get("asset_description", "")
        asset_location: str = task["asset_location"]
        asset_type: str = task.get("asset_type", "real estate")
        valuation: dict = task["valuation"]
        regulatory: dict = task["regulatory"]
        risk: dict = task["risk"]

        await self.emit("writing", f"Synthesizing DD report for: {asset_name}")

        reg_points = {"GREEN": 40, "YELLOW": 25, "RED": 10}.get(regulatory["regulatory_status"], 25)
        risk_points = max(0, 20 - (risk["risk_score"] * 2))
        dd_score = 40 + reg_points + risk_points

        if dd_score >= 70:
            recommendation = "PROCEED"
        elif dd_score >= 50:
            recommendation = "PROCEED WITH CAUTION"
        else:
            recommendation = "DO NOT PROCEED"

        await self.emit("thinking", "Generating comprehensive report with Groq LLM...")

        report = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior due diligence analyst writing a professional investment report "
                        "for a real-world asset tokenization. Write in structured Markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a complete due diligence report for this asset:\n\n"
                        f"Asset Name: {asset_name}\n"
                        f"Description: {asset_description or asset_name}\n"
                        f"Location: {asset_location}\n"
                        f"Type: {asset_type}\n"
                        f"DD Score: {dd_score}/100\n"
                        f"Recommendation: {recommendation}\n\n"
                        f"=== VALUATION ANALYSIS ===\n{valuation['analysis']}\n\n"
                        f"=== REGULATORY ANALYSIS ===\n{regulatory['analysis']}\n\n"
                        f"=== RISK ANALYSIS ===\n{risk['analysis']}\n\n"
                        "Structure the report with these exact sections:\n"
                        "# Due Diligence Report: [Asset Name]\n"
                        "## Executive Summary\n"
                        "## Asset Overview\n"
                        "## Valuation Assessment\n"
                        "## Regulatory & Compliance Review\n"
                        "## Risk Assessment\n"
                        "## Tokenization Parameters\n"
                        "## Conclusion & Recommendation"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=4000,
        )

        token_symbol = _make_symbol(asset_name)
        estimated_value = valuation.get("estimated_value_usd", 1_000_000)

        params = {
            "token_name": f"{asset_name} Token",
            "token_symbol": token_symbol,
            "asset_name": asset_name,
            "asset_description": asset_description or asset_name,
            "asset_location": asset_location,
            "asset_value_usd_cents": estimated_value * 100,
            "total_tokens": 1_000_000,
            "initial_mint_pct": 10,
            "dd_score": dd_score,
            "risk_level": risk["risk_level"],
            "regulatory_status": regulatory["regulatory_status"],
            "recommendation": recommendation,
        }

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        header = (
            f"---\ntype: due-diligence\nasset: {asset_name}\n"
            f"location: {asset_location}\ndd_score: {dd_score}/100\n"
            f"recommendation: {recommendation}\ngenerated: {now}\n---\n\n"
        )
        params_block = f"\n<!-- TOKENIZATION_PARAMS\n{json.dumps(params, indent=2)}\n-->\n"
        full_report = header + report + params_block

        filepath = _save(asset_name, full_report)

        await self.emit(
            "completed",
            f"Report ready — Score: {dd_score}/100 — {recommendation}",
            {"file": str(filepath), "dd_score": dd_score, "recommendation": recommendation, "params": params},
        )
        return {
            "report": full_report,
            "output_file": str(filepath),
            "dd_score": dd_score,
            "recommendation": recommendation,
            "params": params,
        }


def _make_symbol(name: str) -> str:
    words = re.sub(r"[^\w\s]", "", name).split()
    symbol = "".join(w[0].upper() for w in words if w)[:5]
    return (symbol + "T") if len(symbol) < 3 else symbol


def _save(asset_name: str, content: str) -> Path:
    slug = re.sub(r"[^\w\s-]", "", asset_name.lower())
    slug = re.sub(r"\s+", "_", slug)[:50]
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path(settings.OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}_dd_{slug}.md"
    path.write_text(content, encoding="utf-8")
    return path
