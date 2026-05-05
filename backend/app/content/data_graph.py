from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataGraphError(ValueError):
    """Raised when the structured content graph cannot be loaded."""


def list_languages(data_dir: Path) -> list[dict[str, str]]:
    """Return available language folders with display names when present."""
    languages_dir = data_dir / "languages"
    if not languages_dir.exists():
        return []

    languages = []
    for language_dir in sorted(path for path in languages_dir.iterdir() if path.is_dir()):
        targets_path = language_dir / "targets.json"
        display_name = language_dir.name
        if targets_path.exists():
            targets_data = read_json(targets_path)
            display_name = str(targets_data.get("display_name", display_name))

        languages.append({"id": language_dir.name, "display_name": display_name})

    return languages


def load_language_session(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
) -> dict[str, Any]:
    """Load and hydrate one language session from the content graph."""
    language_dir = data_dir / "languages" / language
    if not language_dir.exists():
        raise DataGraphError(f"Language '{language}' not found")

    functions = index_by_id(read_json(data_dir / "curriculum" / "functions.json"), "functions")
    scenes = index_by_id(read_json(data_dir / "curriculum" / "scenes.json"), "scenes")
    review_modes = index_by_id(read_json(data_dir / "curriculum" / "review_modes.json"), "review_modes")
    targets_data = read_json(language_dir / "targets.json")
    dialogues_data = read_json(language_dir / "dialogues.json")
    practice_data = read_json(language_dir / "practice_cards.json")
    visual_data = read_json(language_dir / "visual_beats.json")
    audio_assets = load_audio_assets(language_dir)

    targets = index_by_id(targets_data, "targets")
    dialogues = index_by_id(dialogues_data, "dialogues")
    visual_beats = visual_data.get("visual_beats", [])

    cards = []
    practice_cards = {card["id"]: card for card in practice_data.get("practice_cards", [])}
    for card_id in practice_data.get("mvp_session", {}).get("cards", []):
        card = practice_cards.get(card_id)
        if card is None:
            raise DataGraphError(f"Practice card '{card_id}' not found")
        cards.append(
            hydrate_practice_card(
                card=card,
                functions=functions,
                scenes=scenes,
                review_modes=review_modes,
                targets=targets,
                dialogues=dialogues,
                visual_beats=visual_beats,
                audio_assets=audio_assets,
                project_dir=project_dir,
            )
        )

    return {
        "language": language,
        "display_name": targets_data.get("display_name", language),
        "script": targets_data.get("script"),
        "native_review_status": targets_data.get("native_review_status"),
        "session": practice_data.get("mvp_session", {}),
        "cards": cards,
    }


def hydrate_practice_card(
    *,
    card: dict[str, Any],
    functions: dict[str, dict[str, Any]],
    scenes: dict[str, dict[str, Any]],
    review_modes: dict[str, dict[str, Any]],
    targets: dict[str, dict[str, Any]],
    dialogues: dict[str, dict[str, Any]],
    visual_beats: list[dict[str, Any]],
    audio_assets: dict[tuple[str, int], str],
    project_dir: Path,
) -> dict[str, Any]:
    dialogue = required(dialogues, card.get("dialogue_id"), "dialogue")
    target = required(targets, card.get("target_id"), "target")
    function = required(functions, card.get("correct_function_id"), "function")
    scene = required(scenes, dialogue.get("scene_id"), "scene")
    review_mode = required(review_modes, card.get("mode"), "review mode")
    asset_slug = dialogue.get("asset_slug") or dialogue.get("id")

    hydrated_dialogue = {
        **dialogue,
        "lines": [
            hydrate_line(
                line=line,
                dialogue_id=str(dialogue["id"]),
                asset_slug=str(asset_slug),
                visual_beats=visual_beats,
                audio_assets=audio_assets,
                project_dir=project_dir,
            )
            for line in dialogue.get("lines", [])
        ],
    }

    return {
        **card,
        "function": function,
        "target": target,
        "scene": scene,
        "review_mode": review_mode,
        "dialogue": hydrated_dialogue,
    }


def hydrate_line(
    *,
    line: dict[str, Any],
    dialogue_id: str,
    asset_slug: str,
    visual_beats: list[dict[str, Any]],
    audio_assets: dict[tuple[str, int], str],
    project_dir: Path,
) -> dict[str, Any]:
    line_index = int(line.get("index", 0))
    beat = find_visual_beat(visual_beats, dialogue_id, line_index)
    beat_assets = beat.get("asset_paths", {}) if beat else {}
    audio_path = line.get("audio_path") or beat_assets.get("audio")
    image_path = beat_assets.get("image")

    if not audio_path:
        manifest_audio = audio_assets.get((dialogue_id, line_index))
        if manifest_audio and (project_dir / manifest_audio).exists():
            audio_path = manifest_audio

    if not audio_path:
        derived_audio = f"audio/{dialogue_id}-{line_index}.mp3"
        audio_path = derived_audio if (project_dir / derived_audio).exists() else None

    if not image_path:
        derived_image = f"visuals/{asset_slug}/frame-{line_index}.png"
        image_path = derived_image if (project_dir / derived_image).exists() else None

    return {
        **line,
        "audio": public_path(audio_path),
        "visual": public_path(image_path),
        "visual_beat": beat,
        "is_learner_target": line.get("line_type") == "learner_target",
    }


def find_visual_beat(
    visual_beats: list[dict[str, Any]],
    dialogue_id: str,
    line_index: int,
) -> dict[str, Any] | None:
    for beat in visual_beats:
        if beat.get("dialogue_id") == dialogue_id and int(beat.get("line_index", -1)) == line_index:
            return beat
    return None


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DataGraphError(f"Missing content file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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
        assets[(str(dialogue_id), int(line_index))] = str(audio_path)
    return assets


def index_by_id(data: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    items = data.get(key, [])
    return {str(item["id"]): item for item in items}


def required(
    items: dict[str, dict[str, Any]],
    item_id: str | None,
    label: str,
) -> dict[str, Any]:
    if item_id is None or item_id not in items:
        raise DataGraphError(f"Missing {label}: {item_id}")
    return items[item_id]


def public_path(path: str | None) -> str | None:
    if not path:
        return None
    return "/" + path.replace("\\", "/").lstrip("/")
