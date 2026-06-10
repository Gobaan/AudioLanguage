from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import re
import shutil
import uuid
from typing import Any

logger = logging.getLogger(__name__)


SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
HUMAN_NAMES = [
    "Bob",
    "Alice",
    "Sam",
    "Maya",
    "Leo",
    "Nina",
    "Owen",
    "Riley",
    "Ava",
    "Ben",
    "Zoe",
    "Kai",
    "Mia",
    "Eli",
    "June",
    "Noah",
    "Ivy",
    "Max",
    "Lena",
    "Finn",
]


class ValidationStore:
    def __init__(self, root: Path):
        self.root = root

    def create_session(self, metadata: dict[str, Any]) -> dict[str, Any]:
        session_id = safe_id(str(metadata.get("sessionId") or uuid.uuid4()))
        session_dir = self.session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        session = {
            "sessionId": session_id,
            "createdAt": now_iso(),
            "participantId": metadata.get("participantId") or "local",
            "language": metadata.get("language"),
            "sceneSet": metadata.get("sceneSet"),
            "lessonPage": metadata.get("lessonPage"),
            "source": "local",
        }
        metadata_path = session_dir / "metadata.json"
        if metadata_path.exists():
            return json.loads(metadata_path.read_text(encoding="utf-8"))

        write_json(metadata_path, session)
        return session

    def suggest_participant_name(self) -> dict[str, str]:
        used_names = self.participant_names()
        for name in HUMAN_NAMES:
            if name not in used_names:
                return {"participantId": name}

        suffix = 2
        while True:
            for name in HUMAN_NAMES:
                candidate = f"{name}-{suffix}"
                if candidate not in used_names:
                    return {"participantId": candidate}
            suffix += 1

    def participant_names(self) -> set[str]:
        names = set()
        for session_dir in sorted((self.root / "sessions").glob("*")):
            metadata_path = session_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            participant_id = metadata.get("participantId")
            if participant_id:
                names.add(str(participant_id))
        return names

    def append_event(self, session_id: str, event: dict[str, Any]) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        stored_event = {
            "eventId": event.get("eventId") or str(uuid.uuid4()),
            "receivedAt": now_iso(),
            **event,
        }
        append_jsonl(session_dir / "events.jsonl", stored_event)
        return stored_event

    def save_attempt(
        self,
        *,
        session_id: str,
        attempt_id: str | None,
        filename: str | None,
        content_type: str | None,
        audio_bytes: bytes,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        attempt_id = safe_id(str(attempt_id or metadata.get("attemptId") or uuid.uuid4()))
        attempts_dir = session_dir / "attempts"
        attempts_dir.mkdir(parents=True, exist_ok=True)
        suffix = safe_suffix(filename, content_type)
        recording_path = attempts_dir / f"{attempt_id}{suffix}"

        if not recording_path.exists():
            recording_path.write_bytes(audio_bytes)
            stored_attempt = {
                "attemptId": attempt_id,
                "receivedAt": now_iso(),
                "recordingPath": relative_to_root(recording_path, self.root),
                "contentType": content_type,
                "byteCount": len(audio_bytes),
                **metadata,
            }
            append_jsonl(session_dir / "attempts.jsonl", stored_attempt)
            return stored_attempt

        existing = self.find_attempt(session_dir, attempt_id)
        if existing:
            return existing

        stored_attempt = {
            "attemptId": attempt_id,
            "receivedAt": now_iso(),
            "recordingPath": relative_to_root(recording_path, self.root),
            "contentType": content_type,
            "byteCount": recording_path.stat().st_size,
            **metadata,
        }
        append_jsonl(session_dir / "attempts.jsonl", stored_attempt)
        return stored_attempt

    def scorecard(self, session_id: str) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
        attempts = read_jsonl(session_dir / "attempts.jsonl")
        events = read_jsonl(session_dir / "events.jsonl")
        scores = self.scores_by_attempt(session_dir)
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

    def admin_summary(self) -> dict[str, Any]:
        sessions = []
        targets: dict[tuple[str, str, str], dict[str, Any]] = {}

        for session_dir in sorted((self.root / "sessions").glob("*")):
            metadata_path = session_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            attempts = read_jsonl(session_dir / "attempts.jsonl")
            events = read_jsonl(session_dir / "events.jsonl")
            scores = self.scores_by_attempt(session_dir)
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

    def delete_session(self, session_id: str) -> dict[str, str]:
        session_dir = self.require_session(session_id)
        shutil.rmtree(session_dir)
        return {"sessionId": safe_id(session_id), "status": "deleted"}

    def delete_attempt(self, session_id: str, attempt_id: str) -> dict[str, str]:
        session_dir = self.require_session(session_id)
        attempt_id = safe_id(attempt_id)
        attempt = self.find_attempt(session_dir, attempt_id)
        if not attempt:
            raise FileNotFoundError(attempt_id)

        recording_path = self.root / str(attempt["recordingPath"])
        recording_path.unlink(missing_ok=True)
        attempts = [item for item in read_jsonl(session_dir / "attempts.jsonl") if item.get("attemptId") != attempt_id]
        scores = [item for item in read_jsonl(session_dir / "scores.jsonl") if item.get("attemptId") != attempt_id]
        write_jsonl(session_dir / "attempts.jsonl", attempts)
        write_jsonl(session_dir / "scores.jsonl", scores)
        return {"sessionId": safe_id(session_id), "attemptId": attempt_id, "status": "deleted"}

    def delete_user(self, participant_id: str) -> dict[str, Any]:
        deleted_sessions = []
        for session_dir in sorted((self.root / "sessions").glob("*")):
            metadata_path = session_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            attempts = read_jsonl(session_dir / "attempts.jsonl")
            events = read_jsonl(session_dir / "events.jsonl")
            if participant_id_from(metadata, attempts, events) != participant_id:
                continue

            deleted_sessions.append(str(metadata.get("sessionId") or session_dir.name))
            shutil.rmtree(session_dir)

        return {
            "participantId": participant_id,
            "deletedSessionCount": len(deleted_sessions),
            "deletedSessions": deleted_sessions,
            "status": "deleted",
        }

    def delete_session_data(self, session_id: str, kinds: list[str]) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        deleted = []
        unknown = []

        for kind in kinds:
            if kind == "recordings":
                attempts_dir = session_dir / "attempts"
                if attempts_dir.exists():
                    shutil.rmtree(attempts_dir)
                    deleted.append(kind)
            elif kind == "scores":
                if delete_file(session_dir / "scores.jsonl"):
                    deleted.append(kind)
            elif kind == "events":
                if delete_file(session_dir / "events.jsonl"):
                    deleted.append(kind)
            else:
                unknown.append(kind)

        return {
            "sessionId": safe_id(session_id),
            "deleted": deleted,
            "unknown": unknown,
        }

    def attempts_needing_score(self, session_id: str) -> list[dict[str, Any]]:
        session_dir = self.require_session(session_id)
        scores = self.scores_by_attempt(session_dir)
        return [
            attempt
            for attempt in read_jsonl(session_dir / "attempts.jsonl")
            if str(attempt.get("attemptId")) not in scores
        ]

    def attempt_metadata(self, session_id: str, attempt_id: str) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        attempt = self.find_attempt(session_dir, safe_id(attempt_id))
        if not attempt:
            raise FileNotFoundError(attempt_id)
        return attempt

    def save_score(self, session_id: str, attempt_id: str, score: dict[str, Any]) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        stored_score = {
            "attemptId": safe_id(attempt_id),
            "receivedAt": now_iso(),
            **score,
        }
        append_jsonl(session_dir / "scores.jsonl", stored_score)
        return stored_score

    def attempt_audio_path(self, session_id: str, attempt_id: str) -> Path:
        session_dir = self.require_session(session_id)
        attempt = self.find_attempt(session_dir, safe_id(attempt_id))
        if not attempt:
            raise FileNotFoundError(attempt_id)

        recording_path = self.root / str(attempt["recordingPath"])
        if not recording_path.exists():
            raise FileNotFoundError(attempt_id)
        return recording_path

    def session_dir(self, session_id: str) -> Path:
        return self.root / "sessions" / safe_id(session_id)

    def require_session(self, session_id: str) -> Path:
        session_dir = self.session_dir(session_id)
        if not (session_dir / "metadata.json").exists():
            raise FileNotFoundError(session_id)
        return session_dir

    def find_attempt(self, session_dir: Path, attempt_id: str) -> dict[str, Any] | None:
        for attempt in read_jsonl(session_dir / "attempts.jsonl"):
            if attempt.get("attemptId") == attempt_id:
                return attempt
        return None

    def scores_by_attempt(self, session_dir: Path) -> dict[str, dict[str, Any]]:
        scores = {}
        for score in read_jsonl(session_dir / "scores.jsonl"):
            attempt_id = score.get("attemptId")
            if attempt_id:
                scores[str(attempt_id)] = score
        return scores


def safe_id(value: str) -> str:
    if not value or not SAFE_ID.match(value):
        raise ValueError(f"Unsafe id: {value!r}")
    return value


def safe_suffix(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in {".webm", ".wav", ".mp3", ".m4a", ".ogg"}:
        return suffix
    if content_type == "audio/wav":
        return ".wav"
    if content_type == "audio/ogg":
        return ".ogg"
    return ".webm"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False))
        file.write("\n")


def write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    if not items:
        path.unlink(missing_ok=True)
        return

    with path.open("w", encoding="utf-8") as file:
        for item in items:
            file.write(json.dumps(item, ensure_ascii=False))
            file.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    items = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping malformed JSONL line %s in %s", line_number, path)
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def relative_to_root(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def delete_file(path: Path) -> bool:
    if not path.exists():
        return False
    path.unlink()
    return True


def is_remembered_score(score: dict[str, Any] | None) -> bool:
    if not score or score.get("status") != "scored":
        return False

    communication = score.get("result", {}).get("communication", {})
    if communication.get("close_enough") is True:
        return True

    return str(communication.get("status") or "") in {"exact", "close", "understood"}


def score_status(score: dict[str, Any] | None) -> str:
    if not score:
        return "unscored"
    if score.get("status") != "scored":
        return str(score.get("status") or "unavailable")
    communication = score.get("result", {}).get("communication", {})
    return str(communication.get("status") or "scored")


def participant_id_from(
    metadata: dict[str, Any],
    attempts: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> str:
    participant_id = metadata.get("participantId")
    if participant_id and participant_id != "local":
        return str(participant_id)

    for item in [*attempts, *events]:
        participant_id = item.get("participantId")
        if participant_id:
            return str(participant_id)

    return str(participant_id or "local")
