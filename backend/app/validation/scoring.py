from __future__ import annotations

from typing import Any

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


def attempt_expected_phrase(attempt: dict[str, Any]) -> tuple[str, str]:
    build_prompt = str(attempt.get("buildPromptText") or "").strip()
    if build_prompt:
        return build_prompt, build_prompt

    expected_text = str(attempt.get("expectedText") or "").strip()
    expected_transliteration = str(attempt.get("expectedTransliteration") or expected_text).strip()
    return expected_text, expected_transliteration


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
