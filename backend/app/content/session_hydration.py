from __future__ import annotations

from pathlib import Path
from typing import Any

from app.content.asset_paths import find_visual_beat, resolve_line_assets
from app.content.graph_core import DataGraphError, index_by_id, read_json, required
from app.content.manifests import load_audio_assets, load_distractors


def list_languages(data_dir: Path) -> list[dict[str, Any]]:
    """Return available language folders with learner-facing metadata when present."""
    languages_dir = data_dir / "languages"
    if not languages_dir.exists():
        return []

    languages = []
    for language_dir in sorted(path for path in languages_dir.iterdir() if path.is_dir()):
        targets_path = language_dir / "targets.json"
        display_name = language_dir.name
        description = ""
        scene_sets = ["mvp"]
        if targets_path.exists():
            targets_data = read_json(targets_path)
            display_name = str(targets_data.get("display_name", display_name))
            metadata = targets_data.get("metadata", {})
            if isinstance(metadata, dict):
                description = str(metadata.get("description", ""))
                raw_scene_sets = metadata.get("scene_sets", ["mvp"])
                if isinstance(raw_scene_sets, list) and raw_scene_sets:
                    scene_sets = [str(scene_set) for scene_set in raw_scene_sets]

        languages.append(
            {
                "id": language_dir.name,
                "display_name": display_name,
                "description": description,
                "scene_sets": scene_sets,
            }
        )

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
    card_templates = index_by_id(read_json(data_dir / "curriculum" / "card_templates.json"), "card_templates")
    targets_data = read_json(language_dir / "targets.json")
    dialogues_data = read_json(language_dir / "dialogues.json")
    practice_data = read_json(language_dir / "practice_cards.json")
    visual_data = read_json(language_dir / "visual_beats.json")
    distractors = load_distractors(data_dir, language_dir)
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
                card_templates=card_templates,
                targets=targets,
                dialogues=dialogues,
                visual_beats=visual_beats,
                distractors=distractors,
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
    card_templates: dict[str, dict[str, Any]],
    targets: dict[str, dict[str, Any]],
    dialogues: dict[str, dict[str, Any]],
    visual_beats: list[dict[str, Any]],
    distractors: dict[str, dict[str, Any]],
    audio_assets: dict[tuple[str, int], str],
    project_dir: Path,
) -> dict[str, Any]:
    dialogue = required(dialogues, card.get("dialogue_id"), "dialogue")
    target = required(targets, card.get("target_id"), "target")
    function = required(functions, card.get("correct_function_id"), "function")
    scene = required(scenes, dialogue.get("scene_id"), "scene")
    review_mode = required(review_modes, card.get("mode"), "review mode")
    template = card_templates.get(str(card.get("template_id", "")))
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

    hydrated_card = {
        **card,
        "function": function,
        "target": target,
        "scene": scene,
        "review_mode": review_mode,
        "dialogue": hydrated_dialogue,
        "distractors": distractors.get(str(dialogue["id"])) or distractors.get(str(function["id"])),
    }
    if template:
        hydrated_card["template"] = template
        hydrated_card["support"] = {
            **template.get("default_support", {}),
            **card.get("support", {}),
        }

    return hydrated_card


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
    audio_path, image_path = resolve_line_assets(
        line=line,
        dialogue_id=dialogue_id,
        asset_slug=asset_slug,
        visual_beats=visual_beats,
        audio_assets=audio_assets,
        project_dir=project_dir,
    )

    return {
        **line,
        "audio_text": line.get("audio_text") or line.get("transliteration") or line.get("text"),
        "audio": audio_path,
        "visual": image_path,
        "visual_beat": beat,
        "is_learner_target": line.get("line_type") == "learner_target",
    }
