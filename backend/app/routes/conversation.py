import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.conversation.models import ConversationContext, LearnerAttempt
from app.deps import ConversationCoachDep
from app.speech.language import romanize_for_language

router = APIRouter()


@router.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    expected: str = Form(""),
    expected_alt: str = Form(""),
    language: str = Form("en"),
    target_audio: str = Form(""),
    target_meaning: str = Form(""),
    scene_contract: str = Form(""),
    focus_chunk_index: int = Form(-1),
):
    """Compatibility wrapper for the guided conversation attempt endpoint."""
    return await evaluate_conversation_attempt(
        file=file,
        expected=expected,
        expected_alt=expected_alt,
        language=language,
        target_audio=target_audio,
        target_meaning=target_meaning,
        scene_contract=scene_contract,
        scene_id="",
        function_id="",
        target_id="",
    )


@router.post("/api/conversation/attempt")
async def evaluate_conversation_attempt(
    conversation_coach: ConversationCoachDep,
    file: UploadFile = File(...),
    expected: str = Form(""),
    expected_alt: str = Form(""),
    language: str = Form("en"),
    target_audio: str = Form(""),
    target_meaning: str = Form(""),
    scene_contract: str = Form(""),
    scene_id: str = Form(""),
    function_id: str = Form(""),
    target_id: str = Form(""),
):
    """Evaluate whether a learner utterance fits the current guided scene."""
    suffix = Path(file.filename or "recording.webm").suffix or ".webm"
    audio_bytes = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(audio_bytes)
        temp_path = Path(temp_file.name)

    try:
        context = ConversationContext(
            language=language,
            scene_id=scene_id,
            function_id=function_id,
            target_id=target_id,
            target_text=expected,
            target_romanized=expected_alt,
            target_meaning=target_meaning,
            target_audio=target_audio,
            scene_contract=parse_scene_contract(scene_contract),
        )
        coach_response = conversation_coach.evaluate_attempt(
            attempt=LearnerAttempt(audio_path=temp_path),
            context=context,
        )
        return conversation_response_payload(
            response=coach_response.to_dict(),
            expected=expected,
            expected_alt=expected_alt,
            language=language,
        )
    finally:
        temp_path.unlink(missing_ok=True)


def conversation_response_payload(
    *,
    response: dict,
    expected: str,
    expected_alt: str,
    language: str,
) -> dict:
    """Return the new response shape plus legacy fields the current UI expects."""
    communication = romanized_communication(response["communication"], language)
    return {
        **response,
        "communication": communication,
        "transcript_phonetic": response["transcript_romanized"],
        "expected": expected,
        "expected_alt": expected_alt,
        "expected_phonetic": expected_alt or expected,
        "text_score": response["score"],
        "transcription_available": response["speech_available"],
        "transcription_feedback": response["speech_feedback"],
        "heard_rhythm": "",
        "heard_beats": [],
        "rhythm_score": 0.0,
        "rhythm_feedback": "Rhythm scoring disabled for guided conversation mode.",
        "rhythm_details": {},
        "chunk_feedback": [],
        "phone_available": False,
        "phone_score": 0.0,
        "phone_feedback": "Phone scoring disabled for guided conversation mode.",
        "learner_phones": [],
        "target_phones": [],
        "score": communication["confidence"],
        "is_match": communication["close_enough"],
        "review_only": False,
        "language": language,
    }


def romanized_communication(communication: dict, language: str) -> dict:
    """Return learner-facing feedback in readable Latin text when possible."""
    display = dict(communication)
    for key in ("message", "partner_response"):
        if display.get(key):
            display[key] = romanize_for_language(str(display[key]), language)
    return display


def parse_scene_contract(raw_contract: str) -> dict | None:
    if not raw_contract:
        return None
    try:
        parsed = json.loads(raw_contract)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
