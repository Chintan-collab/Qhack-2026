import tempfile
import os

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from google.genai import types as genai_types

from app.core.config import settings
from app.db.session import get_db
from app.schemas.voice import TranscriptionResponse
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest

router = APIRouter()


async def _transcribe_with_gemini(audio_bytes: bytes, filename: str) -> str:
    """Transcribe audio using Gemini's multimodal capabilities."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Write audio to a temp file for upload
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        audio_file = client.files.upload(file=tmp_path)
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                audio_file,
                "Transcribe this audio exactly as spoken. "
                "Return only the transcription, nothing else.",
            ],
        )
        return response.text.strip()
    finally:
        os.unlink(tmp_path)


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
) -> TranscriptionResponse:
    """Transcribe audio to text using Gemini."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured",
        )

    audio_bytes = await audio.read()
    text = await _transcribe_with_gemini(
        audio_bytes, audio.filename or "audio.webm"
    )

    return TranscriptionResponse(text=text)


@router.post("/chat")
async def voice_chat(
    audio: UploadFile = File(...),
    conversation_id: str | None = None,
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Full voice round-trip: transcribe with Gemini → agent pipeline.

    Returns JSON with transcript and agent reply text.
    Frontend handles TTS via browser SpeechSynthesis.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured",
        )

    # Step 1: Transcribe with Gemini
    audio_bytes = await audio.read()
    user_text = await _transcribe_with_gemini(
        audio_bytes, audio.filename or "audio.webm"
    )

    # Step 2: Run through the agent pipeline
    service = ChatService(db=db)
    chat_response = await service.process_message(
        ChatRequest(
            conversation_id=conversation_id,
            project_id=project_id,
            message=user_text,
        )
    )

    return {
        "transcript": user_text,
        "reply": chat_response.message,
        "conversation_id": chat_response.conversation_id,
        "agent_name": chat_response.metadata.get("agent_name"),
        "phase": chat_response.metadata.get("phase"),
        "metadata": chat_response.metadata,
    }
