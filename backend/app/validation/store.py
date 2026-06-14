from __future__ import annotations

import json
from pathlib import Path
import shutil
import uuid
from typing import Any

from app.validation.jsonl_io import (
    append_jsonl,
    delete_file,
    now_iso,
    read_jsonl,
    relative_to_root,
    safe_id,
    safe_suffix,
    write_json,
    write_jsonl,
)
from app.validation.rollups import build_admin_summary, build_scorecard
from app.validation.scoring import HUMAN_NAMES, participant_id_from


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

    def scorecard(self, session_id: str, *, data_dir: Path | None = None, project_dir: Path | None = None) -> dict[str, Any]:
        session_dir = self.require_session(session_id)
        return build_scorecard(
            session_dir,
            self.scores_by_attempt,
            data_dir=data_dir,
            project_dir=project_dir,
        )

    def admin_summary(self) -> dict[str, Any]:
        return build_admin_summary(self.root, self.scores_by_attempt)

    def delete_session(self, session_id: str) -> dict[str, str]:
        session_dir = self.require_session(session_id)
        shutil.rmtree(session_dir)
        return {"sessionId": safe_id(session_id), "status": "deleted"}

    def delete_all_sessions(self) -> dict[str, Any]:
        sessions_dir = self.root / "sessions"
        deleted_count = 0
        if sessions_dir.exists():
            deleted_count = sum(1 for session_dir in sessions_dir.iterdir() if session_dir.is_dir())
            shutil.rmtree(sessions_dir)

        sessions_dir.mkdir(parents=True, exist_ok=True)
        return {"deletedSessionCount": deleted_count, "status": "deleted"}

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
