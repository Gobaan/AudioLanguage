"""Shared helpers for content asset manifest scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from project_config.paths import repo_file_for_relative_path

DEFAULT_DATA_DIR = "model/content"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def list_language_dirs(data_dir: Path) -> list[Path]:
    languages_dir = data_dir / "languages"
    if not languages_dir.exists():
        return []
    return sorted(path for path in languages_dir.iterdir() if path.is_dir())


def load_curriculum(data_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    functions = read_json(data_dir / "curriculum" / "functions.json")["functions"]
    scenes = read_json(data_dir / "curriculum" / "scenes.json")["scenes"]
    return (
        {item["id"]: item for item in functions},
        {item["id"]: item for item in scenes},
    )


def load_language_data(data_dir: Path, language: str) -> tuple[dict[str, Any], dict[str, Any]]:
    language_dir = data_dir / "languages" / language
    targets_payload = read_json(language_dir / "targets.json")
    dialogues_payload = read_json(language_dir / "dialogues.json")
    return targets_payload, dialogues_payload


def iter_dialogue_lines(dialogues_payload: dict[str, Any]):
    for dialogue in dialogues_payload.get("dialogues", []):
        for line in dialogue.get("lines", []):
            yield dialogue, line


def relative_posix(path: Path) -> str:
    return path.as_posix()


def asset_folder_slug(value: str) -> str:
    parts = value.split("-", 1)
    if len(parts) == 2 and parts[0] in {"en", "es", "fr", "ja", "ta", "yue", "zh"}:
        return parts[1]
    return value


def audio_path_candidates(
    language: str,
    dialogue_id: str,
    line_index: int,
    asset_slug: str | None = None,
) -> list[str]:
    folder_slugs: list[str] = []
    for value in (asset_slug, dialogue_id, asset_folder_slug(dialogue_id)):
        if value and value not in folder_slugs:
            folder_slugs.append(value)

    candidates: list[str] = []
    seen: set[str] = set()
    for slug in folder_slugs:
        for candidate in (
            relative_posix(Path("audio") / "generated" / language / slug / f"line-{line_index}.mp3"),
            relative_posix(Path("audio") / f"{slug}-{line_index}.mp3"),
        ):
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    return candidates


def resolve_audio_path(
    project_dir: Path,
    language: str,
    dialogue: dict[str, Any],
    line: dict[str, Any],
) -> tuple[str, str]:
    dialogue_id = str(dialogue["id"])
    asset_slug = dialogue.get("asset_slug")
    if line.get("audio_path"):
        audio_path = str(line["audio_path"])
        status = "generated" if path_exists(project_dir, audio_path) else "needs_generation"
        return audio_path, status

    candidates = audio_path_candidates(language, dialogue_id, int(line["index"]), asset_slug)
    for candidate in candidates:
        if path_exists(project_dir, candidate):
            return candidate, "generated"

    return candidates[0], "needs_generation"


def path_exists(project_dir: Path, relative_path: str) -> bool:
    path = repo_file_for_relative_path(project_dir, relative_path)
    return path.exists() and path.stat().st_size > 0
