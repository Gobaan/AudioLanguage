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
