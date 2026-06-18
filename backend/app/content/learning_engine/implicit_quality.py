from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ResponsePace = Literal["fast", "normal", "slow", "unknown"]
ConfidenceBand = Literal["low", "medium", "high", "unknown"]
SemanticOutcome = Literal["off_target", "close_with_gaps", "clean_pass", "exact_clean"]

DEFAULT_EXPECTED_RECORDING_DURATION_MS = 5000.0
FAST_RESPONSE_RATIO_MAX = 0.55
SLOW_RESPONSE_RATIO_MIN = 0.9
LOW_CONFIDENCE_MAX = 0.55
HIGH_CONFIDENCE_MIN = 0.85
MINIMUM_USABLE_BYTECOUNT = 900


@dataclass(frozen=True)
class ImplicitQualityDecision:
    quality: int
    reason_code: str
    duration_ratio: float | None
    response_pace: ResponsePace
    confidence_band: ConfidenceBand
    semantic_outcome: SemanticOutcome
    no_speech: bool


def derive_implicit_quality_decision(
    *,
    attempt: dict[str, Any],
    score: dict[str, Any],
    passed: bool,
) -> ImplicitQualityDecision | None:
    if score.get("status") != "scored":
        return None

    duration_ratio = recording_duration_ratio(attempt)
    response_pace = response_pace_from_ratio(duration_ratio, attempt)
    confidence_band = communication_confidence_band(score)
    semantic_outcome = communication_semantic_outcome(score, passed)
    no_speech = has_no_speech_signal(attempt)

    if no_speech:
        return ImplicitQualityDecision(
            quality=0,
            reason_code="no_speech_signal",
            duration_ratio=duration_ratio,
            response_pace=response_pace,
            confidence_band=confidence_band,
            semantic_outcome=semantic_outcome,
            no_speech=True,
        )

    if semantic_outcome == "off_target" or not passed:
        return ImplicitQualityDecision(
            quality=0,
            reason_code="semantic_failure",
            duration_ratio=duration_ratio,
            response_pace=response_pace,
            confidence_band=confidence_band,
            semantic_outcome=semantic_outcome,
            no_speech=False,
        )

    if (
        semantic_outcome == "close_with_gaps"
        or response_pace == "slow"
        or confidence_band == "low"
    ):
        return ImplicitQualityDecision(
            quality=3,
            reason_code="shaky_success",
            duration_ratio=duration_ratio,
            response_pace=response_pace,
            confidence_band=confidence_band,
            semantic_outcome=semantic_outcome,
            no_speech=False,
        )

    if (
        semantic_outcome == "exact_clean"
        and confidence_band == "high"
        and response_pace in {"fast", "normal"}
    ):
        return ImplicitQualityDecision(
            quality=5,
            reason_code="strong_fluent_success",
            duration_ratio=duration_ratio,
            response_pace=response_pace,
            confidence_band=confidence_band,
            semantic_outcome=semantic_outcome,
            no_speech=False,
        )

    return ImplicitQualityDecision(
        quality=4,
        reason_code="solid_success",
        duration_ratio=duration_ratio,
        response_pace=response_pace,
        confidence_band=confidence_band,
        semantic_outcome=semantic_outcome,
        no_speech=False,
    )


def has_no_speech_signal(attempt: dict[str, Any]) -> bool:
    if bool(attempt.get("timedOutWithoutSpeech")):
        return True
    if str(attempt.get("recordingStoppedBy") or "") == "no_speech_timeout":
        return True

    speech_detected = attempt.get("speechDetected")
    byte_count = numeric_or_none(attempt.get("byteCount"))
    if speech_detected is False and byte_count is not None and byte_count < MINIMUM_USABLE_BYTECOUNT:
        return True
    if byte_count is not None and byte_count <= 0:
        return True
    return False


def recording_duration_ratio(attempt: dict[str, Any]) -> float | None:
    duration_ms = numeric_or_none(attempt.get("recordingDurationMs"))
    if duration_ms is None or duration_ms <= 0:
        return None

    expected_ms = (
        numeric_or_none(attempt.get("recordingLimitMs"))
        or numeric_or_none(attempt.get("expectedRecordingDurationMs"))
        or DEFAULT_EXPECTED_RECORDING_DURATION_MS
    )
    if expected_ms <= 0:
        return None

    return round(duration_ms / expected_ms, 3)


def response_pace_from_ratio(duration_ratio: float | None, attempt: dict[str, Any]) -> ResponsePace:
    if duration_ratio is not None:
        if duration_ratio <= FAST_RESPONSE_RATIO_MAX:
            return "fast"
        if duration_ratio >= SLOW_RESPONSE_RATIO_MIN:
            return "slow"
        return "normal"

    if str(attempt.get("recordingStoppedBy") or "") == "hard_limit":
        return "slow"

    return "unknown"


def communication_confidence_band(score: dict[str, Any]) -> ConfidenceBand:
    communication = score.get("result", {}).get("communication", {})
    confidence = numeric_or_none(communication.get("confidence"))
    if confidence is None:
        return "unknown"
    if confidence <= LOW_CONFIDENCE_MAX:
        return "low"
    if confidence >= HIGH_CONFIDENCE_MIN:
        return "high"
    return "medium"


def communication_semantic_outcome(score: dict[str, Any], passed: bool) -> SemanticOutcome:
    communication = score.get("result", {}).get("communication", {})
    status = str(communication.get("status") or "").strip().lower()
    missing_slots = communication.get("missing_slots") or []
    has_missing_slots = isinstance(missing_slots, list) and len(missing_slots) > 0
    has_extra_intent = bool(communication.get("extra_intent"))

    if not passed or has_extra_intent:
        return "off_target"
    if status in {"missed", "wrong", "off_target", "invalid"}:
        return "off_target"
    if status == "close" or has_missing_slots:
        return "close_with_gaps"
    if status == "exact":
        return "exact_clean"
    return "clean_pass"


def numeric_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
