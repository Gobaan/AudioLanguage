"""Resolve full learner-line dialogue audio for scorecards and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.content.graph_core import read_json
from app.content.manifests import load_audio_assets
from app.content.session_hydration import hydrate_line


def learner_dialogue_audio_url(
    *,
    language: str,
    target_id: str,
    data_dir: Path,
    project_dir: Path,
) -> str | None:
    language_dir = data_dir / "languages" / language
    if not language_dir.exists():
        return None

    practice_data = read_json(language_dir / "practice_cards.json")
    dialogues_data = read_json(language_dir / "dialogues.json")
    visual_data = read_json(language_dir / "visual_beats.json")
    dialogues = {dialogue["id"]: dialogue for dialogue in dialogues_data.get("dialogues", [])}
    audio_assets = load_audio_assets(language_dir)
    visual_beats = visual_data.get("visual_beats", [])

    dialogue_id = _dialogue_id_for_target(practice_data.get("practice_cards", []), target_id)
    if not dialogue_id:
        return None

    dialogue = dialogues.get(dialogue_id)
    if not dialogue:
        return None

    asset_slug = str(dialogue.get("asset_slug") or dialogue.get("id"))
    for line in dialogue.get("lines", []):
        if line.get("line_type") != "learner_target":
            continue
        hydrated = hydrate_line(
            line=line,
            dialogue_id=dialogue_id,
            asset_slug=asset_slug,
            visual_beats=visual_beats,
            audio_assets=audio_assets,
            project_dir=project_dir,
        )
        audio = hydrated.get("audio")
        if isinstance(audio, str) and audio.strip():
            return audio.strip()
    return None


def _dialogue_id_for_target(practice_cards: list[dict[str, Any]], target_id: str) -> str | None:
    for card in practice_cards:
        if card.get("target_id") == target_id and card.get("dialogue_id"):
            return str(card["dialogue_id"])
    return None
