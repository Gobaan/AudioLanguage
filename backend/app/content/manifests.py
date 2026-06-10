from __future__ import annotations

from pathlib import Path
from typing import Any

from app.content.graph_core import DataGraphError, read_json


def load_audio_assets(language_dir: Path) -> dict[tuple[str, int], str]:
    manifest_path = language_dir / "audio_assets.json"
    if not manifest_path.exists():
        return {}

    manifest = read_json(manifest_path)
    assets: dict[tuple[str, int], str] = {}
    for item in manifest.get("assets", []):
        dialogue_id = item.get("dialogue_id")
        line_index = item.get("line_index")
        audio_path = item.get("audio_path")
        if dialogue_id is None or line_index is None or not audio_path:
            continue
        key = (str(dialogue_id), int(line_index))
        assets[key] = str(audio_path)
    return assets


def load_distractors(data_dir: Path, language_dir: Path) -> dict[str, dict[str, Any]]:
    if not language_dir.exists():
        raise DataGraphError(f"Language '{language_dir.name}' not found")

    distractors = load_curriculum_distractors(data_dir)
    distractor_path = language_dir / "distractor.json"
    if not distractor_path.exists():
        return distractors

    distractor_data = read_json(distractor_path)
    for item in distractor_data.get("dialogue_distractors", []):
        dialogue_id = item.get("dialogue_id")
        if dialogue_id:
            distractors[str(dialogue_id)] = item
    return distractors


def load_curriculum_distractors(data_dir: Path) -> dict[str, dict[str, Any]]:
    distractor_path = data_dir / "curriculum" / "distractors.json"
    if not distractor_path.exists():
        return {}

    distractor_data = read_json(distractor_path)
    distractors: dict[str, dict[str, Any]] = {}
    for item in distractor_data.get("function_distractors", []):
        function_id = item.get("function_id")
        if function_id:
            distractors[str(function_id)] = item
    for item in distractor_data.get("dialogue_distractors", []):
        dialogue_id = item.get("dialogue_id")
        if dialogue_id:
            distractors[str(dialogue_id)] = item
    return distractors
