from pathlib import Path
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.scenes import scenes

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = PROJECT_DIR / "audio"
DIALOGUES_PATH = PROJECT_DIR / "dialogues.json"
PROMPTS_PATH = PROJECT_DIR / "prompts.json"

app = FastAPI(title="Audio Language")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/scenes")
def list_scenes():
    """Return all available scenes."""
    return scenes


@app.get("/api/dialogues")
def list_dialogues():
    """Return dialogue card metadata from dialogues.json."""
    with DIALOGUES_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    return [
        scene | {"category": category["id"], "category_label": category["label"]}
        for category in data["categories"]
        for scene in category["scenes"]
    ]


@app.get("/api/prompts")
def list_prompts():
    """Return available spoken prompt keys."""
    with PROMPTS_PATH.open(encoding="utf-8") as file:
        return json.load(file)


@app.get("/api/scenes/{scene_id}")
def get_scene(scene_id: str):
    """Return a single scene by id."""
    for scene in scenes:
        if scene.id == scene_id:
            return scene
    return {"error": f"Scene '{scene_id}' not found"}
