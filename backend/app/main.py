from pathlib import Path
from difflib import SequenceMatcher
import json
import re
import tempfile
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.content.data_graph import DataGraphError, list_languages, load_language_session
from app.content.loader import load_content_graph
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
WHISPER_MODEL = None

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


def get_whisper_model():
    """Load the local transcription model once, on first use."""
    global WHISPER_MODEL

    if WHISPER_MODEL is None:
        from faster_whisper import WhisperModel

        WHISPER_MODEL = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    return WHISPER_MODEL


@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    expected: str = Form(""),
):
    """Transcribe a short learner recording."""
    suffix = Path(file.filename or "recording.webm").suffix or ".webm"
    audio_bytes = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(audio_bytes)
        temp_path = Path(temp_file.name)

    try:
        segments, info = get_whisper_model().transcribe(
            str(temp_path),
            language="en",
            vad_filter=True,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        score = text_similarity(transcript, expected)

        return {
            "transcript": transcript,
            "expected": expected,
            "score": score,
            "is_match": bool(expected and score >= 0.72),
            "language": info.language,
            "language_probability": info.language_probability,
        }
    finally:
        temp_path.unlink(missing_ok=True)


def text_similarity(actual: str, expected: str) -> float:
    """Compare learner transcript to target phrase with forgiving punctuation/case."""
    actual_normalized = normalize_for_match(actual)
    expected_normalized = normalize_for_match(expected)

    if not actual_normalized or not expected_normalized:
        return 0.0

    return SequenceMatcher(None, actual_normalized, expected_normalized).ratio()


def normalize_for_match(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


@app.get("/api/scenes/{scene_id}")
def get_scene(scene_id: str):
    """Return a single scene by id."""
    for scene in scenes:
        if scene.id == scene_id:
            return scene
    raise HTTPException(status_code=404, detail=f"Scene '{scene_id}' not found")
