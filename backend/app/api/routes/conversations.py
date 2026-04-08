from fastapi import APIRouter

from app.schemas.chat import ConversationSummary

router = APIRouter()


@router.get("/", response_model=list[ConversationSummary])
async def list_conversations() -> list[ConversationSummary]:
    """List all conversations."""
    # TODO: fetch from DB
    return []


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict:
    """Get full conversation history."""
    # TODO: fetch from DB
    return {"id": conversation_id, "messages": []}


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """Delete a conversation."""
    # TODO: delete from DB
    return {"deleted": True}
