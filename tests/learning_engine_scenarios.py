from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
from typing import Any, Iterator

import test_support  # noqa: F401
from app.content.learning_engine import build_learning_plan
from app.content.learning_engine.state_store import LearningStateStore

DATA_DIR = Path("model/content")
PROJECT_DIR = Path(".")
DEFAULT_PARTICIPANT = "Bob"
DEFAULT_LANGUAGE = "ja"
DEFAULT_REVIEWED_AT = "2026-06-01"
DEFAULT_PLANNING_DATE = "2026-06-01"


@contextmanager
def make_learning_state() -> Iterator[SyntheticLearningState]:
    with tempfile.TemporaryDirectory() as temp_dir:
        yield SyntheticLearningState(LearningStateStore(Path(temp_dir) / "learning_state.sqlite"))


@dataclass
class SyntheticLearningState:
    store: LearningStateStore
    participant_id: str = DEFAULT_PARTICIPANT
    language: str = DEFAULT_LANGUAGE
    _attempt_number: int = field(default=0, init=False)

    def record_choice(
        self,
        *,
        target_id: str,
        lesson_id: str,
        is_correct: bool,
        scene_set: str = "mvp",
    ) -> None:
        self.store.record_choice(
            {
                "type": "choice_selected",
                "participantId": self.participant_id,
                "language": self.language,
                "sceneSet": scene_set,
                "lessonId": lesson_id,
                "lessonPage": page_from_lesson_id(lesson_id),
                "stepId": "broad_meaning_guess",
                "targetId": target_id,
                "isCorrect": is_correct,
            }
        )

    def record_passed_anchor(
        self,
        *,
        target_id: str,
        lesson_id: str,
        reviewed_at: str = DEFAULT_REVIEWED_AT,
        attempt_overrides: dict[str, Any] | None = None,
        score_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.record_scored_attempt(
            target_id=target_id,
            lesson_id=lesson_id,
            passed=True,
            scene_set="mvp",
            reviewed_at=reviewed_at,
            attempt_overrides=attempt_overrides,
            score_overrides=score_overrides,
        )

    def record_failed_anchor(
        self,
        *,
        target_id: str,
        lesson_id: str,
        reviewed_at: str = DEFAULT_REVIEWED_AT,
        attempt_overrides: dict[str, Any] | None = None,
        score_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.record_scored_attempt(
            target_id=target_id,
            lesson_id=lesson_id,
            passed=False,
            scene_set="mvp",
            reviewed_at=reviewed_at,
            attempt_overrides=attempt_overrides,
            score_overrides=score_overrides,
        )

    def record_failed_transfer(
        self,
        *,
        target_id: str,
        lesson_id: str,
        reviewed_at: str = DEFAULT_REVIEWED_AT,
        attempt_overrides: dict[str, Any] | None = None,
        score_overrides: dict[str, Any] | None = None,
    ) -> None:
        merged_attempt_overrides = {"lessonStage": "same_day_transfer"}
        if attempt_overrides:
            merged_attempt_overrides.update(attempt_overrides)
        self.record_scored_attempt(
            target_id=target_id,
            lesson_id=lesson_id,
            passed=False,
            scene_set="mvp",
            reviewed_at=reviewed_at,
            attempt_overrides=merged_attempt_overrides,
            score_overrides=score_overrides,
        )

    def record_failed_delayed(
        self,
        *,
        target_id: str,
        lesson_id: str,
        reviewed_at: str = DEFAULT_REVIEWED_AT,
        attempt_overrides: dict[str, Any] | None = None,
        score_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.record_scored_attempt(
            target_id=target_id,
            lesson_id=lesson_id,
            passed=False,
            scene_set="delayed",
            reviewed_at=reviewed_at,
            attempt_overrides=attempt_overrides,
            score_overrides=score_overrides,
        )

    def record_pending_attempt(self, *, target_id: str, lesson_id: str, scene_set: str = "mvp") -> None:
        self.store.record_attempt(
            {
                "attemptId": self.next_attempt_id(),
                "participantId": self.participant_id,
                "language": self.language,
                "sceneSet": scene_set,
                "lessonId": lesson_id,
                "lessonPage": page_from_lesson_id(lesson_id),
                "stepId": "scene_recall" if scene_set == "delayed" else "backward_build",
                "targetId": target_id,
            }
        )

    def record_scored_attempt(
        self,
        *,
        target_id: str,
        lesson_id: str,
        passed: bool,
        scene_set: str,
        reviewed_at: str = DEFAULT_REVIEWED_AT,
        attempt_overrides: dict[str, Any] | None = None,
        score_overrides: dict[str, Any] | None = None,
    ) -> None:
        attempt: dict[str, Any] = {
            "attemptId": self.next_attempt_id(),
            "participantId": self.participant_id,
            "language": self.language,
            "sceneSet": scene_set,
            "lessonId": lesson_id,
            "lessonPage": page_from_lesson_id(lesson_id),
            "stepId": "scene_recall" if scene_set == "delayed" else "backward_build",
            "targetId": target_id,
            "receivedAt": reviewed_at,
            "lessonStage": lesson_stage_for_scene_set(scene_set),
            "recordingLimitMs": 5000,
        }
        if attempt_overrides:
            attempt.update(attempt_overrides)
        self.store.record_attempt(attempt)
        self.store.record_score(
            attempt=attempt,
            score=score_payload(passed, reviewed_at=reviewed_at, overrides=score_overrides),
        )

    def build_plan_for(
        self,
        *,
        participant_id: str | None = DEFAULT_PARTICIPANT,
        language: str = DEFAULT_LANGUAGE,
        scene_set: str = "mvp",
        order_seed: str = "synthetic",
        planning_date: str = DEFAULT_PLANNING_DATE,
    ) -> dict:
        return build_learning_plan(
            data_dir=DATA_DIR,
            project_dir=PROJECT_DIR,
            language=language,
            scene_set=scene_set,
            order_seed=order_seed,
            participant_id=participant_id,
            state_store=self.store,
            planning_date=planning_date,
        )

    def next_attempt_id(self) -> str:
        self._attempt_number += 1
        return f"synthetic-attempt-{self._attempt_number}"


def plan_rows(plan: dict) -> list[tuple[str, str | None, str | None]]:
    return [
        (
            str(lesson.get("targetId") or lesson.get("target", {}).get("id")),
            lesson.get("planPurpose"),
            lesson.get("repairCategory"),
        )
        for lesson in plan.get("lessons", [])
    ]


def plan_stages(plan: dict) -> list[str | None]:
    return [lesson.get("stage") for lesson in plan.get("lessons", [])]


def score_payload(
    passed: bool,
    *,
    reviewed_at: str = DEFAULT_REVIEWED_AT,
    overrides: dict[str, Any] | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "receivedAt": reviewed_at,
        "status": "scored",
        "result": {
            "communication": {
                "status": "exact" if passed else "missed",
                "close_enough": passed,
            }
        },
    }
    if overrides:
        payload = deep_merge(payload, overrides)
    return payload


def deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def lesson_stage_for_scene_set(scene_set: str) -> str:
    if scene_set == "delayed":
        return "delayed_review"
    if scene_set == "transfer":
        return "same_day_transfer"
    return "guided_scene_production"


def page_from_lesson_id(lesson_id: str) -> str:
    if "introduce" in lesson_id:
        return "introduce"
    if "repair" in lesson_id or "understand" in lesson_id:
        return "repair"
    if "excuse-me" in lesson_id:
        return "excuse-me"
    if "order" in lesson_id:
        return "food-order"
    return "hello"
