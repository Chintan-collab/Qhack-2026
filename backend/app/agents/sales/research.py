import json
from dataclasses import dataclass

import anthropic

from app.agents.base.agent import BaseAgent
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

SYSTEM_PROMPT = (
    "You are a market research analyst. Given information "
    "about a company and its products, you conduct competitive "
    "analysis and market research.\n\n"
    "You have access to a `web_search` tool to find real-time "
    "information. Use it to:\n"
    "1. Search for direct competitors\n"
    "2. Find market trends and industry data\n"
    "3. Analyze competitive positioning\n"
    "4. Identify market size and growth\n\n"
    "After each search, summarize what you found and update "
    "the research data. When you have gathered enough "
    "competitive intelligence (at least 2-3 competitors and "
    "key market trends), call `mark_research_complete`.\n\n"
    "Be thorough but efficient. Focus on actionable insights "
    "for the sales team."
)

SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "Search the internet for market research, "
        "competitor info, and industry trends"
    ),
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

STORE_COMPETITOR_TOOL = {
    "name": "store_competitor",
    "description": "Store structured competitor information",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
            },
            "weaknesses": {
                "type": "array",
                "items": {"type": "string"},
            },
            "market_share": {"type": "string"},
        },
        "required": ["name"],
    },
}

STORE_TRENDS_TOOL = {
    "name": "store_market_trends",
    "description": (
        "Store market trends and insights "
        "discovered during research"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "trends": {
                "type": "array",
                "items": {"type": "string"},
            },
            "market_size": {"type": "string"},
            "insights": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}

COMPLETE_TOOL = {
    "name": "mark_research_complete",
    "description": "Mark research phase as complete",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Summary of research findings",
            },
        },
        "required": ["summary"],
    },
}

ALL_TOOLS = [
    SEARCH_TOOL,
    STORE_COMPETITOR_TOOL,
    STORE_TRENDS_TOOL,
    COMPLETE_TOOL,
]


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
        "Performs competitive analysis and market research"
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
        client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

        known = json.dumps(
            {
                "company": sales_data.company_name,
                "products": [
                    p.model_dump() for p in sales_data.products
                ],
                "target_market": sales_data.target_market,
                "industry": sales_data.industry,
            },
            indent=2,
        )
        system = (
            self.system_prompt
            + f"\n\nCompany data collected:\n{known}"
        )

        messages = [
            {"role": "user", "content": message.content}
        ]

        # Multi-step agentic loop
        all_text = ""
        for _ in range(settings.MAX_AGENT_STEPS):
            response = await client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system,
                messages=messages,
                tools=ALL_TOOLS,
            )

            tool_results = []
            for block in response.content:
                if block.type == "text":
                    all_text += block.text
                elif block.type == "tool_use":
                    result = await self._handle_tool(
                        block.name,
                        block.input,
                        sales_data,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
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
                "content": response.content,
            })
            messages.append({
                "role": "user",
                "content": tool_results,
            })

        if not all_text.strip():
            all_text = (
                "I've completed the market research. "
                "Let me now help develop your sales strategy."
            )

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=all_text,
            agent_name=self.name,
            metadata={"phase": sales_data.phase.value},
        )

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

        if tool_name == "store_competitor":
            competitor = CompetitorInfo(
                name=tool_input["name"],
                description=tool_input.get("description", ""),
                strengths=tool_input.get("strengths", []),
                weaknesses=tool_input.get("weaknesses", []),
                market_share=tool_input.get("market_share", ""),
            )
            names = {c.name for c in sales_data.competitors}
            if competitor.name not in names:
                sales_data.competitors.append(competitor)
            return f"Stored competitor: {competitor.name}"

        if tool_name == "store_market_trends":
            for trend in tool_input.get("trends", []):
                if trend not in sales_data.market_trends:
                    sales_data.market_trends.append(trend)
            if tool_input.get("market_size"):
                sales_data.market_size = tool_input["market_size"]
            for insight in tool_input.get("insights", []):
                if insight not in sales_data.industry_insights:
                    sales_data.industry_insights.append(insight)
            return "Market trends stored"

        if tool_name == "mark_research_complete":
            sales_data.phase = SalesPhase.STRATEGY
            summary = tool_input.get("summary", "")
            return f"Research complete: {summary}"

        return "Unknown tool"

    async def plan(
        self, context: AgentContext, task: str
    ) -> list[str]:
        return [
            "Search for direct competitors",
            "Analyze competitive landscape",
            "Research market trends and size",
            "Summarize findings",
        ]

    async def can_handle(
        self, message: AgentMessage
    ) -> float:
        return 0.2
