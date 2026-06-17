from __future__ import annotations

from typing import Any

from app.content.learning_engine.models import IndexedLesson
from app.content.lesson_tabs import lesson_tab_key, ordered_lesson_tabs
from app.content.lessons import lessons_from_session


def indexed_lessons(
    session: dict[str, Any],
    *,
    scene_set: str,
    order_seed: str | None,
) -> list[IndexedLesson]:
    session_config = session["session"]
    tab_key = lesson_tab_key(scene_set)
    ordered_tabs = ordered_lesson_tabs(session_config, tab_key, scene_set, order_seed)
    lessons = lessons_from_session(session, choice_order_seed=order_seed)
    lessons_by_id = {str(lesson.get("id")): lesson for lesson in lessons if lesson.get("id")}
    indexed = []
    for tab in ordered_tabs:
        lesson = lessons_by_id.get(str(tab.get("card_id", "")))
        if not lesson:
            continue
        indexed.append(
            IndexedLesson(
                tab=tab,
                lesson=lesson,
                target_id=str(lesson.get("target", {}).get("id", "")),
                stage=str(lesson.get("stage", "")),
            )
        )
    return indexed


def lesson_with_plan_metadata(
    lesson: dict[str, Any],
    *,
    plan_purpose: str,
    repair_category: str | None,
) -> dict[str, Any]:
    planned_lesson = dict(lesson)
    planned_lesson["targetId"] = str(lesson.get("target", {}).get("id", ""))
    planned_lesson["planPurpose"] = plan_purpose
    planned_lesson["sceneSet"] = planned_lesson.get("sceneSet") or stage_scene_set(str(lesson.get("stage", "")))
    if repair_category:
        planned_lesson["repairCategory"] = repair_category
    return planned_lesson


def tab_from_indexed(indexed: IndexedLesson) -> dict:
    return {"id": str(indexed.tab.get("id")), "label": str(indexed.tab.get("label", indexed.tab.get("id")))}


def stage_scene_set(stage: str) -> str:
    if stage == "delayed_review":
        return "delayed"
    return "mvp"
