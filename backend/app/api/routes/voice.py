from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.voice import TranscriptionResponse
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest

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


@router.post("/tts")
async def text_to_speech(
    request: dict,
) -> StreamingResponse:
    """Convert text to speech using OpenAI TTS.

    Body: { "text": "...", "voice": "alloy" }
    Returns: audio/mpeg stream
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured",
        )

    text = request.get("text", "")
    voice = request.get("voice", "alloy")

    if not text:
        raise HTTPException(
            status_code=400, detail="No text provided"
        )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )

    return StreamingResponse(
        response.iter_bytes(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=response.mp3"
        },
    )


@router.post("/chat")
async def voice_chat(
    audio: UploadFile = File(...),
    conversation_id: str | None = None,
    project_id: str | None = None,
    voice: str = "alloy",
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Full voice round-trip: transcribe → agent → TTS.

    Accepts audio, returns audio. One request, one response.
    The transcript and agent reply are in response headers.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured",
        )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Step 1: Transcribe
    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=(audio.filename or "audio.webm", await audio.read()),
    )
    user_text = transcript.text

    # Step 2: Run through the agent pipeline
    service = ChatService(db=db)
    chat_response = await service.process_message(
        ChatRequest(
            conversation_id=conversation_id,
            project_id=project_id,
            message=user_text,
        )
    )

    # Step 3: Convert agent response to speech
    tts_response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=chat_response.message,
        response_format="mp3",
    )

    return StreamingResponse(
        tts_response.iter_bytes(),
        media_type="audio/mpeg",
        headers={
            "X-Transcript": user_text.replace("\n", " "),
            "X-Agent-Reply": (
                chat_response.message[:500].replace("\n", " ")
            ),
            "X-Conversation-Id": chat_response.conversation_id,
            "X-Agent-Name": str(
                chat_response.metadata.get("agent_name", "")
            ),
            "X-Phase": str(
                chat_response.metadata.get("phase", "")
            ),
            "Access-Control-Expose-Headers": (
                "X-Transcript, X-Agent-Reply, "
                "X-Conversation-Id, X-Agent-Name, X-Phase"
            ),
        },
    )
