from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.content.data_graph import DataGraphError, load_language_session
from app.content.learner_audio import learner_dialogue_audio_url
from app.validation.jsonl_io import read_jsonl
from app.validation.scoring import is_remembered_score, participant_id_from, score_status

SCENE_KIND_LABELS = {
    "anchor": "Anchor",
    "transfer": "Transfer",
    "delayed": "Delayed",
}

TRY_KIND_LABELS = {
    "anchor": "Anchor",
    "anchor_transfer": "Anchor transfer",
    "transfer": "Transfer",
}


def filter_scorecard_attempts(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the final backward-build recording per lesson; drop practice chunks."""
    kept: list[dict[str, Any]] = []
    backward_by_lesson: dict[str, dict[str, Any]] = {}

    for attempt in attempts:
        if attempt.get("stepId") != "backward_build":
            kept.append(attempt)
            continue

        lesson_id = str(attempt.get("lessonId") or attempt.get("attemptId") or "unknown")
        current = backward_by_lesson.get(lesson_id)
        if current is None or str(attempt.get("receivedAt") or "") >= str(current.get("receivedAt") or ""):
            backward_by_lesson[lesson_id] = attempt

    kept.extend(backward_by_lesson.values())
    return kept


def learner_line_for_attempts(attempts: list[dict[str, Any]]) -> str:
    candidates: list[str] = []
    for attempt in attempts:
        for key in ("expectedTransliteration", "expectedText"):
            value = str(attempt.get(key) or "").strip()
            if value:
                candidates.append(value)
    if not candidates:
        return ""
    return max(candidates, key=len)


def learner_audio_for_attempts(attempts: list[dict[str, Any]]) -> str | None:
    candidates: list[tuple[int, int, str]] = []
    for attempt in attempts:
        audio_url = attempt.get("targetAudioUrl")
        if not isinstance(audio_url, str) or not audio_url.strip():
            continue
        line = str(attempt.get("expectedTransliteration") or attempt.get("expectedText") or "").strip()
        is_backward_build = "/backward-build/" in audio_url
        candidates.append((0 if is_backward_build else 1, len(line), audio_url.strip()))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def is_backward_build_audio_url(url: str | None) -> bool:
    return isinstance(url, str) and "/backward-build/" in url


def build_scorecard(
    session_dir: Path,
    scores_by_attempt: Callable[[Path], dict[str, dict[str, Any]]],
    *,
    data_dir: Path | None = None,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
    attempts = read_jsonl(session_dir / "attempts.jsonl")
    events = read_jsonl(session_dir / "events.jsonl")
    scores = scores_by_attempt(session_dir)
    language = str(metadata.get("language") or "")
    anchor_metadata = anchor_metadata_by_target(
        data_dir=data_dir,
        project_dir=project_dir,
        language=language,
    )
    targets: dict[str, dict[str, Any]] = {}

    for attempt in attempts:
        attempt = {
            **attempt,
            "aiScore": scores.get(str(attempt.get("attemptId"))),
        }
        target_id = str(attempt.get("targetId") or "unknown")
        target = targets.setdefault(
            target_id,
            {
                "targetId": target_id,
                **anchor_metadata.get(target_id, {}),
                "expectedText": attempt.get("expectedText"),
                "expectedTransliteration": attempt.get("expectedTransliteration"),
                "targetAudioUrl": attempt.get("targetAudioUrl"),
                "attempts": [],
                "reviewStatus": "needs_review",
            },
        )
        target["attempts"].append(attempt)

    for target in targets.values():
        target["attempts"] = filter_scorecard_attempts(target["attempts"])
        learner_line = learner_line_for_attempts(target["attempts"])
        if learner_line:
            target["learnerLine"] = learner_line
            target["expectedTransliteration"] = learner_line
        learner_audio = learner_audio_for_attempts(target["attempts"])
        if learner_audio and is_backward_build_audio_url(learner_audio) and data_dir and project_dir:
            language = str(metadata.get("language") or target["attempts"][0].get("language") or "")
            resolved = learner_dialogue_audio_url(
                language=language,
                target_id=str(target["targetId"]),
                data_dir=data_dir,
                project_dir=project_dir,
            )
            if resolved:
                learner_audio = resolved
        elif not learner_audio and data_dir and project_dir and target["attempts"]:
            language = str(metadata.get("language") or target["attempts"][0].get("language") or "")
            learner_audio = learner_dialogue_audio_url(
                language=language,
                target_id=str(target["targetId"]),
                data_dir=data_dir,
                project_dir=project_dir,
            )
        if learner_audio:
            target["targetAudioUrl"] = learner_audio

    return {
        "session": metadata,
        "eventCount": len(events),
        "attemptCount": sum(len(target["attempts"]) for target in targets.values()),
        "targets": list(targets.values()),
    }


def anchor_metadata_by_target(
    *,
    data_dir: Path | None,
    project_dir: Path | None,
    language: str,
) -> dict[str, dict[str, str]]:
    if not data_dir or not project_dir or not language:
        return {}

    try:
        session = load_language_session(data_dir=data_dir, project_dir=project_dir, language=language)
    except DataGraphError:
        return {}

    tabs_by_card_id = {
        str(tab.get("card_id")): str(tab.get("id"))
        for tab in session.get("session", {}).get("lesson_tabs", [])
        if isinstance(tab, dict) and tab.get("card_id") and tab.get("id")
    }
    metadata: dict[str, dict[str, str]] = {}
    for card in session.get("cards", []):
        if not isinstance(card, dict) or card.get("stage") != "guided_scene_production":
            continue
        target = card.get("target") if isinstance(card.get("target"), dict) else {}
        target_id = str(card.get("target_id") or target.get("id") or "")
        card_id = str(card.get("id") or "")
        lesson_page = tabs_by_card_id.get(card_id)
        if target_id and card_id and lesson_page:
            metadata[target_id] = {
                "anchorLessonId": card_id,
                "anchorLessonPage": lesson_page,
            }
    return metadata


def build_admin_summary(
    root: Path,
    scores_by_attempt: Callable[[Path], dict[str, dict[str, Any]]],
    *,
    participant_id: str | None = None,
) -> dict[str, Any]:
    sessions = []
    targets: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for session_dir in sorted((root / "sessions").glob("*")):
        metadata_path = session_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        attempts = read_jsonl(session_dir / "attempts.jsonl")
        events = read_jsonl(session_dir / "events.jsonl")
        scores = scores_by_attempt(session_dir)
        session_participant_id = participant_id_from(metadata, attempts, events)
        if participant_id and session_participant_id != participant_id:
            continue

        language = str(metadata.get("language") or "unknown")
        scene_set = str(metadata.get("sceneSet") or "unknown")

        session_summary = {
            "sessionId": metadata.get("sessionId"),
            "participantId": session_participant_id,
            "clientIp": metadata.get("clientIp"),
            "locationFlag": metadata.get("locationFlag"),
            "language": language,
            "sceneSet": scene_set,
            "lessonPage": metadata.get("lessonPage"),
            "createdAt": metadata.get("createdAt"),
            "eventCount": len(events),
            "attemptCount": len(attempts),
            "scoredAttemptCount": sum(1 for attempt in attempts if str(attempt.get("attemptId")) in scores),
            "rememberedAttemptCount": sum(1 for attempt in attempts if is_remembered_score(scores.get(str(attempt.get("attemptId"))))),
        }
        sessions.append(session_summary)

        for attempt in attempts:
            target_id = str(attempt.get("targetId") or "unknown")
            scene_kind = scene_kind_for_record(attempt, metadata)
            try_kind = try_kind_for_record(attempt, metadata)
            key = (language, scene_set, scene_kind, target_id)
            target = targets.setdefault(
                key,
                {
                    "language": language,
                    "sceneSet": scene_set,
                    "sceneKind": scene_kind,
                    "sceneKindLabel": SCENE_KIND_LABELS[scene_kind],
                    "targetId": target_id,
                    "expectedText": attempt.get("expectedText"),
                    "expectedTransliteration": attempt.get("expectedTransliteration"),
                    "targetAudioUrl": attempt.get("targetAudioUrl"),
                    "attemptCount": 0,
                    "scoredAttemptCount": 0,
                    "rememberedAttemptCount": 0,
                    "sessions": [],
                },
            )
            score = scores.get(str(attempt.get("attemptId")))
            target["attemptCount"] += 1
            target["scoredAttemptCount"] += 1 if score else 0
            target["rememberedAttemptCount"] += 1 if is_remembered_score(score) else 0
            target["sessions"].append(
                {
                    "type": "recording",
                    "sessionId": metadata.get("sessionId"),
                    "participantId": session_participant_id,
                    "language": language,
                    "sceneSet": scene_set,
                    "sceneKind": scene_kind,
                    "sceneKindLabel": SCENE_KIND_LABELS[scene_kind],
                    "tryKind": try_kind,
                    "tryKindLabel": TRY_KIND_LABELS[try_kind],
                    "lessonId": attempt.get("lessonId"),
                    "lessonPage": attempt.get("lessonPage") or metadata.get("lessonPage"),
                    "lessonStage": attempt.get("lessonStage"),
                    "planPurpose": attempt.get("planPurpose"),
                    "stepId": attempt.get("stepId"),
                    "attemptId": attempt.get("attemptId"),
                    "receivedAt": attempt.get("receivedAt"),
                    "createdAt": metadata.get("createdAt"),
                    "scorePassed": is_remembered_score(score),
                    "scoreStatus": score_status(score),
                }
            )

        for event in events:
            if event.get("type") != "choice_selected" or not event.get("targetId"):
                continue

            target_id = str(event.get("targetId"))
            scene_kind = scene_kind_for_record(event, metadata)
            try_kind = try_kind_for_record(event, metadata)
            key = (language, scene_set, scene_kind, target_id)
            target = targets.setdefault(
                key,
                {
                    "language": language,
                    "sceneSet": scene_set,
                    "sceneKind": scene_kind,
                    "sceneKindLabel": SCENE_KIND_LABELS[scene_kind],
                    "targetId": target_id,
                    "expectedText": None,
                    "expectedTransliteration": None,
                    "targetAudioUrl": None,
                    "attemptCount": 0,
                    "scoredAttemptCount": 0,
                    "rememberedAttemptCount": 0,
                    "sessions": [],
                },
            )
            target["sessions"].append(
                {
                    "type": "choice",
                    "sessionId": metadata.get("sessionId"),
                    "participantId": session_participant_id,
                    "language": language,
                    "sceneSet": scene_set,
                    "sceneKind": scene_kind,
                    "sceneKindLabel": SCENE_KIND_LABELS[scene_kind],
                    "tryKind": try_kind,
                    "tryKindLabel": TRY_KIND_LABELS[try_kind],
                    "lessonId": event.get("lessonId"),
                    "lessonPage": event.get("lessonPage") or metadata.get("lessonPage"),
                    "lessonStage": event.get("lessonStage"),
                    "planPurpose": event.get("planPurpose"),
                    "stepId": event.get("stepId"),
                    "eventId": event.get("eventId"),
                    "choiceId": event.get("choiceId"),
                    "choiceCorrect": event.get("isCorrect"),
                    "receivedAt": event.get("receivedAt") or event.get("timestamp"),
                    "createdAt": metadata.get("createdAt"),
                }
            )

    return {
        "sessionCount": len(sessions),
        "attemptCount": sum(session["attemptCount"] for session in sessions),
        "scoredAttemptCount": sum(session["scoredAttemptCount"] for session in sessions),
        "rememberedAttemptCount": sum(session["rememberedAttemptCount"] for session in sessions),
        "sessions": sessions,
        "targets": list(targets.values()),
    }


def scene_kind_for_record(record: dict[str, Any], metadata: dict[str, Any]) -> str:
    lesson_stage = str(record.get("lessonStage") or "").strip().lower()
    plan_purpose = str(record.get("planPurpose") or "").strip().lower()
    scene_set = str(record.get("sceneSet") or metadata.get("sceneSet") or "").strip().lower()
    lesson_page = str(record.get("lessonPage") or metadata.get("lessonPage") or "").strip().lower()

    if "transfer" in lesson_stage or "transfer" in plan_purpose or "transfer" in lesson_page:
        return "transfer"
    if (
        "delayed" in lesson_stage
        or "delayed" in plan_purpose
        or "delayed" in scene_set
        or "delayed" in lesson_page
        or "memory_repair" in plan_purpose
    ):
        return "delayed"
    return "anchor"


def try_kind_for_record(record: dict[str, Any], metadata: dict[str, Any]) -> str:
    lesson_stage = str(record.get("lessonStage") or "").strip().lower()
    plan_purpose = str(record.get("planPurpose") or "").strip().lower()

    if lesson_stage in {"same_day_anchor_recall", "anchor_transfer"} or plan_purpose == "same_day_anchor_recall":
        return "anchor_transfer"
    if scene_kind_for_record(record, metadata) in {"transfer", "delayed"}:
        return "transfer"
    return "anchor"
