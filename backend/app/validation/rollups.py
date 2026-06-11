from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.validation.jsonl_io import read_jsonl
from app.validation.scoring import is_remembered_score, participant_id_from, score_status


def build_scorecard(
    session_dir: Path,
    scores_by_attempt: Callable[[Path], dict[str, dict[str, Any]]],
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

    return {
        "session": metadata,
        "eventCount": len(events),
        "attemptCount": len(attempts),
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
