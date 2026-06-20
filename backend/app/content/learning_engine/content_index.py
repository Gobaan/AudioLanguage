from __future__ import annotations

from pathlib import Path
from typing import Any

from app.content.learning_engine.models import IndexedLesson
from app.content.lesson_tabs import lesson_tab_key, ordered_lesson_tabs
from app.content.lessons import lessons_from_session, load_speech_bubble_overrides


def indexed_lessons(
    session: dict[str, Any],
    *,
    data_dir: Path | None = None,
    scene_set: str,
    order_seed: str | None,
) -> list[IndexedLesson]:
    session_config = session["session"]
    tab_key = lesson_tab_key(scene_set)
    ordered_tabs = ordered_lesson_tabs(session_config, tab_key, scene_set, order_seed)
    lessons = lessons_from_session(
        session,
        choice_order_seed=order_seed,
        speech_bubble_overrides=load_speech_bubble_overrides(data_dir) if data_dir else None,
    )
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
    lesson_unit_id: str = "",
) -> dict[str, Any]:
    planned_lesson = (
        same_day_anchor_recall_lesson(lesson)
        if plan_purpose == "same_day_anchor_recall"
        else dict(lesson)
    )
    planned_lesson["targetId"] = str(lesson.get("target", {}).get("id", ""))
    planned_lesson["planPurpose"] = plan_purpose
    planned_lesson["sceneSet"] = planned_lesson.get("sceneSet") or stage_scene_set(str(lesson.get("stage", "")))
    if lesson_unit_id:
        planned_lesson["lessonUnitId"] = lesson_unit_id
    if repair_category:
        planned_lesson["repairCategory"] = repair_category
    return planned_lesson


def tab_from_indexed(indexed: IndexedLesson) -> dict:
    return {"id": str(indexed.tab.get("id")), "label": str(indexed.tab.get("label", indexed.tab.get("id")))}


def stage_scene_set(stage: str) -> str:
    if stage == "delayed_review":
        return "delayed"
    return "mvp"


def same_day_anchor_recall_lesson(lesson: dict[str, Any]) -> dict[str, Any]:
    recalled = dict(lesson)
    recalled["id"] = f"{lesson.get('id')}-same_day_anchor_recall"
    recalled["stage"] = "same_day_anchor_recall"
    recalled["steps"] = same_day_anchor_recall_steps(lesson)
    return recalled


def same_day_anchor_recall_steps(lesson: dict[str, Any]) -> list[dict[str, Any]]:
    from app.content.lesson_steps import audio_behavior, mic_off, recording_mic, step

    frames = lesson.get("frames", [])
    if not isinstance(frames, list):
        frames = []
    opener_frame = frame_for_line_type(frames, "world_opener") or first_frame(frames)
    learner_frame = frame_for_line_type(frames, "learner_target")
    playback_flow = anchor_recall_playback_flow(frames)
    expected_text, expected_transliteration = expected_phrase_for_recall(lesson, learner_frame)

    return [
        step(
            "scene_setup",
            "SceneFrame",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="Listen.",
            audio=audio_behavior(
                opener_frame.get("audioUrl") if opener_frame else None,
                autoplay=True,
                replayable=True,
                audio_text=opener_frame.get("audioText") if opener_frame else None,
            ),
            mic=mic_off(),
            props={
                "initialFrameId": opener_frame.get("id") if opener_frame else None,
                "frames": frames,
                "stopAtLineType": "world_opener",
                "playbackFlow": playback_flow,
            },
        ),
        step(
            "scene_recall",
            "ProductionPrompt",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="What would you say?",
            audio=audio_behavior(None, autoplay=False, replayable=False, play_before_mic=False),
            mic=recording_mic(expected_text, expected_transliteration, starts_after_audio=False),
            props={
                "playbackFlow": playback_flow,
                "recordBeforeModelLine": True,
                "playModelLineAfterAttempt": True,
                "playWorldResponseAfterAttempt": has_playback_line(playback_flow, "world_response"),
                "showDialogueRevealAfterAttempt": False,
            },
        ),
    ]


def anchor_recall_playback_flow(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flow: list[dict[str, Any]] = []
    opener = frame_for_line_type(frames, "world_opener")
    learner = frame_for_line_type(frames, "learner_target")
    response = frame_for_line_type(frames, "world_response")
    if opener:
        flow.append(play_line_for_frame(opener, "world_opener"))
    flow.append({"type": "record_attempt"})
    if learner:
        flow.append(play_line_for_frame(learner, "learner_target"))
    if response:
        flow.append(play_line_for_frame(response, "world_response"))
    return flow


def play_line_for_frame(frame: dict[str, Any], line_type: str) -> dict[str, Any]:
    item: dict[str, Any] = {"type": "play_line", "line_type": line_type}
    if frame.get("id") is not None:
        item["frame_id"] = frame.get("id")
    if frame.get("lineIndex") is not None:
        item["line_index"] = frame.get("lineIndex")
    return item


def has_playback_line(playback_flow: list[dict[str, Any]], line_type: str) -> bool:
    return any(item.get("type") == "play_line" and item.get("line_type") == line_type for item in playback_flow)


def expected_phrase_for_recall(
    lesson: dict[str, Any],
    learner_frame: dict[str, Any] | None,
) -> tuple[str, str]:
    target = lesson.get("target", {}) if isinstance(lesson.get("target"), dict) else {}
    expected_text = str(
        (learner_frame or {}).get("originalText")
        or (learner_frame or {}).get("text")
        or target.get("text", "")
    )
    expected_transliteration = str(
        (learner_frame or {}).get("transliteration")
        or target.get("transliteration", "")
    )
    return expected_text, expected_transliteration


def first_frame(frames: list[dict[str, Any]]) -> dict[str, Any] | None:
    return frames[0] if frames else None


def frame_for_line_type(frames: list[dict[str, Any]], line_type: str) -> dict[str, Any] | None:
    for frame in frames:
        if isinstance(frame, dict) and frame.get("lineType") == line_type:
            return frame
    return None
