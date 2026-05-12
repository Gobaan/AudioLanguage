from pathlib import Path
import json
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.conversation.factory import create_conversation_coach
from app.conversation.models import ConversationContext, LearnerAttempt
from app.content.data_graph import DataGraphError, list_languages, load_language_session
from app.content.loader import load_content_graph
from app.speech.similarity import normalize_for_match, text_similarity
from app.scenes import scenes

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = PROJECT_DIR / "audio"
VISUALS_DIR = PROJECT_DIR / "visuals"
AUDIO_SOURCES_DIR = PROJECT_DIR / "audio_sources"
DATA_DIR = PROJECT_DIR / "data"
DIALOGUES_PATH = AUDIO_SOURCES_DIR / "dialogues.json"
PROMPTS_PATH = AUDIO_SOURCES_DIR / "prompts.json"

conversation_coach = create_conversation_coach()

app = FastAPI(title="Audio Language")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/visuals", StaticFiles(directory=str(VISUALS_DIR)), name="visuals")


@app.get("/")
def index():
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
    communication = response["communication"]
    return {
        **response,
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


def parse_scene_contract(raw_contract: str) -> dict | None:
    if not raw_contract:
        return None
    try:
        parsed = json.loads(raw_contract)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
