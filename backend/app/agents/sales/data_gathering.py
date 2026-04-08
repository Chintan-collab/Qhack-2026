import json
from dataclasses import dataclass

from app.agents.base.agent import BaseAgent
from app.agents.base.llm import chat_completion
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import SalesData, SalesPhase, ProductInfo
from app.core.config import settings

SYSTEM_PROMPT = """You are a sales consultant conducting a discovery session. Your job is to \
gather key information about the user's company, products, and target market.

You must collect the following (ask naturally, one or two questions at a time):
1. Company name and description
2. Industry
3. Products/services (name, description, key features)
4. Target market / ideal customer
5. Pain points their product solves
6. Unique selling points

When the user provides information, call the `extract_sales_data` tool to structure it.
When you believe you have enough data (at minimum: company name, description, at least one \
product, and target market), call `mark_gathering_complete`.

Be conversational and professional. Ask follow-up questions to get specific, actionable details. \
Do not ask all questions at once — have a natural dialogue."""

EXTRACT_TOOL = {
    "name": "extract_sales_data",
    "description": "Extract and store structured sales data from the conversation",
    "input_schema": {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Name of the company"},
            "company_description": {"type": "string", "description": "What the company does"},
            "industry": {"type": "string", "description": "Industry/sector"},
            "product_name": {"type": "string", "description": "Product or service name"},
            "product_description": {"type": "string", "description": "What the product does"},
            "product_features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key features of the product",
            },
            "target_market": {"type": "string", "description": "Target customer segment"},
            "pain_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Customer pain points the product addresses",
            },
            "unique_selling_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What makes this product/company unique",
            },
        },
    },
}

COMPLETE_TOOL = {
    "name": "mark_gathering_complete",
    "description": "Mark data gathering as complete when sufficient information has been collected",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief summary of what was collected",
            }
        },
        "required": ["summary"],
    },
}


def _get_sales_data(context: AgentContext) -> SalesData:
    raw = context.shared_state.get("sales_data")
    if isinstance(raw, SalesData):
        return raw
    if isinstance(raw, dict):
        return SalesData(**raw)
    return SalesData()


def _save_sales_data(context: AgentContext, data: SalesData) -> None:
    context.shared_state["sales_data"] = data.model_dump()


def _build_messages(context: AgentContext) -> list[dict]:
    """Convert agent history to Anthropic message format."""
    messages = []
    for msg in context.history:
        if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
            messages.append({"role": msg.role.value, "content": msg.content})
    return messages


def _apply_extraction(sales_data: SalesData, tool_input: dict) -> SalesData:
    """Apply extracted fields to sales data."""
    if tool_input.get("company_name"):
        sales_data.company_name = tool_input["company_name"]
    if tool_input.get("company_description"):
        sales_data.company_description = tool_input["company_description"]
    if tool_input.get("industry"):
        sales_data.industry = tool_input["industry"]
    if tool_input.get("product_name"):
        product = ProductInfo(
            name=tool_input["product_name"],
            description=tool_input.get("product_description", ""),
            key_features=tool_input.get("product_features", []),
        )
        # Avoid duplicates by name
        existing_names = {p.name for p in sales_data.products}
        if product.name not in existing_names:
            sales_data.products.append(product)
    if tool_input.get("target_market"):
        sales_data.target_market = tool_input["target_market"]
    if tool_input.get("pain_points"):
        for pp in tool_input["pain_points"]:
            if pp not in sales_data.pain_points:
                sales_data.pain_points.append(pp)
    if tool_input.get("unique_selling_points"):
        for usp in tool_input["unique_selling_points"]:
            if usp not in sales_data.unique_selling_points:
                sales_data.unique_selling_points.append(usp)
    return sales_data


@dataclass
class DataGatheringAgent(BaseAgent):
    name: str = "data_gathering"
    description: str = "Collects company, product, and market info through conversation"
    system_prompt: str = SYSTEM_PROMPT

    async def execute(self, context: AgentContext, message: AgentMessage) -> AgentMessage:
        sales_data = _get_sales_data(context)

        # Build conversation history for the LLM
        messages = _build_messages(context)
        messages.append({"role": "user", "content": message.content})

        # Add context about what we already know
        system = self.system_prompt
        if sales_data.company_name:
            known = json.dumps(
                sales_data.model_dump(exclude_none=True, exclude_defaults=True),
                indent=2,
            )
            system += f"\n\nData collected so far:\n{known}"

        response = await chat_completion(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=[EXTRACT_TOOL, COMPLETE_TOOL],
        )

        # Process tool calls and text response
        reply_text = response.text
        for tc in response.tool_calls:
            if tc.name == "extract_sales_data":
                sales_data = _apply_extraction(sales_data, tc.input)
            elif tc.name == "mark_gathering_complete":
                sales_data.phase = SalesPhase.RESEARCH

        _save_sales_data(context, sales_data)

        # If the LLM only made tool calls with no text, generate a follow-up
        if not reply_text.strip():
            if sales_data.phase == SalesPhase.RESEARCH:
                reply_text = (
                    "I've captured all the key information about "
                    "your company, products, and target market. "
                    "Now I'll research your competitive landscape."
                )
            else:
                reply_text = (
                    "Got it, I've noted that down. "
                    "What else can you tell me?"
                )

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=reply_text,
            agent_name=self.name,
            metadata={"phase": sales_data.phase.value, "sales_data": sales_data.model_dump()},
        )

    async def plan(self, context: AgentContext, task: str) -> list[str]:
        return [
            "Ask about company name and description",
            "Ask about products/services",
            "Ask about target market and pain points",
            "Confirm and summarize gathered data",
        ]

    async def can_handle(self, message: AgentMessage) -> float:
        # This is handled by the supervisor, but provide a baseline
        return 0.3
