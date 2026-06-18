from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.content.learner_audio import learner_dialogue_audio_url
from app.validation.jsonl_io import read_jsonl
from app.validation.scoring import is_remembered_score, participant_id_from, score_status


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


def build_admin_summary(
    root: Path,
    scores_by_attempt: Callable[[Path], dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    sessions = []
    targets: dict[tuple[str, str, str], dict[str, Any]] = {}

    for session_dir in sorted((root / "sessions").glob("*")):
        metadata_path = session_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        attempts = read_jsonl(session_dir / "attempts.jsonl")
        events = read_jsonl(session_dir / "events.jsonl")
        scores = scores_by_attempt(session_dir)
        participant_id = participant_id_from(metadata, attempts, events)
        language = str(metadata.get("language") or "unknown")
        scene_set = str(metadata.get("sceneSet") or "unknown")

        session_summary = {
            "sessionId": metadata.get("sessionId"),
            "participantId": participant_id,
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
            key = (language, scene_set, target_id)
            target = targets.setdefault(
                key,
                {
                    "language": language,
                    "sceneSet": scene_set,
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
                    "participantId": participant_id,
                    "lessonPage": attempt.get("lessonPage") or metadata.get("lessonPage"),
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
            key = (language, scene_set, target_id)
            target = targets.setdefault(
                key,
                {
                    "language": language,
                    "sceneSet": scene_set,
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
                    "participantId": participant_id,
                    "lessonPage": event.get("lessonPage") or metadata.get("lessonPage"),
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
