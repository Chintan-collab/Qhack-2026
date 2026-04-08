import uuid
from typing import Any, AsyncIterator

from fastapi import WebSocket

from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.orchestrator.orchestrator import AgentOrchestrator
from app.schemas.chat import ChatRequest, ChatResponse


class ChatService:
    """Service layer for chat operations, bridges API <-> Agent system."""

    def __init__(self) -> None:
        self.orchestrator = AgentOrchestrator()

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        context = AgentContext(conversation_id=conversation_id)

        message = AgentMessage(
            role=MessageRole.USER,
            content=request.message,
        )

        response = await self.orchestrator.execute(context, message)

        return ChatResponse(
            conversation_id=conversation_id,
            message=response.content,
            agent_actions=[],
            metadata=response.metadata,
        )

    async def stream_response(
        self, conversation_id: str, websocket: WebSocket
    ) -> AsyncIterator[dict[str, Any]]:
        data = await websocket.receive_json()
        context = AgentContext(conversation_id=conversation_id)

        message = AgentMessage(
            role=MessageRole.USER,
            content=data["message"],
        )

        async for event in self.orchestrator.stream(context, message):
            yield event
