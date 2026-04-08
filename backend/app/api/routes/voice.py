from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.voice import TranscriptionResponse

router = APIRouter()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
) -> TranscriptionResponse:
    """Transcribe audio to text using OpenAI Whisper."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured",
        )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=(audio.filename or "audio.webm", await audio.read()),
    )

    return TranscriptionResponse(text=transcript.text)
