from typing import Any

from app.content.data_graph import load_language_session
from app.content.lesson_tabs import (
    lesson_tab_key,
    lesson_tabs_from_ordered_tabs,
    lessons_in_tab_order,
    ordered_lesson_tabs,
)
from app.content.lessons import lessons_from_session


def build_learning_plan(
    *,
    data_dir,
    project_dir,
    language: str,
    scene_set: str,
    order_seed: str | None,
) -> dict[str, Any]:
    """Return the full lesson plan for a learner session.

    This is intentionally small for the MVP: it preserves the existing content
    order rules while giving us one backend boundary to replace with a smarter
    learning engine later.
    """
    session = load_language_session(
        data_dir=data_dir,
        project_dir=project_dir,
        language=language,
    )
    return learning_plan_from_session(session, scene_set=scene_set, order_seed=order_seed)


def learning_plan_from_session(
    session: dict[str, Any],
    *,
    scene_set: str,
    order_seed: str | None,
) -> dict[str, Any]:
    session_config = session["session"]
    tab_key = lesson_tab_key(scene_set)
    ordered_tabs = ordered_lesson_tabs(session_config, tab_key, scene_set, order_seed)
    lessons = lessons_from_session(session, choice_order_seed=order_seed)

    return {
        "plan_version": 1,
        "session_id": learning_plan_session_id(session["language"], scene_set, order_seed),
        "language": session["language"],
        "display_name": session["display_name"],
        "scene_set": scene_set,
        "order_seed": order_seed,
        "lesson_tabs": lesson_tabs_from_ordered_tabs(ordered_tabs),
        "lessons": lessons_in_tab_order(lessons, ordered_tabs),
    }


def learning_plan_session_id(language: str, scene_set: str, order_seed: str | None) -> str:
    seed = order_seed or "default"
    return f"{language}:{scene_set}:{seed}"
