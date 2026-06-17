from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RepairCategory = Literal[
    "meaning_repair",
    "recall_repair",
    "transfer_repair",
    "memory_repair",
    "healthy",
    "new",
]

PlanPurpose = Literal[
    "meaning_repair",
    "recall_repair",
    "transfer_repair",
    "memory_repair",
    "due_review",
    "new",
]


@dataclass(frozen=True)
class TargetState:
    participant_id: str
    language: str
    target_id: str
    last_choice_correct: bool | None = None
    has_wrong_choice: bool = False
    last_attempt_status: str = "none"
    last_scene_set: str = ""
    last_lesson_id: str = ""
    anchor_passed: bool = False
    transfer_passed: bool = False
    delayed_passed: bool = False
    failed_transfer: bool = False
    failed_delayed: bool = False
    review_count: int = 0
    lapse_count: int = 0
    ease_factor: float = 2.5
    interval_days: int = 0
    last_reviewed_at: str = ""
    next_review_at: str = ""
    last_quality: int | None = None
    updated_at: str = ""


@dataclass(frozen=True)
class IndexedLesson:
    tab: dict
    lesson: dict
    target_id: str
    stage: str


@dataclass(frozen=True)
class PlannedLesson:
    tab: dict
    lesson: dict
    purpose: PlanPurpose
    repair_category: RepairCategory | None = None
