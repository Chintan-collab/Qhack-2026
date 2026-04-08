from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """Send a message and get an agent-orchestrated response."""
    service = ChatService()
    return await service.process_message(request)


@router.websocket("/ws/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str) -> None:
    """WebSocket endpoint for real-time streaming chat with agents."""
    await websocket.accept()
    service = ChatService()
    try:
        async for chunk in service.stream_response(conversation_id, websocket):
            await websocket.send_json(chunk)
    except WebSocketDisconnect:
        pass
