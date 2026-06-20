import json
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.conversation.coach import ConversationCoach
from app.conversation.models import ConversationContext, LearnerAttempt
from app.deps import ConversationCoachDep
from app.runtime import DATA_DIR, PROJECT_DIR, validation_store
from app.validation.location import enrich_session_metadata_with_location
from app.validation.scoring import attempt_expected_phrase

logger = logging.getLogger(__name__)

router = APIRouter()

LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1", "testserver", "testclient"}


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


class ScoreOverrideRequest(BaseModel):
    isCorrect: bool


@router.post("/api/validation/sessions")
def start_validation_session(request: ValidationSessionRequest, http_request: Request):
    """Create a local validation session for workflow events and recordings."""
    try:
        metadata = enrich_session_metadata_with_location(request.model_dump(), http_request)
        return validation_store.create_session(metadata)
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
    conversation_coach: ConversationCoachDep,
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
        stored_attempt = validation_store.save_attempt(
            session_id=session_id,
            attempt_id=parsed_metadata.get("attemptId"),
            filename=file.filename,
            content_type=file.content_type,
            audio_bytes=audio_bytes,
            metadata=parsed_metadata,
        )
        attempt_id = str(stored_attempt.get("attemptId") or "")
        if attempt_id:
            pending_attempts = validation_store.attempts_needing_score(session_id)
            if any(str(item.get("attemptId") or "") == attempt_id for item in pending_attempts):
                score_validation_attempt(session_id, stored_attempt, conversation_coach)
        return stored_attempt
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
        return validation_store.scorecard(session_id, data_dir=DATA_DIR, project_dir=PROJECT_DIR)
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


@router.post("/api/validation/sessions/{session_id}/attempts/{attempt_id}/score-override")
def override_validation_attempt_score(
    session_id: str,
    attempt_id: str,
    request: ScoreOverrideRequest,
):
    """Record a learner correction for an automatic score without deleting the original score."""
    try:
        validation_store.attempt_metadata(session_id, attempt_id)
        return validation_store.save_score(
            session_id,
            attempt_id,
            learner_override_score(request.isCorrect),
        )
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


@router.delete("/api/validation/local/sessions")
def delete_all_local_validation_sessions(request: Request):
    """Delete every local validation session for fresh localhost testing."""
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail="Local validation data can only be cleared from localhost")

    return validation_store.delete_all_sessions()


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


def is_local_request(request: Request) -> bool:
    client_host = request.client.host.lower() if request.client else ""
    request_host = (request.url.hostname or "").lower()
    return (
        is_local_hostname(client_host)
        and is_local_hostname(request_host)
        and is_local_header(request.headers.get("origin"))
        and is_local_header(request.headers.get("referer"))
    )


def is_local_header(value: str | None) -> bool:
    if not value:
        return True

    return is_local_hostname((urlparse(value).hostname or "").lower())


def is_local_hostname(value: str) -> bool:
    return value in LOCAL_HOSTNAMES


def score_validation_attempts(session_id: str, conversation_coach: ConversationCoach) -> None:
    """Score unscored local recordings when the scorecard is opened."""
    for attempt in validation_store.attempts_needing_score(session_id):
        score_validation_attempt(session_id, attempt, conversation_coach)


def score_validation_attempt(session_id: str, attempt: dict, conversation_coach: ConversationCoach) -> dict:
    attempt_id = str(attempt.get("attemptId", ""))
    if not attempt_id:
        return {"status": "skipped", "error": "Missing attempt id"}
    try:
        expected_text, expected_transliteration = attempt_expected_phrase(attempt)
        coach_response = conversation_coach.evaluate_attempt(
            attempt=LearnerAttempt(audio_path=validation_store.attempt_audio_path(session_id, attempt_id)),
            context=ConversationContext(
                language=str(attempt.get("language", "")),
                target_id=str(attempt.get("targetId", "")),
                target_text=expected_text,
                target_romanized=expected_transliteration,
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


def learner_override_score(is_correct: bool) -> dict:
    status = "learner_correct" if is_correct else "learner_incorrect"
    return {
        "status": "scored",
        "source": "learner_override",
        "overridesAttemptScore": True,
        "learnerOverride": {
            "isCorrect": is_correct,
        },
        "result": {
            "communication": {
                "status": status,
                "close_enough": is_correct,
                "confidence": 1.0 if is_correct else 0.0,
            },
        },
    }
