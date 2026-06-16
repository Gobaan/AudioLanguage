"""Shared character identity metadata for visuals and dialogue audio."""

from __future__ import annotations

from typing import Any


DEFAULT_CHARACTER_ID = "staff"


CHARACTER_BY_ROLE: dict[str, dict[str, str]] = {
    "learner": {
        "character_id": "learner",
        "visual_reference": "learner-reference.png",
        "gender": "female",
    },
    "barista": {
        "character_id": "vendor",
        "visual_reference": "vendor-reference.png",
        "gender": "female",
    },
    "cashier": {
        "character_id": "vendor",
        "visual_reference": "vendor-reference.png",
        "gender": "female",
    },
    "class_partner": {
        "character_id": "friend",
        "visual_reference": "friend-reference.png",
        "gender": "male",
    },
    "classmate": {
        "character_id": "friend",
        "visual_reference": "friend-reference.png",
        "gender": "male",
    },
    "conversation_partner": {
        "character_id": "friend",
        "visual_reference": "friend-reference.png",
        "gender": "male",
    },
    "friend": {
        "character_id": "friend",
        "visual_reference": "friend-reference.png",
        "gender": "male",
    },
    "host": {
        "character_id": "staff",
        "visual_reference": "staff-reference.png",
        "gender": "male",
    },
    "local": {
        "character_id": "local_helper",
        "visual_reference": "local-helper-reference.png",
        "gender": "male",
    },
    "neighbor": {
        "character_id": "friend",
        "visual_reference": "friend-reference.png",
        "gender": "male",
    },
    "pharmacist": {
        "character_id": "pharmacist",
        "visual_reference": "pharmacist-reference.png",
        "gender": "male",
    },
    "receptionist": {
        "character_id": "staff",
        "visual_reference": "staff-reference.png",
        "gender": "male",
    },
    "server": {
        "character_id": "vendor",
        "visual_reference": "vendor-reference.png",
        "gender": "female",
    },
    "shopkeeper": {
        "character_id": "vendor",
        "visual_reference": "vendor-reference.png",
        "gender": "female",
    },
    "staff": {
        "character_id": "staff",
        "visual_reference": "staff-reference.png",
        "gender": "male",
    },
    "station_helper": {
        "character_id": "staff",
        "visual_reference": "staff-reference.png",
        "gender": "male",
    },
    "vendor": {
        "character_id": "vendor",
        "visual_reference": "vendor-reference.png",
        "gender": "female",
    },
}


def character_for_role(speaker_role: str) -> dict[str, str]:
    character = CHARACTER_BY_ROLE.get(speaker_role) or CHARACTER_BY_ROLE[DEFAULT_CHARACTER_ID]
    return {
        **character,
        "speaker_role": speaker_role,
    }


def partner_character_for_scene(scene: dict[str, Any]) -> dict[str, str]:
    for character in scene.get("characters", []):
        role = str(character.get("role", ""))
        if role and role != "learner":
            return character_for_role(role)
    return character_for_role(DEFAULT_CHARACTER_ID)
