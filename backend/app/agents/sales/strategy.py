import json
from dataclasses import dataclass

import anthropic

from app.agents.base.agent import BaseAgent
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import ObjectionResponse, SalesData, SalesPhase
from app.core.config import settings

SYSTEM_PROMPT = """You are a sales strategist. Given company data and market research, you help \
develop a winning sales strategy.

Work with the user to develop:
1. **Positioning** — How the product should be positioned in the market
2. **Value Proposition** — The core value proposition statement
3. **Key Messages** — 3-5 key sales messages
4. **Objection Handling** — Common objections and how to respond
5. **Target Personas** — Key buyer personas to target

Be collaborative: propose ideas and refine based on user feedback. Use the tools to store \
finalized strategy elements. When you and the user are satisfied with the strategy, call \
`mark_strategy_complete`."""

STORE_STRATEGY_TOOL = {
    "name": "store_strategy",
    "description": "Store a finalized strategy element",
    "input_schema": {
        "type": "object",
        "properties": {
            "positioning": {"type": "string", "description": "Market positioning statement"},
            "value_proposition": {"type": "string", "description": "Core value proposition"},
            "key_messages": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key sales messages",
            },
            "target_personas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Target buyer personas",
            },
        },
    },
}

STORE_OBJECTION_TOOL = {
    "name": "store_objection",
    "description": "Store an objection and its recommended response",
    "input_schema": {
        "type": "object",
        "properties": {
            "objection": {"type": "string"},
            "response": {"type": "string"},
        },
        "required": ["objection", "response"],
    },
}

COMPLETE_TOOL = {
    "name": "mark_strategy_complete",
    "description": "Mark strategy development as complete",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
        },
        "required": ["summary"],
    },
}


def _get_sales_data(context: AgentContext) -> SalesData:
    raw = context.shared_state.get("sales_data")
    if isinstance(raw, dict):
        return SalesData(**raw)
    if isinstance(raw, SalesData):
        return raw
    return SalesData()


def _save_sales_data(context: AgentContext, data: SalesData) -> None:
    context.shared_state["sales_data"] = data.model_dump()


@dataclass
class StrategyAgent(BaseAgent):
    name: str = "strategy"
    description: str = "Develops sales positioning, messaging, and objection handling"
    system_prompt: str = SYSTEM_PROMPT

    async def execute(self, context: AgentContext, message: AgentMessage) -> AgentMessage:
        sales_data = _get_sales_data(context)
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Build full context
        known = json.dumps(sales_data.model_dump(exclude_none=True, exclude_defaults=True), indent=2)
        system = self.system_prompt + f"\n\nAll collected data:\n{known}"

        # Include conversation history for multi-turn strategy discussion
        messages = []
        for msg in context.history:
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
                messages.append({"role": msg.role.value, "content": msg.content})
        messages.append({"role": "user", "content": message.content})

        response = await client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=[STORE_STRATEGY_TOOL, STORE_OBJECTION_TOOL, COMPLETE_TOOL],
        )

        reply_text = ""
        for block in response.content:
            if block.type == "text":
                reply_text += block.text
            elif block.type == "tool_use":
                self._handle_tool(block.name, block.input, sales_data)

        _save_sales_data(context, sales_data)

        if not reply_text.strip():
            if sales_data.phase == SalesPhase.DELIVERABLE:
                reply_text = "Excellent! The strategy is locked in. Let me generate your pitch deck now."
            else:
                reply_text = "I've noted that. Let's continue refining the strategy."

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=reply_text,
            agent_name=self.name,
            metadata={"phase": sales_data.phase.value},
        )

    def _handle_tool(self, tool_name: str, tool_input: dict, sales_data: SalesData) -> None:
        if tool_name == "store_strategy":
            if tool_input.get("positioning"):
                sales_data.positioning = tool_input["positioning"]
            if tool_input.get("value_proposition"):
                sales_data.value_proposition = tool_input["value_proposition"]
            if tool_input.get("key_messages"):
                sales_data.key_messages = tool_input["key_messages"]
            if tool_input.get("target_personas"):
                sales_data.target_personas = tool_input["target_personas"]

        elif tool_name == "store_objection":
            sales_data.objections.append(
                ObjectionResponse(
                    objection=tool_input["objection"],
                    response=tool_input["response"],
                )
            )

        elif tool_name == "mark_strategy_complete":
            sales_data.phase = SalesPhase.DELIVERABLE

    async def plan(self, context: AgentContext, task: str) -> list[str]:
        return [
            "Develop market positioning",
            "Craft value proposition",
            "Define key sales messages",
            "Prepare objection handling",
            "Identify target personas",
        ]

    async def can_handle(self, message: AgentMessage) -> float:
        return 0.2
