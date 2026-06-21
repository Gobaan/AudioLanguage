from __future__ import annotations

from pathlib import Path
from typing import Any

from app.content.data_graph import load_language_session
from app.content.learning_engine.content_index import indexed_lessons, lesson_with_plan_metadata
from app.content.learning_engine.models import IndexedLesson, PlannedLesson
from app.content.learning_engine.policy import is_anchor_stage
from app.content.learning_engine.selection import same_day_anchor_recall_for, select_session_lessons
from app.content.learning_engine.scheduling import planning_date_or_today
from app.content.learning_engine.state_store import LearningStateStore
from app.content.lesson_tabs import lesson_tab_key, lesson_tabs_from_ordered_tabs, lessons_in_tab_order, ordered_lesson_tabs
from app.content.lessons import lessons_from_session, load_speech_bubble_overrides


def build_learning_plan(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    scene_set: str,
    order_seed: str | None,
    participant_id: str | None = None,
    state_store: LearningStateStore | None = None,
    planning_date: str | None = None,
) -> dict[str, Any]:
    session = load_language_session(
        data_dir=data_dir,
        project_dir=project_dir,
        language=language,
    )
    if participant_id and state_store:
        return adaptive_learning_plan_from_session(
            session,
            data_dir=data_dir,
            scene_set=scene_set,
            order_seed=order_seed,
            participant_id=participant_id,
            state_store=state_store,
            planning_date=planning_date_or_today(planning_date),
        )
    return learning_plan_from_session(
        session,
        data_dir=data_dir,
        scene_set=scene_set,
        order_seed=order_seed,
    )


def build_relearn_target_plan(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    participant_id: str,
    target_id: str,
    state_store: LearningStateStore,
) -> dict[str, Any]:
    session = load_language_session(
        data_dir=data_dir,
        project_dir=project_dir,
        language=language,
    )
    anchor = anchor_plan_for_target(session, data_dir=data_dir, target_id=target_id)
    state_store.delete_target(participant_id, session["language"], target_id)
    recall = same_day_anchor_recall_for(anchor)

    return {
        "targetId": target_id,
        "language": session["language"],
        "display_name": session["display_name"],
        "lesson_tabs": [tab_from_indexed_plan(item) for item in [anchor, recall]],
        "lessons": [lesson_from_plan(item) for item in [anchor, recall]],
    }


def learning_plan_from_session(
    session: dict[str, Any],
    *,
    data_dir: Path | None = None,
    scene_set: str,
    order_seed: str | None,
) -> dict[str, Any]:
    session_config = session["session"]
    tab_key = lesson_tab_key(scene_set)
    ordered_tabs = ordered_lesson_tabs(session_config, tab_key, scene_set, order_seed)
    lessons = lessons_from_session(
        session,
        choice_order_seed=order_seed,
        speech_bubble_overrides=load_speech_bubble_overrides(data_dir) if data_dir else None,
    )

    return {
        "plan_version": 1,
        "session_id": learning_plan_session_id(session["language"], scene_set, order_seed, None),
        "language": session["language"],
        "display_name": session["display_name"],
        "scene_set": scene_set,
        "order_seed": order_seed,
        "lesson_tabs": lesson_tabs_from_ordered_tabs(ordered_tabs),
        "lessons": lessons_in_tab_order(lessons, ordered_tabs),
    }


def adaptive_learning_plan_from_session(
    session: dict[str, Any],
    *,
    data_dir: Path | None = None,
    scene_set: str,
    order_seed: str | None,
    participant_id: str,
    state_store: LearningStateStore,
    planning_date: str,
) -> dict[str, Any]:
    indexed = adaptive_indexed_lessons(session, data_dir=data_dir, scene_set=scene_set, order_seed=order_seed)
    states = state_store.target_states(participant_id, session["language"])
    planned = select_session_lessons(indexed, states, planning_date=planning_date)

    return {
        "plan_version": 2,
        "session_id": learning_plan_session_id(session["language"], scene_set, order_seed, participant_id),
        "participant_id": participant_id,
        "language": session["language"],
        "display_name": session["display_name"],
        "scene_set": scene_set,
        "order_seed": order_seed,
        "lesson_tabs": [tab_from_indexed_plan(item) for item in planned],
        "lessons": [lesson_from_plan(item) for item in planned],
    }


def first_new_or_empty(indexed: list[IndexedLesson]) -> list[PlannedLesson]:
    if not indexed:
        return []
    first = indexed[0]
    return [PlannedLesson(first.tab, first.lesson, "new", "new")]


def anchor_plan_for_target(
    session: dict[str, Any],
    *,
    data_dir: Path | None,
    target_id: str,
) -> PlannedLesson:
    for indexed in indexed_lessons(session, data_dir=data_dir, scene_set="mvp", order_seed=None):
        if indexed.target_id == target_id and is_anchor_stage(indexed.stage):
            return PlannedLesson(
                indexed.tab,
                indexed.lesson,
                "new",
                "new",
                lesson_unit_id=target_id,
            )
    raise ValueError(f"No anchor lesson found for target '{target_id}'")


def adaptive_indexed_lessons(
    session: dict[str, Any],
    *,
    data_dir: Path | None = None,
    scene_set: str,
    order_seed: str | None,
) -> list[IndexedLesson]:
    indexed = indexed_lessons(session, data_dir=data_dir, scene_set=scene_set, order_seed=order_seed)
    if scene_set not in {"delayed", "delayed_review"}:
        indexed.extend(indexed_lessons(session, data_dir=data_dir, scene_set="delayed", order_seed=order_seed))
    return indexed


def tab_from_indexed_plan(item: PlannedLesson) -> dict[str, str]:
    tab_id = str(item.tab.get("id", ""))
    return {"id": tab_id, "label": str(item.tab.get("label", tab_id))}


def lesson_from_plan(item: PlannedLesson) -> dict[str, Any]:
    return lesson_with_plan_metadata(
        item.lesson,
        plan_purpose=item.purpose,
        repair_category=item.repair_category,
        lesson_unit_id=item.lesson_unit_id,
    )


def learning_plan_session_id(
    language: str,
    scene_set: str,
    order_seed: str | None,
    participant_id: str | None,
) -> str:
    seed = order_seed or "default"
    if participant_id:
        return f"{participant_id}:{language}:{scene_set}:{seed}"
    return f"{language}:{scene_set}:{seed}"
