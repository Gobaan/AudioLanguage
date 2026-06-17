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
        sort_order = 999
        if targets_path.exists():
            targets_data = read_json(targets_path)
            display_name = str(targets_data.get("display_name", display_name))
            metadata = targets_data.get("metadata", {})
            if isinstance(metadata, dict):
                description = str(metadata.get("description", ""))
                raw_scene_sets = metadata.get("scene_sets", ["mvp"])
                if isinstance(raw_scene_sets, list) and raw_scene_sets:
                    scene_sets = [str(scene_set) for scene_set in raw_scene_sets]
                raw_sort_order = metadata.get("sort_order")
                if isinstance(raw_sort_order, int):
                    sort_order = raw_sort_order

        languages.append(
            {
                "id": language_dir.name,
                "display_name": display_name,
                "description": description,
                "scene_sets": scene_sets,
                "sort_order": sort_order,
            }
        )

    languages.sort(key=lambda item: (item.get("sort_order", 999), item["id"]))
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
    card_templates_data = read_json(data_dir / "curriculum" / "card_templates.json")
    card_templates = index_by_id(card_templates_data, "card_templates")
    support_ui_labels = card_templates_data.get("support_ui_labels", {})
    targets_data = read_json(language_dir / "targets.json")
    dialogues_data = read_json(language_dir / "dialogues.json")
    practice_data = read_json(language_dir / "practice_cards.json")
    visual_data = read_json(language_dir / "visual_beats.json")
    distractors = load_distractors(data_dir, language_dir)
    audio_assets = load_audio_assets(language_dir)

    targets = index_by_id(targets_data, "targets")
    english_targets = english_targets_lookup(data_dir)
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
                english_targets=english_targets,
                dialogues=dialogues,
                visual_beats=visual_beats,
                distractors=distractors,
                audio_assets=audio_assets,
                project_dir=project_dir,
                support_ui_labels=support_ui_labels,
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
    english_targets: dict[str, dict[str, dict[str, Any]]],
    dialogues: dict[str, dict[str, Any]],
    visual_beats: list[dict[str, Any]],
    distractors: dict[str, dict[str, Any]],
    audio_assets: dict[tuple[str, int], str],
    project_dir: Path,
    support_ui_labels: dict[str, Any],
) -> dict[str, Any]:
    dialogue = required(dialogues, card.get("dialogue_id"), "dialogue")
    target = required(targets, card.get("target_id"), "target")
    english_target = english_target_for(target, english_targets)
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
        "english_target": english_target,
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

    hydrated_card["ui_labels"] = ui_labels_for_card(
        card=card,
        template=template,
        support_ui_labels=support_ui_labels,
    )

    return hydrated_card


def english_targets_lookup(data_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    english_targets_path = data_dir / "languages" / "en" / "targets.json"
    if not english_targets_path.exists():
        return {"by_slug": {}, "by_function": {}}

    targets_data = read_json(english_targets_path)
    by_slug: dict[str, dict[str, Any]] = {}
    by_function: dict[str, dict[str, Any]] = {}
    for target in targets_data.get("targets", []):
        target_slug = target_id_slug(str(target.get("id", "")))
        if target_slug:
            by_slug[target_slug] = target
        function_id = str(target.get("function_id", ""))
        if function_id and function_id not in by_function:
            by_function[function_id] = target
    return {"by_slug": by_slug, "by_function": by_function}


def english_target_for(
    target: dict[str, Any],
    english_targets: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any] | None:
    target_slug = target_id_slug(str(target.get("id", "")))
    function_id = str(target.get("function_id", ""))
    return english_targets["by_slug"].get(target_slug) or english_targets["by_function"].get(function_id)


def target_id_slug(target_id: str) -> str:
    if "-target-" not in target_id:
        return target_id
    return target_id.split("-target-", 1)[1]


def ui_labels_for_card(
    *,
    card: dict[str, Any],
    template: dict[str, Any] | None,
    support_ui_labels: dict[str, Any],
) -> dict[str, dict[str, str]]:
    support_language = str(card.get("ai_scene_contract", {}).get("support_language", "English"))
    sources = [
        support_ui_labels.get(support_language, {}),
        template.get("default_ui_labels", {}) if template else {},
        card.get("ai_scene_contract", {}).get("ui_labels", {}),
    ]
    merged: dict[str, dict[str, str]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in ("audio", "mic"):
            labels = source.get(key)
            if isinstance(labels, dict):
                merged[key] = {**merged.get(key, {}), **{str(label): str(value) for label, value in labels.items()}}
    return merged


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
