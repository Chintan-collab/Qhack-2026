import json
from dataclasses import dataclass

from app.agents.base.agent import BaseAgent
from app.agents.base.llm import chat_completion
from app.agents.base.types import (
    AgentContext,
    AgentMessage,
    MessageRole,
)
from app.agents.sales.schemas import (
    CompetitorInfo,
    SalesData,
    SalesPhase,
)
from app.core.config import settings

SYSTEM_PROMPT = """\
You are a market research analyst for a residential energy installer. \
Given customer and property data, research the local energy market to \
help the installer build a compelling pitch.

Use the `web_search` tool to find:
1. Regional subsidies, tax credits, and incentive programs (e.g. KfW, BAFA, \
local municipality programs) for the customer's postal code area
2. Current energy prices and outlook in Germany
3. Competitor pricing for the products the customer is interested in
4. Market trends in residential solar/heat pump/battery adoption

After searching, use `store_research` to save your findings.

When you have enough data (incentives + at least some market context), \
present a clear summary and say you are ready for the strategy phase. \
Do NOT ask the user what to search — you already have the customer data."""

SEARCH_TOOL = {
    "name": "web_search",
    "description": "Search the internet for energy incentives, pricing, and market data",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            }
        },
        "required": ["query"],
    },
}

STORE_RESEARCH_TOOL = {
    "name": "store_research",
    "description": "Store research findings",
    "input_schema": {
        "type": "object",
        "properties": {
            "regional_incentives": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Subsidies, tax credits, programs",
            },
            "energy_price_outlook": {
                "type": "string",
                "description": "Current and projected energy prices",
            },
            "market_trends": {
                "type": "array",
                "items": {"type": "string"},
            },
            "insights": {
                "type": "array",
                "items": {"type": "string"},
            },
            "competitor_name": {"type": "string"},
            "competitor_description": {"type": "string"},
            "competitor_strengths": {
                "type": "array",
                "items": {"type": "string"},
            },
            "competitor_weaknesses": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}

ALL_TOOLS = [SEARCH_TOOL, STORE_RESEARCH_TOOL]


def _get_sales_data(context: AgentContext) -> SalesData:
    raw = context.shared_state.get("sales_data")
    if isinstance(raw, dict):
        return SalesData(**raw)
    if isinstance(raw, SalesData):
        return raw
    return SalesData()


def _save(context: AgentContext, data: SalesData) -> None:
    context.shared_state["sales_data"] = data.model_dump()


@dataclass
class ResearchAgent(BaseAgent):
    name: str = "research"
    description: str = (
        "Researches energy incentives, pricing, and market data"
    )
    system_prompt: str = SYSTEM_PROMPT

    def __post_init__(self) -> None:
        from app.agents.tools.web_search import WebSearchTool
        self._search_tool = WebSearchTool()

    async def execute(
        self,
        context: AgentContext,
        message: AgentMessage,
    ) -> AgentMessage:
        sales_data = _get_sales_data(context)

        known = json.dumps(
            {
                "customer": sales_data.customer_name,
                "postal_code": sales_data.postal_code,
                "city": sales_data.city,
                "product_interest": sales_data.product_interest,
                "house_type": sales_data.house_type,
                "build_year": sales_data.build_year,
                "heating_type": sales_data.heating_type,
                "electricity_kwh_year": sales_data.electricity_kwh_year,
                "monthly_bill": sales_data.monthly_energy_bill_eur,
                "existing_assets": sales_data.existing_assets,
            },
            indent=2,
        )
        system = (
            self.system_prompt
            + f"\n\nCustomer data:\n{known}"
        )

        messages = [
            {"role": "user", "content": message.content}
        ]

        all_text = ""
        for _ in range(settings.MAX_AGENT_STEPS):
            response = await chat_completion(
                model=self.model,
                max_tokens=2048,
                system=system,
                messages=messages,
                tools=ALL_TOOLS,
            )

            tool_results = []
            all_text += response.text
            for tc in response.tool_calls:
                result = await self._handle_tool(
                    tc.name,
                    tc.input,
                    sales_data,
                )
                tool_results.append({
                    "type": "tool_result",
                    "name": tc.name,
                    "content": result,
                })

            _save(context, sales_data)

            if (
                response.stop_reason == "end_turn"
                or not tool_results
            ):
                break

            messages.append({
                "role": "assistant",
                "content": response.text or "Using tools.",
            })
            messages.append({
                "role": "user",
                "content": (
                    f"Tool results: {json.dumps(tool_results)}"
                ),
            })

        if not all_text.strip():
            all_text = self._build_summary(sales_data)

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=all_text,
            agent_name=self.name,
            metadata={"phase": sales_data.phase.value},
        )

    def _build_summary(self, sales_data: SalesData) -> str:
        parts = ["Here's what I found:\n"]
        if sales_data.regional_incentives:
            parts.append("**Regional Incentives:**")
            for i in sales_data.regional_incentives:
                parts.append(f"- {i}")
        if sales_data.energy_price_outlook:
            parts.append(
                f"\n**Energy Prices:** "
                f"{sales_data.energy_price_outlook}"
            )
        if sales_data.market_trends:
            parts.append("\n**Market Trends:**")
            for t in sales_data.market_trends:
                parts.append(f"- {t}")
        if sales_data.competitors:
            parts.append("\n**Competitors:**")
            for c in sales_data.competitors:
                parts.append(f"- {c.name}: {c.description}")
        parts.append(
            "\nResearch complete — moving to strategy."
        )
        return "\n".join(parts)

    async def _handle_tool(
        self,
        tool_name: str,
        tool_input: dict,
        sales_data: SalesData,
    ) -> str:
        if tool_name == "web_search":
            query = tool_input.get("query", "")
            result = await self._search_tool.execute(
                query=query
            )
            return result.output

        if tool_name == "store_research":
            for inc in tool_input.get(
                "regional_incentives", []
            ):
                if inc not in sales_data.regional_incentives:
                    sales_data.regional_incentives.append(inc)
            if tool_input.get("energy_price_outlook"):
                sales_data.energy_price_outlook = (
                    tool_input["energy_price_outlook"]
                )
            for trend in tool_input.get("market_trends", []):
                if trend not in sales_data.market_trends:
                    sales_data.market_trends.append(trend)
            for ins in tool_input.get("insights", []):
                if ins not in sales_data.industry_insights:
                    sales_data.industry_insights.append(ins)
            if tool_input.get("competitor_name"):
                comp = CompetitorInfo(
                    name=tool_input["competitor_name"],
                    description=tool_input.get(
                        "competitor_description", ""
                    ),
                    strengths=tool_input.get(
                        "competitor_strengths", []
                    ),
                    weaknesses=tool_input.get(
                        "competitor_weaknesses", []
                    ),
                )
                names = {
                    c.name for c in sales_data.competitors
                }
                if comp.name not in names:
                    sales_data.competitors.append(comp)
            return "Research stored"

        return "Unknown tool"

    async def plan(
        self, context: AgentContext, task: str
    ) -> list[str]:
        return [
            "Search for regional energy incentives",
            "Research energy prices and outlook",
            "Find competitor pricing",
            "Summarize findings",
        ]

    async def can_handle(
        self, message: AgentMessage
    ) -> float:
        return 0.2
