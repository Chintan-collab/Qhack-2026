import uuid
from typing import Any, AsyncIterator

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.sales.schemas import SalesData
from app.agents.sales.supervisor import SalesSupervisor
from app.models.conversation import Conversation, Message
from app.models.project import Project
from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    """Service layer for chat operations, bridges API <-> Agent system."""

    # In-memory context store keyed by conversation_id.
    # Preserves agent history and shared_state across turns.
    _contexts: dict[str, AgentContext] = {}

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.orchestrator = SalesSupervisor()
        self.db = db

    def _get_or_create_context(
        self, conversation_id: str
    ) -> AgentContext:
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = AgentContext(
                conversation_id=conversation_id
            )
        return self._contexts[conversation_id]

    async def _persist_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: str | None = None,
    ) -> None:
        if not self.db:
            return
        # Ensure conversation row exists
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if not result.scalar_one_or_none():
            self.db.add(Conversation(id=conversation_id))

        self.db.add(Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
        ))
        await self.db.commit()

    async def _load_project_into_context(
        self, project_id: str, context: AgentContext
    ) -> None:
        """Load project data into agent context shared_state."""
        if not self.db:
            return
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return

        # Build SalesData from project fields
        sales_data = SalesData(
            company_name=project.company_name,
            company_description=project.company_description,
            industry=project.industry,
            target_market=project.target_market,
            competitors=project.competitors or [],
        )
        # Set products from project JSON
        if project.products:
            sales_data.products = project.products

        # If project already has data, skip to appropriate phase
        if sales_data.is_gathering_complete():
            from app.agents.sales.schemas import SalesPhase
            sales_data.phase = SalesPhase.RESEARCH

        context.shared_state["sales_data"] = sales_data.model_dump()
        context.shared_state["project_id"] = project_id

    async def _persist_project_data(
        self, context: AgentContext
    ) -> None:
        """Sync sales_data back to the Project row."""
        project_id = context.shared_state.get("project_id")
        if not self.db or not project_id:
            return

        raw = context.shared_state.get("sales_data", {})
        if isinstance(raw, SalesData):
            sales_data = raw
        else:
            sales_data = SalesData(**raw)

        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return

        project.company_name = sales_data.company_name
        project.company_description = sales_data.company_description
        project.industry = sales_data.industry
        project.target_market = sales_data.target_market
        project.products = [
            p.model_dump() if hasattr(p, "model_dump") else p
            for p in sales_data.products
        ]
        project.competitors = [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in sales_data.competitors
        ]
        project.research_data = {
            "market_trends": sales_data.market_trends,
            "market_size": sales_data.market_size,
            "industry_insights": sales_data.industry_insights,
        }
        project.strategy_notes = {
            "positioning": sales_data.positioning,
            "value_proposition": sales_data.value_proposition,
            "key_messages": sales_data.key_messages,
            "objections": [
                o.model_dump() if hasattr(o, "model_dump") else o
                for o in sales_data.objections
            ],
            "target_personas": sales_data.target_personas,
        }
        project.status = sales_data.phase.value
        await self.db.commit()

    async def process_message(
        self, request: ChatRequest
    ) -> ChatResponse:
        conversation_id = (
            request.conversation_id or str(uuid.uuid4())
        )
        context = self._get_or_create_context(conversation_id)

        # Load project data into context on first message
        if request.project_id and "project_id" not in context.shared_state:
            await self._load_project_into_context(
                request.project_id, context
            )

        # Ensure sales_data exists in context
        if "sales_data" not in context.shared_state:
            context.shared_state["sales_data"] = (
                SalesData().model_dump()
            )

        message = AgentMessage(
            role=MessageRole.USER,
            content=request.message,
        )

        # Persist user message
        await self._persist_message(
            conversation_id, "user", request.message
        )

        response = await self.orchestrator.execute(context, message)

        # Persist assistant response
        await self._persist_message(
            conversation_id,
            "assistant",
            response.content,
            response.agent_name,
        )

        # Sync updated sales data back to project
        await self._persist_project_data(context)

        return ChatResponse(
            conversation_id=conversation_id,
            message=response.content,
            agent_actions=[],
            metadata=response.metadata,
        )

    async def stream_response(
        self,
        conversation_id: str,
        websocket: WebSocket,
    ) -> AsyncIterator[dict[str, Any]]:
        data = await websocket.receive_json()
        context = self._get_or_create_context(conversation_id)

        # Load project if specified
        project_id = data.get("project_id")
        if project_id and "project_id" not in context.shared_state:
            await self._load_project_into_context(
                project_id, context
            )

        if "sales_data" not in context.shared_state:
            context.shared_state["sales_data"] = (
                SalesData().model_dump()
            )

        message = AgentMessage(
            role=MessageRole.USER,
            content=data["message"],
        )

        await self._persist_message(
            conversation_id, "user", data["message"]
        )

        full_response = ""
        agent_name = None

        async for event in self.orchestrator.stream(
            context, message
        ):
            if event.get("type") == "agent_selected":
                agent_name = event.get("agent")
            if event.get("type") == "message":
                full_response += event.get("content", "")
            yield event

        # Persist the full streamed response
        if full_response:
            await self._persist_message(
                conversation_id,
                "assistant",
                full_response,
                agent_name,
            )

        # Sync updated sales data back to project
        await self._persist_project_data(context)
