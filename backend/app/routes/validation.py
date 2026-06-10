import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.conversation.coach import ConversationCoach
from app.conversation.models import ConversationContext, LearnerAttempt
from app.deps import ConversationCoachDep
from app.runtime import validation_store

logger = logging.getLogger(__name__)

router = APIRouter()


class ValidationSessionRequest(BaseModel):
    sessionId: str | None = None
    participantId: str | None = None
    language: str
    sceneSet: str = "mvp"
    lessonPage: str | None = None


class ValidationEventRequest(BaseModel):
    type: str = Field(min_length=1)
    eventId: str | None = None
    participantId: str | None = None
    language: str | None = None
    sceneSet: str | None = None
    lessonId: str | None = None
    lessonPage: str | None = None
    stepId: str | None = None
    stepIndex: int | None = None
    frameId: str | None = None
    choiceId: str | None = None
    isCorrect: bool | None = None
    direction: str | None = None
    targetId: str | None = None
    timestamp: str | None = None
    metadata: dict | None = None


@router.post("/api/validation/sessions")
def start_validation_session(request: ValidationSessionRequest):
    """Create a local validation session for workflow events and recordings."""
    try:
        return validation_store.create_session(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/api/validation/sessions/{session_id}/events")
def log_validation_event(session_id: str, request: ValidationEventRequest):
    """Append one local validation event to the session event log."""
    try:
        return validation_store.append_event(session_id, request.model_dump(exclude_none=True))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/api/validation/sessions/{session_id}/attempts")
async def save_validation_attempt(
    session_id: str,
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
):
    """Save one learner recording locally with enough metadata for later review."""
    try:
        parsed_metadata = json.loads(metadata)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid attempt metadata JSON") from error
    if not isinstance(parsed_metadata, dict):
        raise HTTPException(status_code=400, detail="Attempt metadata must be a JSON object")

    audio_bytes = await file.read()
    try:
        return validation_store.save_attempt(
            session_id=session_id,
            attempt_id=parsed_metadata.get("attemptId"),
            filename=file.filename,
            content_type=file.content_type,
            audio_bytes=audio_bytes,
            metadata=parsed_metadata,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/api/validation/sessions/{session_id}/scorecard")
def get_validation_scorecard(
    session_id: str,
    conversation_coach: ConversationCoachDep,
    score: bool = Query(default=False),
):
    """Return a local scorecard skeleton for manual or AI review."""
    try:
        if score:
            logger.warning(
                "GET /api/validation/sessions/{session_id}/scorecard?score=true triggers scoring; "
                "prefer POST /attempts/{attempt_id}/score for explicit scoring."
            )
            score_validation_attempts(session_id, conversation_coach)
        return validation_store.scorecard(session_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error


@router.get("/api/validation/sessions/{session_id}/attempts/{attempt_id}/audio")
def get_validation_attempt_audio(session_id: str, attempt_id: str):
    """Return one saved local learner recording for scorecard review."""
    try:
        return FileResponse(str(validation_store.attempt_audio_path(session_id, attempt_id)))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Attempt '{attempt_id}' not found") from error


@router.delete("/api/validation/sessions/{session_id}/attempts/{attempt_id}")
def delete_validation_attempt(session_id: str, attempt_id: str):
    """Delete one saved learner recording attempt and its score."""
    try:
        return validation_store.delete_attempt(session_id, attempt_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Attempt '{attempt_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/api/validation/sessions/{session_id}/attempts/{attempt_id}/score")
def score_validation_attempt_endpoint(
    session_id: str,
    attempt_id: str,
    conversation_coach: ConversationCoachDep,
):
    """Score one saved learner recording from the admin dashboard."""
    try:
        attempt = validation_store.attempt_metadata(session_id, attempt_id)
        return score_validation_attempt(session_id, attempt, conversation_coach)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Attempt '{attempt_id}' not found") from error


@router.get("/api/validation/admin/summary")
def get_validation_admin_summary():
    """Return a local validation rollup across participants, languages, and review days."""
    return validation_store.admin_summary()


@router.get("/api/validation/participant-name")
def get_validation_participant_name():
    """Return a human-readable participant id that has not appeared in saved sessions."""
    return validation_store.suggest_participant_name()


@router.delete("/api/validation/users/{participant_id}")
def delete_validation_user(participant_id: str):
    """Delete all validation sessions for one participant."""
    return validation_store.delete_user(participant_id)


@router.delete("/api/validation/sessions/{session_id}")
def delete_validation_session(session_id: str):
    """Delete one validation session and its saved recordings."""
    try:
        return validation_store.delete_session(session_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/api/validation/sessions/{session_id}/data")
def delete_validation_session_data(session_id: str, kind: list[str] = Query(...)):
    """Delete selected validation data files for one session."""
    try:
        return validation_store.delete_session_data(session_id, kind)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def score_validation_attempts(session_id: str, conversation_coach: ConversationCoach) -> None:
    """Score unscored local recordings when the scorecard is opened."""
    for attempt in validation_store.attempts_needing_score(session_id):
        score_validation_attempt(session_id, attempt, conversation_coach)


def score_validation_attempt(session_id: str, attempt: dict, conversation_coach: ConversationCoach) -> dict:
    attempt_id = str(attempt.get("attemptId", ""))
    if not attempt_id:
        return {"status": "skipped", "error": "Missing attempt id"}
    try:
        coach_response = conversation_coach.evaluate_attempt(
            attempt=LearnerAttempt(audio_path=validation_store.attempt_audio_path(session_id, attempt_id)),
            context=ConversationContext(
                language=str(attempt.get("language", "")),
                target_id=str(attempt.get("targetId", "")),
                target_text=str(attempt.get("expectedText", "")),
                target_romanized=str(attempt.get("expectedTransliteration", "")),
                target_audio=str(attempt.get("targetAudioUrl", "")),
            ),
        )
        return validation_store.save_score(
            session_id,
            attempt_id,
            {
                "status": "scored",
                "result": coach_response.to_dict(),
            },
        )
    except Exception as error:
        logger.exception(
            "Validation scoring unavailable for session %s attempt %s",
            session_id,
            attempt_id,
        )
        return validation_store.save_score(
            session_id,
            attempt_id,
            {
                "status": "unavailable",
                "error": str(error),
            },
        )
