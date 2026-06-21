from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.content.learning_engine.models import TargetState
from app.content.learning_engine.scheduling import (
    STARTING_EASE_FACTOR,
    quality_decision_from_attempt_and_score,
    update_schedule,
    utc_now_iso,
)

logger = logging.getLogger(__name__)


class LearningStateStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def target_states(self, participant_id: str, language: str) -> dict[str, TargetState]:
        self.ensure_schema()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM learner_target_state
                WHERE participant_id = ? AND language = ?
                """,
                (participant_id, language),
            ).fetchall()
        return {str(row["target_id"]): target_state_from_row(row) for row in rows}

    def record_choice(self, event: dict[str, Any], session: dict[str, Any] | None = None) -> None:
        if event.get("type") != "choice_selected":
            return

        target_id = str(event.get("targetId") or "")
        language = str(event.get("language") or (session or {}).get("language") or "")
        participant_id = str(event.get("participantId") or (session or {}).get("participantId") or "")
        if not target_id or not language or not participant_id:
            return

        event_time = str(event.get("receivedAt") or event.get("timestamp") or "")
        choice_correct = event.get("isCorrect")
        with self.connect() as connection:
            self.ensure_schema(connection)
            current = self.get_state(connection, participant_id, language, target_id)
            state = dict(current or base_state(participant_id, language, target_id))
            state.update(
                {
                    "last_choice_correct": bool_to_int(choice_correct) if choice_correct is not None else None,
                    "last_scene_set": str(event.get("sceneSet") or (session or {}).get("sceneSet") or ""),
                    "last_lesson_id": str(event.get("lessonId") or ""),
                    "last_lesson_page": str(event.get("lessonPage") or (session or {}).get("lessonPage") or ""),
                    "last_step_id": str(event.get("stepId") or ""),
                    "updated_at": event_time,
                }
            )
            if choice_correct is False:
                state["has_wrong_choice"] = 1
            self.upsert_state(connection, state)

    def record_attempt(self, attempt: dict[str, Any], session: dict[str, Any] | None = None) -> None:
        target_id = str(attempt.get("targetId") or "")
        language = str(attempt.get("language") or (session or {}).get("language") or "")
        participant_id = str(attempt.get("participantId") or (session or {}).get("participantId") or "")
        if not target_id or not language or not participant_id:
            return

        with self.connect() as connection:
            self.ensure_schema(connection)
            current = self.get_state(connection, participant_id, language, target_id)
            state = dict(current or base_state(participant_id, language, target_id))
            state.update(
                {
                    "last_attempt_id": str(attempt.get("attemptId") or ""),
                    "last_attempt_status": "pending",
                    "last_score_status": "unscored",
                    "last_scene_set": str(attempt.get("sceneSet") or (session or {}).get("sceneSet") or ""),
                    "last_lesson_id": str(attempt.get("lessonId") or ""),
                    "last_lesson_page": str(attempt.get("lessonPage") or (session or {}).get("lessonPage") or ""),
                    "last_step_id": str(attempt.get("stepId") or ""),
                    "updated_at": str(attempt.get("receivedAt") or ""),
                }
            )
            self.upsert_state(connection, state)

    def record_score(
        self,
        *,
        attempt: dict[str, Any],
        score: dict[str, Any],
        session: dict[str, Any] | None = None,
    ) -> None:
        target_id = str(attempt.get("targetId") or "")
        language = str(attempt.get("language") or (session or {}).get("language") or "")
        participant_id = str(attempt.get("participantId") or (session or {}).get("participantId") or "")
        if not target_id or not language or not participant_id:
            return

        status = score_status(score)
        passed = is_remembered_score(score)
        quality_decision = quality_decision_from_attempt_and_score(
            attempt=attempt,
            score=score,
            passed=passed,
        )
        quality = quality_decision.quality if quality_decision is not None else None
        scored_failure = score.get("status") == "scored" and not passed
        attempt_status = "passed" if passed else "failed" if scored_failure else "pending"
        stage = stage_from_attempt(attempt)
        reviewed_at = str(score.get("receivedAt") or attempt.get("receivedAt") or utc_now_iso())

        with self.connect() as connection:
            self.ensure_schema(connection)
            current = self.get_state(connection, participant_id, language, target_id)
            state = dict(current or base_state(participant_id, language, target_id))
            state.update(
                {
                    "last_attempt_id": str(attempt.get("attemptId") or ""),
                    "last_attempt_status": attempt_status,
                    "last_score_status": status,
                    "last_scene_set": str(attempt.get("sceneSet") or (session or {}).get("sceneSet") or ""),
                    "last_lesson_id": str(attempt.get("lessonId") or ""),
                    "last_lesson_page": str(attempt.get("lessonPage") or (session or {}).get("lessonPage") or ""),
                    "last_step_id": str(attempt.get("stepId") or ""),
                    "updated_at": reviewed_at,
                }
            )
            if quality_decision is not None:
                state.update(
                    {
                        "last_duration_ratio": quality_decision.duration_ratio,
                        "last_confidence_band": quality_decision.confidence_band,
                        "last_quality_reason": quality_decision.reason_code,
                    }
                )
            if passed and stage == "anchor":
                state["anchor_passed"] = 1
            elif passed and stage == "transfer":
                state["transfer_passed"] = 1
                state["failed_transfer"] = 0
            elif passed and stage == "delayed":
                state["delayed_passed"] = 1
                state["failed_delayed"] = 0
            if spoken_success_clears_meaning_repair(attempt, passed):
                state["has_wrong_choice"] = 0
                state["last_choice_correct"] = 1
            elif scored_failure and stage == "transfer":
                state["failed_transfer"] = 1
            elif scored_failure and stage == "delayed":
                state["failed_delayed"] = 1
            if quality is not None:
                state.update(schedule_state_values(state, quality=quality, reviewed_at=reviewed_at))
            self.upsert_state(connection, state)

    def rebuild_from_validation_root(self, validation_root: Path) -> None:
        self.database_path.unlink(missing_ok=True)
        self.ensure_schema()
        sessions_dir = validation_root / "sessions"
        if not sessions_dir.exists():
            return

        for session_dir in sorted(path for path in sessions_dir.iterdir() if path.is_dir()):
            metadata_path = session_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            events = read_jsonl_file(session_dir / "events.jsonl")
            attempts = read_jsonl_file(session_dir / "attempts.jsonl")
            scores = {
                str(score.get("attemptId")): score
                for score in read_jsonl_file(session_dir / "scores.jsonl")
                if score.get("attemptId")
            }
            session = {
                **metadata,
                "participantId": participant_id_from(metadata, attempts, events),
            }
            for event in events:
                self.record_choice(event, session)
            for attempt in attempts:
                self.record_attempt(attempt, session)
                score = scores.get(str(attempt.get("attemptId")))
                if score:
                    self.record_score(attempt=attempt, score=score, session=session)

    def clear(self) -> None:
        self.database_path.unlink(missing_ok=True)

    def delete_participant(self, participant_id: str) -> int:
        """Delete all learner target history for one participant."""
        normalized = str(participant_id or "").strip()
        if not normalized:
            return 0

        with self.connect() as connection:
            self.ensure_schema(connection)
            cursor = connection.execute(
                """
                DELETE FROM learner_target_state
                WHERE participant_id = ?
                """,
                (normalized,),
            )
            return int(cursor.rowcount or 0)

    def delete_target(self, participant_id: str, language: str, target_id: str) -> int:
        normalized_participant = str(participant_id or "").strip()
        normalized_language = str(language or "").strip()
        normalized_target = str(target_id or "").strip()
        if not normalized_participant or not normalized_language or not normalized_target:
            return 0

        with self.connect() as connection:
            self.ensure_schema(connection)
            cursor = connection.execute(
                """
                DELETE FROM learner_target_state
                WHERE participant_id = ? AND language = ? AND target_id = ?
                """,
                (normalized_participant, normalized_language, normalized_target),
            )
            return int(cursor.rowcount or 0)

    def merge_participant(self, source_participant_id: str, target_participant_id: str) -> int:
        source_id = str(source_participant_id or "").strip()
        target_id = str(target_participant_id or "").strip()
        if not source_id or not target_id or source_id == target_id:
            return 0

        with self.connect() as connection:
            self.ensure_schema(connection)
            source_rows = connection.execute(
                """
                SELECT * FROM learner_target_state
                WHERE participant_id = ?
                """,
                (source_id,),
            ).fetchall()
            merged_count = 0
            for source_row in source_rows:
                existing_target_row = self.get_state(
                    connection,
                    target_id,
                    str(source_row["language"]),
                    str(source_row["target_id"]),
                )
                source_state = dict(source_row)
                source_state["participant_id"] = target_id
                if existing_target_row is None:
                    self.upsert_state(connection, source_state)
                else:
                    self.upsert_state(connection, merged_state(dict(existing_target_row), source_state))
                merged_count += 1

            connection.execute(
                """
                DELETE FROM learner_target_state
                WHERE participant_id = ?
                """,
                (source_id,),
            )
            return merged_count

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def ensure_schema(self, connection: sqlite3.Connection | None = None) -> None:
        if connection is None:
            with self.connect() as owned_connection:
                self.ensure_schema(owned_connection)
            return

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS learner_target_state (
                participant_id TEXT NOT NULL,
                language TEXT NOT NULL,
                target_id TEXT NOT NULL,
                last_choice_correct INTEGER,
                has_wrong_choice INTEGER NOT NULL DEFAULT 0,
                last_attempt_id TEXT NOT NULL DEFAULT '',
                last_attempt_status TEXT NOT NULL DEFAULT 'none',
                last_score_status TEXT NOT NULL DEFAULT 'unscored',
                last_scene_set TEXT NOT NULL DEFAULT '',
                last_lesson_id TEXT NOT NULL DEFAULT '',
                last_lesson_page TEXT NOT NULL DEFAULT '',
                last_step_id TEXT NOT NULL DEFAULT '',
                anchor_passed INTEGER NOT NULL DEFAULT 0,
                transfer_passed INTEGER NOT NULL DEFAULT 0,
                delayed_passed INTEGER NOT NULL DEFAULT 0,
                failed_transfer INTEGER NOT NULL DEFAULT 0,
                failed_delayed INTEGER NOT NULL DEFAULT 0,
                review_count INTEGER NOT NULL DEFAULT 0,
                lapse_count INTEGER NOT NULL DEFAULT 0,
                ease_factor REAL NOT NULL DEFAULT 2.5,
                interval_days INTEGER NOT NULL DEFAULT 0,
                last_reviewed_at TEXT NOT NULL DEFAULT '',
                next_review_at TEXT NOT NULL DEFAULT '',
                last_quality INTEGER,
                last_duration_ratio REAL,
                last_confidence_band TEXT NOT NULL DEFAULT '',
                last_quality_reason TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (participant_id, language, target_id)
            )
            """
        )
        ensure_columns(
            connection,
            "learner_target_state",
            {
                "review_count": "INTEGER NOT NULL DEFAULT 0",
                "lapse_count": "INTEGER NOT NULL DEFAULT 0",
                "ease_factor": "REAL NOT NULL DEFAULT 2.5",
                "interval_days": "INTEGER NOT NULL DEFAULT 0",
                "last_reviewed_at": "TEXT NOT NULL DEFAULT ''",
                "next_review_at": "TEXT NOT NULL DEFAULT ''",
                "last_quality": "INTEGER",
                "last_duration_ratio": "REAL",
                "last_confidence_band": "TEXT NOT NULL DEFAULT ''",
                "last_quality_reason": "TEXT NOT NULL DEFAULT ''",
            },
        )

    def get_state(
        self,
        connection: sqlite3.Connection,
        participant_id: str,
        language: str,
        target_id: str,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT * FROM learner_target_state
            WHERE participant_id = ? AND language = ? AND target_id = ?
            """,
            (participant_id, language, target_id),
        ).fetchone()

    def upsert_state(self, connection: sqlite3.Connection, state: dict[str, Any]) -> None:
        columns = list(state.keys())
        placeholders = ", ".join("?" for _ in columns)
        assignments = ", ".join(f"{column} = excluded.{column}" for column in columns if column not in PRIMARY_KEY)
        connection.execute(
            f"""
            INSERT INTO learner_target_state ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(participant_id, language, target_id) DO UPDATE SET {assignments}
            """,
            [state[column] for column in columns],
        )


PRIMARY_KEY = {"participant_id", "language", "target_id"}


def base_state(participant_id: str, language: str, target_id: str) -> dict[str, Any]:
    return {
        "participant_id": participant_id,
        "language": language,
        "target_id": target_id,
        "last_choice_correct": None,
        "has_wrong_choice": 0,
        "last_attempt_id": "",
        "last_attempt_status": "none",
        "last_score_status": "unscored",
        "last_scene_set": "",
        "last_lesson_id": "",
        "last_lesson_page": "",
        "last_step_id": "",
        "anchor_passed": 0,
        "transfer_passed": 0,
        "delayed_passed": 0,
        "failed_transfer": 0,
        "failed_delayed": 0,
        "review_count": 0,
        "lapse_count": 0,
        "ease_factor": STARTING_EASE_FACTOR,
        "interval_days": 0,
        "last_reviewed_at": "",
        "next_review_at": "",
        "last_quality": None,
        "last_duration_ratio": None,
        "last_confidence_band": "",
        "last_quality_reason": "",
        "updated_at": "",
    }


def target_state_from_row(row: sqlite3.Row) -> TargetState:
    return TargetState(
        participant_id=str(row["participant_id"]),
        language=str(row["language"]),
        target_id=str(row["target_id"]),
        last_choice_correct=int_to_bool(row["last_choice_correct"]),
        has_wrong_choice=bool(row["has_wrong_choice"]),
        last_attempt_status=str(row["last_attempt_status"]),
        last_scene_set=str(row["last_scene_set"]),
        last_lesson_id=str(row["last_lesson_id"]),
        anchor_passed=bool(row["anchor_passed"]),
        transfer_passed=bool(row["transfer_passed"]),
        delayed_passed=bool(row["delayed_passed"]),
        failed_transfer=bool(row["failed_transfer"]),
        failed_delayed=bool(row["failed_delayed"]),
        review_count=int(row["review_count"]),
        lapse_count=int(row["lapse_count"]),
        ease_factor=float(row["ease_factor"]),
        interval_days=int(row["interval_days"]),
        last_reviewed_at=str(row["last_reviewed_at"]),
        next_review_at=str(row["next_review_at"]),
        last_quality=int(row["last_quality"]) if row["last_quality"] is not None else None,
        last_duration_ratio=float(row["last_duration_ratio"]) if row["last_duration_ratio"] is not None else None,
        last_confidence_band=str(row["last_confidence_band"] or ""),
        last_quality_reason=str(row["last_quality_reason"] or ""),
        updated_at=str(row["updated_at"]),
    )


def bool_to_int(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def int_to_bool(value: int | None) -> bool | None:
    if value is None:
        return None
    return bool(value)


def stage_from_attempt(attempt: dict[str, Any]) -> str:
    lesson_stage = str(attempt.get("lessonStage") or "").strip()
    if lesson_stage in {"guided_scene_production", "same_day_anchor_recall", "anchor"}:
        return "anchor"
    if lesson_stage in {"same_day_transfer", "transfer"}:
        return "transfer"
    if lesson_stage in {"delayed_review", "delayed"}:
        return "delayed"

    plan_purpose = str(attempt.get("planPurpose") or "")
    if plan_purpose in {"transfer_repair", "transfer_practice"}:
        return "transfer"
    if plan_purpose in {"memory_repair"}:
        return "delayed"

    lesson_id = str(attempt.get("lessonId") or "")
    scene_set = str(attempt.get("sceneSet") or "")
    if "same_day_transfer" in lesson_id or lesson_id.endswith("-transfer") or scene_set == "transfer":
        return "transfer"
    if "delayed_review" in lesson_id or scene_set in {"delayed", "delayed_review"}:
        return "delayed"
    return "anchor"


def spoken_success_clears_meaning_repair(attempt: dict[str, Any], passed: bool) -> bool:
    if not passed:
        return False

    build_prompt_text = str(attempt.get("buildPromptText") or "").strip()
    expected_text = str(attempt.get("expectedText") or "").strip()
    if build_prompt_text and build_prompt_text != expected_text:
        return False

    return True


def read_jsonl_file(path: Path) -> list[dict[str, Any]]:
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


def ensure_columns(connection: sqlite3.Connection, table_name: str, columns: dict[str, str]) -> None:
    existing_columns = {
        str(row["name"])
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, definition in columns.items():
        if column_name not in existing_columns:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def merged_state(target_state: dict[str, Any], source_state: dict[str, Any]) -> dict[str, Any]:
    progress_state = more_advanced_state(target_state, source_state)
    newest_state = newest_updated_state(target_state, source_state)
    merged = dict(newest_state)
    merged["participant_id"] = str(target_state["participant_id"])
    merged["language"] = str(target_state["language"])
    merged["target_id"] = str(target_state["target_id"])

    for column in [
        "has_wrong_choice",
        "anchor_passed",
        "transfer_passed",
        "delayed_passed",
        "failed_transfer",
        "failed_delayed",
    ]:
        merged[column] = 1 if bool(target_state.get(column)) or bool(source_state.get(column)) else 0
    if merged["transfer_passed"]:
        merged["failed_transfer"] = 0
    if merged["delayed_passed"]:
        merged["failed_delayed"] = 0

    for column in [
        "last_attempt_id",
        "last_attempt_status",
        "last_score_status",
        "last_scene_set",
        "last_lesson_id",
        "last_lesson_page",
        "last_step_id",
        "review_count",
        "ease_factor",
        "interval_days",
        "last_reviewed_at",
        "next_review_at",
        "last_quality",
        "last_duration_ratio",
        "last_confidence_band",
        "last_quality_reason",
    ]:
        merged[column] = progress_state[column]
    merged["review_count"] = max(int(target_state.get("review_count") or 0), int(source_state.get("review_count") or 0))
    merged["lapse_count"] = max(int(target_state.get("lapse_count") or 0), int(source_state.get("lapse_count") or 0))
    if bool(target_state.get("last_choice_correct")) or bool(source_state.get("last_choice_correct")):
        merged["last_choice_correct"] = 1

    return merged


def more_advanced_state(first_state: dict[str, Any], second_state: dict[str, Any]) -> dict[str, Any]:
    first_rank = progress_rank(first_state)
    second_rank = progress_rank(second_state)
    if second_rank > first_rank:
        return second_state
    return first_state


def newest_updated_state(first_state: dict[str, Any], second_state: dict[str, Any]) -> dict[str, Any]:
    if str(second_state.get("updated_at") or "") >= str(first_state.get("updated_at") or ""):
        return second_state
    return first_state


def progress_rank(state: dict[str, Any]) -> tuple[int, int, int, str, str]:
    return (
        stage_rank(state),
        int(state.get("review_count") or 0),
        int(state.get("interval_days") or 0),
        str(state.get("next_review_at") or ""),
        str(state.get("updated_at") or ""),
    )


def stage_rank(state: dict[str, Any]) -> int:
    if bool(state.get("delayed_passed")):
        return 3
    if bool(state.get("transfer_passed")):
        return 2
    if bool(state.get("anchor_passed")):
        return 1
    return 0


def schedule_state_values(state: dict[str, Any], *, quality: int, reviewed_at: str) -> dict[str, Any]:
    update = update_schedule(state, quality=quality, reviewed_at=reviewed_at)
    return {
        "review_count": update.review_count,
        "lapse_count": update.lapse_count,
        "ease_factor": update.ease_factor,
        "interval_days": update.interval_days,
        "last_reviewed_at": update.last_reviewed_at,
        "next_review_at": update.next_review_at,
        "last_quality": update.last_quality,
    }
