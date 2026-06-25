import re
from datetime import datetime, timezone
from pathlib import Path
from agents.base import BaseAgent
from agents.registry import register_agent
from core.llm import llm
from core.config import settings


@register_agent("writer")
class WriterAgent(BaseAgent):
    name = "writer"

    async def run(self, task: dict) -> dict:
        query: str = task["query"]
        analysis: str = task["analysis"]
        pages: list[dict] = task.get("pages", [])
        search_results: list[dict] = task.get("search_results", [])

        await self.emit("writing", f"Writing research report for: {query}")

        sources_section = self._build_sources_section(pages, search_results)

        report = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert research writer. Write a comprehensive, well-structured research report "
                        "in Markdown format. Use headers, bullet points, tables where appropriate. "
                        "Be clear, thorough, and professional."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a complete research report for the query: **{query}**\n\n"
                        f"Based on this analysis:\n{analysis}\n\n"
                        "Structure the report with:\n"
                        "# Executive Summary\n"
                        "# Key Findings\n"
                        "# Detailed Analysis\n"
                        "# Data & Statistics\n"
                        "# Conclusions\n"
                        "# Recommendations\n\n"
                        "Make it professional, detailed, and actionable."
                    ),
                },
            ],
            temperature=0.4,
            max_tokens=4000,
        )

        report_with_meta = self._add_metadata(report, query, pages, search_results, sources_section)
        filepath = self._save(query, report_with_meta)

        await self.emit("completed", f"Report saved → {filepath}", {"file": str(filepath), "length": len(report_with_meta)})
        return {"report": report_with_meta, "output_file": str(filepath)}

    def _add_metadata(self, report: str, query: str, pages: list, search_results: list, sources: str) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        header = (
            f"---\nquery: {query}\ngenerated: {now}\n"
            f"sources: {len(pages)} pages read, {len(search_results)} search results\n"
            f"model: {settings.PRIMARY_MODEL}\n---\n\n"
        )
        return header + report + "\n\n" + sources

    def _build_sources_section(self, pages: list[dict], search_results: list[dict]) -> str:
        lines = ["\n## Sources\n"]
        seen = set()
        for page in pages:
            url = page["url"]
            if url not in seen:
                seen.add(url)
                lines.append(f"- [{page.get('title') or url}]({url})")
        if not pages:
            for r in search_results[:10]:
                url = r["url"]
                if url not in seen:
                    seen.add(url)
                    lines.append(f"- [{r.get('title', url)}]({url})")
        return "\n".join(lines)

    def _save(self, query: str, content: str) -> Path:
        slug = re.sub(r"[^\w\s-]", "", query.lower())
        slug = re.sub(r"[\s]+", "_", slug)[:50]
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_dir = Path(settings.OUTPUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{date}_{slug}.md"
        path.write_text(content, encoding="utf-8")
        return path
