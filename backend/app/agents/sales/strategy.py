import json
from dataclasses import dataclass

import anthropic

from app.agents.base.agent import BaseAgent
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import ObjectionResponse, SalesData, SalesPhase
from app.core.config import settings

SYSTEM_PROMPT = """\
You are a sales strategist working with a user to develop their \
sales strategy. You have company data and market research available.

IMPORTANT RULES FOR THIS CONVERSATION:
- Work through ONE element at a time. Do NOT dump everything at once.
- After proposing each element, WAIT for the user to approve or give feedback.
- Only call `store_strategy` for elements the user has approved.
- Only call `mark_strategy_complete` when the user explicitly says \
they are satisfied or wants to proceed to the pitch deck.

Work through these elements in order:
1. **Positioning** — Propose how the product should be positioned. \
Ask if the user agrees or wants changes.
2. **Value Proposition** — Propose a one-line value prop. Wait for approval.
3. **Key Messages** — Propose 3-5 key sales messages. Refine with the user.
4. **Objection Handling** — Suggest common objections and responses. \
Ask if the user wants to add or change any.
5. **Target Personas** — Describe 2-3 buyer personas. Confirm with the user.

After ALL elements are approved, ask: "Are you happy with the strategy? \
Should I generate the pitch deck?" Only call `mark_strategy_complete` \
if they say yes.

Start by proposing the positioning statement."""

STORE_STRATEGY_TOOL = {
    "name": "store_strategy",
    "description": (
        "Store a strategy element that the user has approved. "
        "Only call this AFTER the user confirms they are happy "
        "with the proposed element."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "positioning": {
                "type": "string",
                "description": "Market positioning statement",
            },
            "value_proposition": {
                "type": "string",
                "description": "Core value proposition",
            },
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
    "description": (
        "Store an objection/response pair the user approved"
    ),
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
    "description": (
        "Mark strategy as finalized. ONLY call this when the "
        "user explicitly confirms they are satisfied with all "
        "strategy elements and wants to generate the pitch deck."
    ),
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


def _save_sales_data(
    context: AgentContext, data: SalesData
) -> None:
    context.shared_state["sales_data"] = data.model_dump()


@dataclass
class StrategyAgent(BaseAgent):
    name: str = "strategy"
    description: str = (
        "Develops sales positioning, messaging, and "
        "objection handling through multi-turn collaboration"
    )
    system_prompt: str = SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext,
        message: AgentMessage,
    ) -> AgentMessage:
        sales_data = _get_sales_data(context)
        client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

        # Build full context of what's been collected
        known = json.dumps(
            sales_data.model_dump(
                exclude_none=True, exclude_defaults=True
            ),
            indent=2,
        )
        system = (
            self.system_prompt
            + f"\n\nAll collected data:\n{known}"
        )

        # Show what strategy elements are already stored
        stored = []
        if sales_data.positioning:
            stored.append(
                f"Positioning: {sales_data.positioning}"
            )
        if sales_data.value_proposition:
            stored.append(
                f"Value prop: {sales_data.value_proposition}"
            )
        if sales_data.key_messages:
            stored.append(
                f"Key messages: {sales_data.key_messages}"
            )
        if sales_data.objections:
            stored.append(
                f"Objections: {len(sales_data.objections)} stored"
            )
        if sales_data.target_personas:
            stored.append(
                f"Personas: {sales_data.target_personas}"
            )

        if stored:
            system += (
                "\n\nStrategy elements already approved:\n"
                + "\n".join(f"- {s}" for s in stored)
                + "\n\nContinue with the next unapproved element."
            )

        # Include conversation history
        messages = []
        for msg in context.history:
            if msg.role in (
                MessageRole.USER,
                MessageRole.ASSISTANT,
            ):
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })
        messages.append({
            "role": "user",
            "content": message.content,
        })

        response = await client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=[
                STORE_STRATEGY_TOOL,
                STORE_OBJECTION_TOOL,
                COMPLETE_TOOL,
            ],
        )

        reply_text = ""
        for block in response.content:
            if block.type == "text":
                reply_text += block.text
            elif block.type == "tool_use":
                self._handle_tool(
                    block.name, block.input, sales_data
                )

        _save_sales_data(context, sales_data)

        if not reply_text.strip():
            if sales_data.phase == SalesPhase.DELIVERABLE:
                reply_text = (
                    "The strategy is locked in. "
                    "Generating your pitch deck now."
                )
            else:
                reply_text = (
                    "I've saved that. "
                    "Let's move to the next element."
                )

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=reply_text,
            agent_name=self.name,
            metadata={"phase": sales_data.phase.value},
        )

    def _handle_tool(
        self,
        tool_name: str,
        tool_input: dict,
        sales_data: SalesData,
    ) -> None:
        if tool_name == "store_strategy":
            if tool_input.get("positioning"):
                sales_data.positioning = (
                    tool_input["positioning"]
                )
            if tool_input.get("value_proposition"):
                sales_data.value_proposition = (
                    tool_input["value_proposition"]
                )
            if tool_input.get("key_messages"):
                sales_data.key_messages = (
                    tool_input["key_messages"]
                )
            if tool_input.get("target_personas"):
                sales_data.target_personas = (
                    tool_input["target_personas"]
                )

        elif tool_name == "store_objection":
            sales_data.objections.append(
                ObjectionResponse(
                    objection=tool_input["objection"],
                    response=tool_input["response"],
                )
            )

        elif tool_name == "mark_strategy_complete":
            sales_data.phase = SalesPhase.DELIVERABLE

    async def plan(
        self, context: AgentContext, task: str
    ) -> list[str]:
        return [
            "Propose and refine positioning",
            "Propose and refine value proposition",
            "Define key sales messages",
            "Prepare objection handling",
            "Identify target personas",
            "Get user approval to proceed",
        ]

    async def can_handle(
        self, message: AgentMessage
    ) -> float:
        return 0.2
