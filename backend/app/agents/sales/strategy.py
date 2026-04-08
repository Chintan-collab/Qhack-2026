import json
from dataclasses import dataclass

from app.agents.base.agent import BaseAgent
from app.agents.base.llm import chat_completion
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import ObjectionResponse, SalesData, SalesPhase
from app.core.config import settings

SYSTEM_PROMPT = """\
You are a sales strategist helping an energy installer build a pitch for a \
residential customer. You have the customer's property data and market research.

IMPORTANT RULES:
- Work through ONE element at a time. Do NOT dump everything at once.
- After proposing each element, WAIT for the installer to approve or tweak.
- Only call `store_strategy` for elements the installer approves.
- Only call `mark_strategy_complete` when the installer says to proceed.

Work through these elements in order:
1. **Value Proposition** — Why this product makes sense for THIS customer \
(based on their energy usage, house, heating type, costs).
2. **Savings Estimate** — Estimated annual savings and payback period.
3. **Key Messages** — 3-5 talking points tailored to the customer's concerns.
4. **Financing Options** — Based on the customer's financial profile.
5. **Objection Handling** — Likely objections and responses.

After ALL elements are approved, ask: "Ready to generate the pitch deck?" \
Only call `mark_strategy_complete` if they say yes.

Start by proposing the value proposition."""

STORE_STRATEGY_TOOL = {
    "name": "store_strategy",
    "description": "Store an approved strategy element",
    "input_schema": {
        "type": "object",
        "properties": {
            "value_proposition": {"type": "string"},
            "savings_estimate": {"type": "string"},
            "payback_period": {"type": "string"},
            "key_messages": {
                "type": "array",
                "items": {"type": "string"},
            },
            "financing_options": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}

STORE_OBJECTION_TOOL = {
    "name": "store_objection",
    "description": "Store an approved objection/response pair",
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
        "Mark strategy as finalized. ONLY call when the "
        "installer confirms they want the pitch deck."
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
        "Develops personalized energy sales strategy "
        "through multi-turn collaboration"
    )
    system_prompt: str = SYSTEM_PROMPT

    async def execute(
        self,
        context: AgentContext,
        message: AgentMessage,
    ) -> AgentMessage:
        sales_data = _get_sales_data(context)

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

        stored = []
        if sales_data.value_proposition:
            stored.append(
                f"Value prop: {sales_data.value_proposition}"
            )
        if sales_data.savings_estimate:
            stored.append(
                f"Savings: {sales_data.savings_estimate}"
            )
        if sales_data.key_messages:
            stored.append(
                f"Key messages: {sales_data.key_messages}"
            )
        if sales_data.financing_options:
            stored.append(
                f"Financing: {sales_data.financing_options}"
            )
        if sales_data.objections:
            stored.append(
                f"Objections: {len(sales_data.objections)} stored"
            )

        if stored:
            system += (
                "\n\nStrategy elements already approved:\n"
                + "\n".join(f"- {s}" for s in stored)
                + "\n\nContinue with the next unapproved element."
            )

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

        response = await chat_completion(
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

        reply_text = response.text
        for tc in response.tool_calls:
            self._handle_tool(
                tc.name, tc.input, sales_data
            )

        _save_sales_data(context, sales_data)

        if not reply_text.strip():
            if sales_data.phase == SalesPhase.DELIVERABLE:
                reply_text = (
                    "Strategy locked in. "
                    "Generating your pitch deck now."
                )
            else:
                reply_text = (
                    "Saved. Let's move to the next element."
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
            if tool_input.get("value_proposition"):
                sales_data.value_proposition = (
                    tool_input["value_proposition"]
                )
            if tool_input.get("savings_estimate"):
                sales_data.savings_estimate = (
                    tool_input["savings_estimate"]
                )
            if tool_input.get("payback_period"):
                sales_data.payback_period = (
                    tool_input["payback_period"]
                )
            if tool_input.get("key_messages"):
                sales_data.key_messages = (
                    tool_input["key_messages"]
                )
            if tool_input.get("financing_options"):
                sales_data.financing_options = (
                    tool_input["financing_options"]
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
            "Propose value proposition",
            "Estimate savings and payback",
            "Define key sales messages",
            "Suggest financing options",
            "Prepare objection handling",
            "Get installer approval to proceed",
        ]

    async def can_handle(
        self, message: AgentMessage
    ) -> float:
        return 0.2
