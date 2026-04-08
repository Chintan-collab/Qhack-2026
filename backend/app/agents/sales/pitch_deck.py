import json
from dataclasses import dataclass

import anthropic

from app.agents.base.agent import BaseAgent
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import SalesData, SalesPhase
from app.core.config import settings

SYSTEM_PROMPT = """You are an expert sales presentation writer. Given comprehensive sales data \
(company info, market research, competitive analysis, and sales strategy), generate a \
professional pitch deck report in Markdown format.

The report MUST include these sections:
1. **Executive Summary** — One paragraph overview
2. **Company Overview** — Who the company is and what they do
3. **Product/Service** — Detailed description with key features
4. **Market Opportunity** — Market size, trends, and growth
5. **Competitive Landscape** — Key competitors and differentiation
6. **Value Proposition** — Why customers should choose this product
7. **Key Sales Messages** — The core messages for the sales team
8. **Target Customer Profiles** — Who to sell to
9. **Objection Handling Guide** — Common objections with responses
10. **Recommended Next Steps** — Action items for the sales team

Make it professional, data-driven, and actionable. Use tables, bullet points, and clear \
formatting. This should be a document the sales team can immediately use."""


@dataclass
class PitchDeckAgent(BaseAgent):
    name: str = "pitch_deck"
    description: str = "Generates a comprehensive sales pitch deck report"
    system_prompt: str = SYSTEM_PROMPT

    async def execute(self, context: AgentContext, message: AgentMessage) -> AgentMessage:
        raw = context.shared_state.get("sales_data")
        if isinstance(raw, dict):
            sales_data = SalesData(**raw)
        elif isinstance(raw, SalesData):
            sales_data = raw
        else:
            sales_data = SalesData()

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        data_dump = json.dumps(sales_data.model_dump(), indent=2)

        response = await client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Generate the complete pitch deck report based on this data:\n\n"
                        f"```json\n{data_dump}\n```\n\n"
                        f"Additional user request: {message.content}"
                    ),
                }
            ],
        )

        report_text = ""
        for block in response.content:
            if block.type == "text":
                report_text += block.text

        # Store the deliverable
        sales_data.phase = SalesPhase.COMPLETE
        context.shared_state["sales_data"] = sales_data.model_dump()
        context.shared_state["deliverable"] = report_text

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=report_text,
            agent_name=self.name,
            metadata={
                "phase": SalesPhase.COMPLETE.value,
                "deliverable_ready": True,
            },
        )

    async def plan(self, context: AgentContext, task: str) -> list[str]:
        return ["Generate pitch deck from accumulated sales data"]

    async def can_handle(self, message: AgentMessage) -> float:
        return 0.1
