"""Shared helpers for content asset manifest scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def path_exists(project_dir: Path, relative_path: str) -> bool:
    return (project_dir / relative_path).exists()
