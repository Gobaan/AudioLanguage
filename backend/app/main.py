from pathlib import Path
import json
import random
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.conversation.factory import create_conversation_coach
from app.conversation.models import ConversationContext, LearnerAttempt
from app.content.data_graph import DataGraphError, list_languages, load_distractors, load_language_session
from app.content.lessons import lessons_from_session
from app.content.loader import load_content_graph
from app.speech.language import romanize_for_language
from app.speech.similarity import normalize_for_match, text_similarity
from app.scenes import scenes
from app.validation import ValidationStore
from project_config.paths import repo_paths

BASE_DIR = Path(__file__).resolve().parent.parent
PATHS = repo_paths()
PROJECT_DIR = PATHS.root
STATIC_DIR = PATHS.static_dir
AUDIO_DIR = PATHS.audio_dir
VISUALS_DIR = PATHS.visuals_dir
AUDIO_SOURCES_DIR = PATHS.audio_sources_dir
DATA_DIR = PATHS.content_dir
DIALOGUES_PATH = AUDIO_SOURCES_DIR / "dialogues.json"
PROMPTS_PATH = AUDIO_SOURCES_DIR / "prompts.json"
VALIDATION_DIR = PATHS.model_dir / "validation"

conversation_coach = create_conversation_coach()
validation_store = ValidationStore(VALIDATION_DIR)


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

app = FastAPI(title="Audio Language")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_browser_cache(request, call_next):
    """Keep phone testing honest while assets and scenes are changing quickly."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/visuals", StaticFiles(directory=str(VISUALS_DIR)), name="visuals")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/admin/validation")
def validation_admin():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/scenes")
def list_scenes():
    """Return all available scenes."""
    return scenes


@app.get("/api/scenes/{scene_id}")
def get_scene(scene_id: str):
    """Return a single scene by id."""
    for scene in scenes:
        if scene.id == scene_id:
            return scene
    raise HTTPException(status_code=404, detail=f"Scene '{scene_id}' not found")


@app.get("/api/dialogues")
def list_dialogues():
    """Return dialogue card metadata from audio_sources/dialogues.json."""
    return [dialogue.model_dump() for dialogue in load_content_graph(DIALOGUES_PATH).dialogues]


@app.get("/api/prompts")
def list_prompts():
    """Return available spoken prompt keys."""
    with PROMPTS_PATH.open(encoding="utf-8") as file:
        return json.load(file)


@app.get("/api/languages")
def get_languages():
    """Return languages available in the structured content graph."""
    return list_languages(DATA_DIR)


@app.get("/api/languages/{language}/session")
def get_language_session(language: str):
    """Return a hydrated MVP practice session for one language."""
    try:
        return load_language_session(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=language,
        )
    except DataGraphError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/languages/{language}/lessons")
def get_language_lessons(
    language: str,
    lesson: str | None = Query(default=None),
    scene_set: str = Query(default="mvp"),
    order_seed: str | None = Query(default=None),
):
    """Return frontend-renderable lessons for one language."""
    try:
        session = load_language_session(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=language,
        )
    except DataGraphError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    lessons = lessons_from_session(session)
    session_config = session["session"]
    tab_key = lesson_tab_key(scene_set)
    ordered_tabs = ordered_lesson_tabs(session_config, tab_key, scene_set, order_seed)
    if lesson:
        lessons = selected_lessons(lessons, lesson, session_config, tab_key)
        if not lessons:
            raise HTTPException(status_code=404, detail=f"Lesson '{lesson}' not found")
    else:
        lessons = lessons_in_tab_order(lessons, ordered_tabs)

    return {
        "language": session["language"],
        "display_name": session["display_name"],
        "scene_set": scene_set,
        "lesson_tabs": lesson_tabs_from_ordered_tabs(ordered_tabs),
        "lessons": lessons,
    }


def lesson_tab_key(scene_set: str) -> str:
    return "delayed_lesson_tabs" if scene_set in {"delayed", "delayed_review"} else "lesson_tabs"


def lesson_tabs_from_session(session_config: dict, tab_key: str = "lesson_tabs") -> list[dict[str, str]]:
    return lesson_tabs_from_ordered_tabs(raw_lesson_tabs(session_config, tab_key))


def raw_lesson_tabs(session_config: dict, tab_key: str = "lesson_tabs") -> list[dict]:
    tabs = session_config.get(tab_key, [])
    if not isinstance(tabs, list):
        return []

    return [tab for tab in tabs if isinstance(tab, dict)]


def lesson_tabs_from_ordered_tabs(tabs: list[dict]) -> list[dict[str, str]]:
    lesson_tabs = []
    for tab in tabs:
        tab_id = tab.get("id")
        label = tab.get("label", tab_id)
        if tab_id and label:
            lesson_tabs.append({"id": str(tab_id), "label": str(label)})

    return lesson_tabs


def ordered_lesson_tabs(
    session_config: dict,
    tab_key: str,
    scene_set: str,
    order_seed: str | None = None,
) -> list[dict]:
    tabs = raw_lesson_tabs(session_config, tab_key)
    if tab_key == "delayed_lesson_tabs" or scene_set in {"delayed", "delayed_review"}:
        return shuffled_tabs(tabs, order_seed, "delayed")

    anchors = [tab for tab in tabs if not is_transfer_tab(tab)]
    transfers = [tab for tab in tabs if is_transfer_tab(tab)]
    return anchors + shuffled_tabs(transfers, order_seed, "transfer")


def shuffled_tabs(tabs: list[dict], order_seed: str | None, namespace: str) -> list[dict]:
    shuffled = list(tabs)
    if len(shuffled) < 2:
        return shuffled

    if order_seed is None:
        random.SystemRandom().shuffle(shuffled)
    else:
        random.Random(f"{namespace}:{order_seed}").shuffle(shuffled)
    return shuffled


def is_transfer_tab(tab: dict) -> bool:
    tab_id = str(tab.get("id", ""))
    card_id = str(tab.get("card_id", ""))
    return tab_id.endswith("-transfer") or "same_day_transfer" in card_id


def lessons_in_tab_order(lessons: list[dict], tabs: list[dict]) -> list[dict]:
    lessons_by_id = {str(item.get("id")): item for item in lessons if item.get("id")}
    ordered_lessons = []
    for tab in tabs:
        card_id = tab.get("card_id")
        if card_id and str(card_id) in lessons_by_id:
            ordered_lessons.append(lessons_by_id[str(card_id)])

    return ordered_lessons or lessons


def selected_lessons(lessons: list[dict], lesson: str, session_config: dict, tab_key: str = "lesson_tabs") -> list[dict]:
    lesson_aliases = lesson_aliases_from_session(session_config, tab_key)
    lesson_id = lesson_aliases.get(lesson, lesson)
    return [item for item in lessons if item.get("id") == lesson_id]


def lesson_aliases_from_session(session_config: dict, tab_key: str = "lesson_tabs") -> dict[str, str]:
    tabs = session_config.get(tab_key, [])
    if not isinstance(tabs, list):
        return {}

    aliases = {}
    for tab in tabs:
        if not isinstance(tab, dict):
            continue

        tab_id = tab.get("id")
        card_id = tab.get("card_id")
        if tab_id and card_id:
            aliases[str(tab_id)] = str(card_id)

    return aliases


@app.get("/api/languages/{language}/distractors")
def get_language_distractors(language: str):
    """Return broad-meaning distractor sets available to one language."""
    language_dir = DATA_DIR / "languages" / language
    if not language_dir.exists():
        raise HTTPException(status_code=404, detail=f"Language '{language}' not found")

    distractors = list(load_distractors(DATA_DIR, language_dir).values())
    return {
        "language": language,
        "dialogue_distractors": distractors,
        "meaning_distractors": distractors,
    }


@app.post("/api/validation/sessions")
def start_validation_session(request: ValidationSessionRequest):
    """Create a local validation session for workflow events and recordings."""
    try:
        return validation_store.create_session(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/validation/sessions/{session_id}/events")
def log_validation_event(session_id: str, request: ValidationEventRequest):
    """Append one local validation event to the session event log."""
    try:
        return validation_store.append_event(session_id, request.model_dump(exclude_none=True))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/validation/sessions/{session_id}/attempts")
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


@app.get("/api/validation/sessions/{session_id}/scorecard")
def get_validation_scorecard(session_id: str, score: bool = Query(default=False)):
    """Return a local scorecard skeleton for manual or AI review."""
    try:
        if score:
            score_validation_attempts(session_id)
        return validation_store.scorecard(session_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error


@app.get("/api/validation/sessions/{session_id}/attempts/{attempt_id}/audio")
def get_validation_attempt_audio(session_id: str, attempt_id: str):
    """Return one saved local learner recording for scorecard review."""
    try:
        return FileResponse(str(validation_store.attempt_audio_path(session_id, attempt_id)))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Attempt '{attempt_id}' not found") from error


@app.get("/api/validation/admin/summary")
def get_validation_admin_summary():
    """Return a local validation rollup across participants, languages, and review days."""
    return validation_store.admin_summary()


@app.get("/api/validation/participant-name")
def get_validation_participant_name():
    """Return a human-readable participant id that has not appeared in saved sessions."""
    return validation_store.suggest_participant_name()


@app.delete("/api/validation/sessions/{session_id}")
def delete_validation_session(session_id: str):
    """Delete one validation session and its saved recordings."""
    try:
        return validation_store.delete_session(session_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def score_validation_attempts(session_id: str) -> None:
    """Score unscored local recordings when the scorecard is opened."""
    for attempt in validation_store.attempts_needing_score(session_id):
        attempt_id = str(attempt.get("attemptId", ""))
        if not attempt_id:
            continue
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
            validation_store.save_score(
                session_id,
                attempt_id,
                {
                    "status": "scored",
                    "result": coach_response.to_dict(),
                },
            )
        except Exception as error:
            validation_store.save_score(
                session_id,
                attempt_id,
                {
                    "status": "unavailable",
                    "error": str(error),
                },
            )


@app.post("/api/transcribe")
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


@app.post("/api/conversation/attempt")
async def evaluate_conversation_attempt(
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
