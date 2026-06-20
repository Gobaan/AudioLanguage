from __future__ import annotations

from app.content.learning_engine.classification import repair_category_for_state
from app.content.learning_engine.models import IndexedLesson, PlannedLesson, TargetState
from app.content.learning_engine.policy import REPAIR_PRIORITY, TARGET_SESSION_SIZE, is_anchor_stage, is_delayed_stage, is_transfer_stage
from app.content.learning_engine.scheduling import is_due_for_review


def select_session_lessons(
    indexed_lessons: list[IndexedLesson],
    states: dict[str, TargetState],
    *,
    planning_date: str,
) -> list[PlannedLesson]:
    selected: list[PlannedLesson] = []
    used_targets: set[str] = set()

    repairs = repair_candidates(indexed_lessons, states)
    for candidate in repairs:
        if add_candidate(selected, used_targets, candidate):
            continue

    if len(selected) < TARGET_SESSION_SIZE:
        for candidate in due_transfer_practice_candidates(indexed_lessons, states, planning_date):
            if add_candidate(selected, used_targets, candidate):
                continue

    if len(selected) < TARGET_SESSION_SIZE:
        for candidate in transfer_candidates(indexed_lessons, states):
            if add_candidate(selected, used_targets, candidate):
                continue

    if len(selected) < TARGET_SESSION_SIZE and repair_load_is_light(selected):
        for candidate in new_anchor_candidates(indexed_lessons, states):
            if add_candidate(selected, used_targets, candidate):
                continue

    return selected_with_same_day_anchor_recalls(selected)


def repair_candidates(
    indexed_lessons: list[IndexedLesson],
    states: dict[str, TargetState],
) -> list[PlannedLesson]:
    candidates = []
    for indexed in indexed_lessons:
        state = states.get(indexed.target_id)
        category = repair_category_for_state(state)
        if category not in REPAIR_PRIORITY:
            continue
        if category == "transfer_repair" and not is_transfer_stage(indexed.stage):
            continue
        if category == "memory_repair" and not is_delayed_stage(indexed.stage):
            continue
        if category in {"meaning_repair", "recall_repair"} and not is_anchor_stage(indexed.stage):
            continue
        candidates.append(PlannedLesson(indexed.tab, indexed.lesson, category, category))

    return sorted(candidates, key=lambda item: REPAIR_PRIORITY[str(item.repair_category)])


def due_transfer_practice_candidates(
    indexed_lessons: list[IndexedLesson],
    states: dict[str, TargetState],
    planning_date: str,
) -> list[PlannedLesson]:
    return [
        PlannedLesson(indexed.tab, indexed.lesson, "transfer_practice", None)
        for indexed in indexed_lessons
        if is_delayed_stage(indexed.stage)
        and (state := states.get(indexed.target_id)) is not None
        and (state.anchor_passed or state.transfer_passed)
        and is_due_for_review(state.next_review_at, planning_date, state.last_reviewed_at)
        and not state.failed_delayed
    ]


def new_anchor_candidates(
    indexed_lessons: list[IndexedLesson],
    states: dict[str, TargetState],
) -> list[PlannedLesson]:
    return [
        PlannedLesson(
            indexed.tab,
            indexed.lesson,
            "new",
            "new",
            lesson_unit_id=lesson_unit_id(indexed.lesson),
        )
        for indexed in indexed_lessons
        if is_anchor_stage(indexed.stage) and repair_category_for_state(states.get(indexed.target_id)) == "new"
    ]


def transfer_candidates(
    indexed_lessons: list[IndexedLesson],
    states: dict[str, TargetState],
) -> list[PlannedLesson]:
    return [
        PlannedLesson(indexed.tab, indexed.lesson, "transfer_practice", None)
        for indexed in indexed_lessons
        if is_transfer_stage(indexed.stage)
        and (state := states.get(indexed.target_id)) is not None
        and state.anchor_passed
        and not state.transfer_passed
        and not state.failed_transfer
    ]


def add_candidate(
    selected: list[PlannedLesson],
    used_targets: set[str],
    candidate: PlannedLesson,
) -> bool:
    target_id = str(candidate.lesson.get("target", {}).get("id", ""))
    if not target_id or target_id in used_targets or len(selected) >= TARGET_SESSION_SIZE:
        return False
    selected.append(candidate)
    used_targets.add(target_id)
    return True


def repair_load_is_light(selected: list[PlannedLesson]) -> bool:
    return sum(1 for item in selected if item.repair_category in REPAIR_PRIORITY) < 2


def selected_with_same_day_anchor_recalls(selected: list[PlannedLesson]) -> list[PlannedLesson]:
    anchor_recalls = [
        same_day_anchor_recall_for(item)
        for item in selected
        if item.purpose == "new" and is_anchor_stage(str(item.lesson.get("stage", "")))
    ]
    return selected + anchor_recalls


def same_day_anchor_recall_for(anchor: PlannedLesson) -> PlannedLesson:
    unit_id = anchor.lesson_unit_id or lesson_unit_id(anchor.lesson)
    tab = dict(anchor.tab)
    tab_id = str(tab.get("id") or unit_id)
    tab["id"] = f"{tab_id}-anchor-recall"
    tab["label"] = str(tab.get("label") or tab_id)
    return PlannedLesson(
        tab,
        anchor.lesson,
        "same_day_anchor_recall",
        None,
        lesson_unit_id=unit_id,
    )


def lesson_unit_id(lesson: dict) -> str:
    target_id = str(lesson.get("target", {}).get("id", ""))
    return target_id or str(lesson.get("id", ""))
