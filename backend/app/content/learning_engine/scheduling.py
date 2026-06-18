from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.content.learning_engine.implicit_quality import ImplicitQualityDecision, derive_implicit_quality_decision

STARTING_EASE_FACTOR = 2.5
MINIMUM_EASE_FACTOR = 1.3

QUALITY_FAIL = 0
QUALITY_PASS = 4
ENABLE_IMPLICIT_QUALITY_SIGNALS = True
MINIMUM_REVIEW_GAP_HOURS = 8


@dataclass(frozen=True)
class SchedulingUpdate:
    review_count: int
    lapse_count: int
    ease_factor: float
    interval_days: int
    last_reviewed_at: str
    next_review_at: str
    last_quality: int


def today_iso() -> str:
    return date.today().isoformat()


def planning_date_or_today(planning_date: str | None = None) -> str:
    return planning_date or today_iso()


def quality_from_score(score: dict[str, Any], passed: bool) -> int | None:
    decision = quality_decision_from_attempt_and_score(attempt={}, score=score, passed=passed)
    if decision is None:
        return None
    return decision.quality


def quality_decision_from_attempt_and_score(
    *,
    attempt: dict[str, Any],
    score: dict[str, Any],
    passed: bool,
) -> ImplicitQualityDecision | None:
    if score.get("status") != "scored":
        return None
    if not ENABLE_IMPLICIT_QUALITY_SIGNALS:
        return ImplicitQualityDecision(
            quality=QUALITY_PASS if passed else QUALITY_FAIL,
            reason_code="coarse_pass_fail",
            duration_ratio=None,
            response_pace="unknown",
            confidence_band="unknown",
            semantic_outcome="clean_pass" if passed else "off_target",
            no_speech=False,
        )

    decision = derive_implicit_quality_decision(attempt=attempt, score=score, passed=passed)
    if decision is not None:
        return decision

    return ImplicitQualityDecision(
        quality=QUALITY_PASS if passed else QUALITY_FAIL,
        reason_code="coarse_pass_fail_fallback",
        duration_ratio=None,
        response_pace="unknown",
        confidence_band="unknown",
        semantic_outcome="clean_pass" if passed else "off_target",
        no_speech=False,
    )


def update_schedule(
    state: dict[str, Any],
    *,
    quality: int,
    reviewed_at: str,
) -> SchedulingUpdate:
    review_day = iso_date(reviewed_at)
    reviewed_at_value = normalized_reviewed_at(reviewed_at)
    review_count = int(state.get("review_count") or 0)
    lapse_count = int(state.get("lapse_count") or 0)
    ease_factor = float(state.get("ease_factor") or STARTING_EASE_FACTOR)
    interval_days = int(state.get("interval_days") or 0)

    if quality < 3:
        lapse_count += 1
        interval_days = 1
        ease_factor = max(MINIMUM_EASE_FACTOR, ease_factor - 0.2)
    else:
        review_count += 1
        if review_count == 1:
            interval_days = 1
        elif review_count == 2:
            interval_days = 3
        else:
            interval_days = max(1, round(interval_days * ease_factor))
        ease_factor = next_ease_factor(ease_factor, quality)

    next_review_day = review_day + timedelta(days=interval_days)
    return SchedulingUpdate(
        review_count=review_count,
        lapse_count=lapse_count,
        ease_factor=ease_factor,
        interval_days=interval_days,
        last_reviewed_at=reviewed_at_value,
        next_review_at=next_review_day.isoformat(),
        last_quality=quality,
    )


def is_due_for_review(next_review_at: str, planning_date: str, last_reviewed_at: str = "") -> bool:
    if not next_review_at:
        return False
    if iso_date(next_review_at) > iso_date(planning_date):
        return False
    return has_minimum_review_gap_elapsed(last_reviewed_at, planning_date)


def has_minimum_review_gap_elapsed(last_reviewed_at: str, planning_date: str) -> bool:
    reviewed_datetime = iso_datetime_or_none(last_reviewed_at)
    planning_datetime = iso_datetime_or_none(planning_date)
    if reviewed_datetime is None or planning_datetime is None:
        return True
    return planning_datetime - reviewed_datetime >= timedelta(hours=MINIMUM_REVIEW_GAP_HOURS)


def next_ease_factor(ease_factor: float, quality: int) -> float:
    if quality >= 5:
        return ease_factor + 0.15
    if quality == 3:
        return max(MINIMUM_EASE_FACTOR, ease_factor - 0.15)
    return ease_factor


def iso_date(value: str) -> date:
    if not value:
        return date.today()

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return date.fromisoformat(value[:10])


def iso_datetime_or_none(value: str) -> datetime | None:
    if not value or "T" not in value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


def normalized_reviewed_at(value: str) -> str:
    parsed = iso_datetime_or_none(value)
    if parsed is not None:
        return parsed.isoformat()
    return iso_date(value).isoformat()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
