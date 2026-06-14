from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from app.content.data_graph import DataGraphError, list_languages, load_distractors, load_language_session
from app.content.learning_engine import build_learning_plan
from app.content.lesson_tabs import (
    lesson_tab_key,
    lesson_tabs_from_ordered_tabs,
    lessons_in_tab_order,
    ordered_lesson_tabs,
    selected_lessons,
)
from app.content.lessons import lessons_from_session
from app.runtime import DATA_DIR, PROJECT_DIR

router = APIRouter()

LanguagePath = Annotated[str, Path(pattern=r"^[a-z]{2,3}(-[a-z]+)?$")]
LanguageQuery = Annotated[str, Query(pattern=r"^[a-z]{2,3}(-[a-z]+)?$")]


@router.get("/api/languages")
def get_languages():
    """Return languages available in the structured content graph."""
    return list_languages(DATA_DIR)


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

    lessons = lessons_from_session(session, choice_order_seed=order_seed)
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
):
    """Return the full ordered lesson plan for the current MVP learning engine."""
    try:
        return build_learning_plan(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=language,
            scene_set=scene_set,
            order_seed=order_seed,
        )
    except DataGraphError as error:
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
