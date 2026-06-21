import json
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.content.data_graph import DataGraphError, list_languages, load_distractors, load_language_session
from app.content.learning_engine import build_learning_plan, build_relearn_target_plan
from app.content.lesson_tabs import (
    lesson_tab_key,
    lesson_tabs_from_ordered_tabs,
    lessons_in_tab_order,
    ordered_lesson_tabs,
    selected_lessons,
)
from app.content.lessons import lessons_from_session, load_speech_bubble_overrides
from app.runtime import DATA_DIR, PROJECT_DIR, validation_store

router = APIRouter()

LanguagePath = Annotated[str, Path(pattern=r"^[a-z]{2,3}(-[a-z]+)?$")]
LanguageQuery = Annotated[str, Query(pattern=r"^[a-z]{2,3}(-[a-z]+)?$")]


class SpeechBubbleOverride(BaseModel):
    lessonId: str
    frameId: str
    lineIndex: int
    imageUrl: str | None = None
    kind: str = Field(pattern=r"^(mic|speaker)$")
    anchorX: float = Field(ge=0, le=1)
    anchorY: float = Field(ge=0, le=1)
    rotationDegrees: float
    side: str = "bottom"
    tipPosition: str = Field(default="center", pattern=r"^(left|center|right)$")
    tipTilt: str = Field(default="none", pattern=r"^(left|none|right)$")


class SpeechBubbleOverridesPayload(BaseModel):
    language: str
    sceneSet: str
    bubbleScale: float = Field(gt=0, le=4)
    editorFrameWidth: int | None = None
    frames: list[SpeechBubbleOverride]


class RelearnTargetRequest(BaseModel):
    language: str = Field(pattern=r"^[a-z]{2,3}(-[a-z]+)?$")
    participantId: str = Field(min_length=1)
    targetId: str = Field(min_length=1)


@router.get("/api/languages")
def get_languages():
    """Return languages available in the structured content graph."""
    return list_languages(DATA_DIR)


@router.get("/api/debug/speech-bubble-overrides")
def get_speech_bubble_overrides() -> dict[str, Any]:
    path = DATA_DIR / "speech_bubble_overrides.json"
    if not path.exists():
        return {"language": "ja", "sceneSet": "mvp", "bubbleScale": 0.72, "frames": []}
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/api/debug/speech-bubble-overrides")
def save_speech_bubble_overrides(payload: SpeechBubbleOverridesPayload):
    path = DATA_DIR / "speech_bubble_overrides.json"
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    try:
        display_path = str(path.relative_to(PROJECT_DIR))
    except ValueError:
        display_path = str(path)
    return {"saved": True, "path": display_path, "frames": len(payload.frames)}


@router.get("/api/languages/{language}/session")
def get_language_session(language: LanguagePath):
    """Return a hydrated MVP practice session for one language."""
    try:
        return load_language_session(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=language,
        )
    except DataGraphError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/api/languages/{language}/lessons")
def get_language_lessons(
    language: LanguagePath,
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

    lessons = lessons_from_session(
        session,
        choice_order_seed=order_seed,
        speech_bubble_overrides=load_speech_bubble_overrides(DATA_DIR),
    )
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


@router.get("/api/learning-engine/lessons")
def get_learning_engine_lessons(
    language: LanguageQuery,
    scene_set: str = Query(default="mvp"),
    order_seed: str | None = Query(default=None),
    participant_id: str | None = Query(default=None),
):
    """Return the full ordered lesson plan for the current MVP learning engine."""
    try:
        return build_learning_plan(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=language,
            scene_set=scene_set,
            order_seed=order_seed,
            participant_id=participant_id,
            state_store=validation_store.learning_state,
        )
    except DataGraphError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/api/learning-engine/relearn-target")
def relearn_target(request: RelearnTargetRequest):
    """Reset one target's scheduler state and return an anchor relearn bundle."""
    try:
        return build_relearn_target_plan(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=request.language,
            participant_id=request.participantId,
            target_id=request.targetId,
            state_store=validation_store.learning_state,
        )
    except DataGraphError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/api/languages/{language}/distractors")
def get_language_distractors(language: LanguagePath):
    """Return broad-meaning distractor sets available to one language."""
    try:
        distractors = list(load_distractors(DATA_DIR, DATA_DIR / "languages" / language).values())
    except DataGraphError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return {
        "language": language,
        "dialogue_distractors": distractors,
        "meaning_distractors": distractors,
    }
