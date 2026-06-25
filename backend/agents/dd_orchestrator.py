from agents.base import BaseAgent
from agents.registry import register_agent
from agents.valuation import ValuationAgent
from agents.regulatory import RegulatoryAgent
from agents.risk import RiskAgent
from agents.dd_writer import DDWriterAgent


@register_agent("dd_orchestrator")
class DDOrchestratorAgent(BaseAgent):
    name = "dd_orchestrator"

    async def run(self, task: dict) -> dict:
        asset_name: str = task["asset_name"]
        asset_location: str = task["asset_location"]
        asset_type: str = task.get("asset_type", "real estate")
        asset_description: str = task.get("asset_description", "")

        await self.emit("planning", f'Starting due diligence for: "{asset_name}" in {asset_location}')

        base = {"asset_name": asset_name, "asset_location": asset_location, "asset_type": asset_type}

        await self.emit("planning", "Phase 1/3: Valuation analysis")
        valuation_result = await ValuationAgent(self.wf).run(base)

        await self.emit("planning", "Phase 2/3: Regulatory review")
        regulatory_result = await RegulatoryAgent(self.wf).run(base)

        await self.emit("planning", "Phase 3/3: Risk assessment")
        risk_result = await RiskAgent(self.wf).run(base)

        await self.emit("planning", "Synthesizing final DD report")
        write_result = await DDWriterAgent(self.wf).run({
            **base,
            "asset_description": asset_description,
            "valuation": valuation_result,
            "regulatory": regulatory_result,
            "risk": risk_result,
        })

        await self.emit(
            "completed",
            f"Due diligence complete — Score: {write_result['dd_score']}/100 — {write_result['recommendation']}",
            {
                "output_file": write_result["output_file"],
                "dd_score": write_result["dd_score"],
                "recommendation": write_result["recommendation"],
                "params": write_result["params"],
            },
        )
        return write_result
