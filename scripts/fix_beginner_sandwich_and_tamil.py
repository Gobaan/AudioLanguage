"""Simplify beginner sandwich and Tamil MVP phrases, then regenerate learner audio."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from app.content.lesson_steps import (  # noqa: E402
    backward_build_audio_relative_path,
    backward_build_entry_spoken_text,
    backward_build_indices,
    backward_build_units,
)
from content_assets import DEFAULT_DATA_DIR, read_json, write_json  # noqa: E402
from generate_backward_build_audio import spoken_phrase_for_target, synthesize_mp3  # noqa: E402
from project_config.paths import repo_file_for_relative_path  # noqa: E402
from voice_registry import voice_profile_for  # noqa: E402


PHRASE_UPDATES: dict[str, dict[str, Any]] = {
    "en-target-one-local-food-please": {
        "language": "en",
        "canonical": "This one.",
        "transliteration": "This one.",
        "display_meaning": "This one.",
        "meaning_units": ["this_one"],
        "meaning_unit_labels": {"this_one": "This one"},
        "accepted_variants": ["This one.", "This one", "This, please.", "This one, please."],
        "valid_but_off_target": ["This, please.", "This one, please."],
        "wrong_for_context_examples": ["I don't understand.", "My name is Anna."],
        "spoken_target": "this one; sandwich is scene-visible only",
        "backward_build_units": ["This", "one"],
        "backward_build_spoken_prompts": ["one.", "This one."],
        "dialogue_suffixes": ("order-local-food", "order-convenience-transfer", "order-bakery-review"),
        "tts_text": "This one.",
    },
    "ja-target-one-local-food-please": {
        "language": "ja",
        "canonical": "これ。",
        "transliteration": "Kore.",
        "display_meaning": "This one.",
        "meaning_units": ["this_one"],
        "meaning_unit_labels": {"this_one": "This one"},
        "accepted_variants": ["これ。", "これ", "Kore.", "Kore"],
        "valid_but_off_target": ["これください。"],
        "wrong_for_context_examples": ["わかりません。", "アンナです。"],
        "spoken_target": "this one; sandwich is scene-visible only",
        "backward_build_units": ["Kore"],
        "backward_build_spoken_prompts": ["これ。"],
        "dialogue_suffixes": ("order-local-food", "order-convenience-transfer", "order-bakery-review"),
        "tts_text": "これ。",
    },
    "zh-target-one-local-food-please": {
        "language": "zh",
        "canonical": "这个。",
        "transliteration": "Zhe ge.",
        "display_meaning": "This one.",
        "meaning_units": ["this_one"],
        "meaning_unit_labels": {"this_one": "This one"},
        "accepted_variants": ["这个。", "这个", "Zhe ge.", "Zhe ge"],
        "valid_but_off_target": ["这个，谢谢。"],
        "wrong_for_context_examples": ["我不懂。", "我叫Anna。"],
        "spoken_target": "this one; sandwich is scene-visible only",
        "backward_build_units": ["Zhe", "ge"],
        "backward_build_spoken_prompts": ["个。", "这个。"],
        "dialogue_suffixes": ("order-local-food", "order-convenience-transfer", "order-bakery-review"),
        "tts_text": "这个。",
    },
    "yue-target-one-local-food-please": {
        "language": "yue",
        "canonical": "呢個。",
        "transliteration": "Ni go.",
        "display_meaning": "This one.",
        "meaning_units": ["this_one"],
        "meaning_unit_labels": {"this_one": "This one"},
        "accepted_variants": ["呢個。", "呢個", "Ni go.", "Ni go"],
        "valid_but_off_target": ["呢個，唔該。"],
        "wrong_for_context_examples": ["我唔明。", "我叫Anna。"],
        "spoken_target": "this one; sandwich is scene-visible only",
        "backward_build_units": ["Ni", "go"],
        "backward_build_spoken_prompts": ["個。", "呢個。"],
        "dialogue_suffixes": ("order-local-food", "order-convenience-transfer", "order-bakery-review"),
        "tts_text": "呢個。",
    },
    "ta-target-one-local-food-please": {
        "language": "ta",
        "canonical": "இது.",
        "transliteration": "Idhu.",
        "display_meaning": "This one.",
        "meaning_units": ["this_one"],
        "meaning_unit_labels": {"this_one": "This one"},
        "accepted_variants": ["இது.", "இது", "Idhu.", "Idhu"],
        "valid_but_off_target": ["இது, தயவு செய்து."],
        "wrong_for_context_examples": ["எனக்கு புரியவில்லை.", "என் பெயர் அன்னா."],
        "spoken_target": "this one; sandwich is scene-visible only",
        "backward_build_units": ["Idhu"],
        "backward_build_spoken_prompts": ["இது."],
        "dialogue_suffixes": ("order-local-food", "order-convenience-transfer", "order-bakery-review"),
        "tts_text": "இது.",
    },
    "ta-target-respond-hi": {
        "language": "ta",
        "canonical": "வணக்கம்!",
        "transliteration": "Vanakkam!",
        "display_meaning": "Hello.",
        "meaning_units": ["hello"],
        "meaning_unit_labels": {"hello": "Hello"},
        "accepted_variants": ["வணக்கம்.", "Vanakkam.", "Vanakkam!"],
        "valid_but_off_target": [],
        "wrong_for_context_examples": ["மன்னிக்கவும்.", "இது."],
        "spoken_target": "hello",
        "backward_build_units": ["Vanakkam"],
        "backward_build_spoken_prompts": ["வணக்கம்!"],
        "dialogue_suffixes": ("first-hi-response", "greeting-neighbor-transfer", "greeting-entry-review"),
        "tts_text": "வணக்கம்!",
    },
    "ta-target-i-dont-understand": {
        "language": "ta",
        "canonical": "புரியல.",
        "transliteration": "Puriyala.",
        "display_meaning": "I don't understand.",
        "meaning_units": ["not_understand"],
        "meaning_unit_labels": {"not_understand": "I don't understand"},
        "accepted_variants": ["புரியல.", "Puriyala.", "Enakku puriyala."],
        "valid_but_off_target": ["மன்னிக்கவும், எனக்கு புரியவில்லை."],
        "wrong_for_context_examples": ["வணக்கம்.", "இது."],
        "spoken_target": "I do not understand",
        "backward_build_units": ["Puriyala"],
        "backward_build_spoken_prompts": ["புரியல."],
        "dialogue_suffixes": ("repair-dont-understand", "repair-ticket-transfer", "repair-clinic-review"),
        "tts_text": "புரியல.",
    },
}


def dialogue_ids(language: str, suffixes: tuple[str, ...]) -> set[str]:
    return {f"{language}-{suffix}" for suffix in suffixes}


def update_target(target: dict[str, Any], update: dict[str, Any]) -> bool:
    changed = False
    for key in (
        "canonical",
        "transliteration",
        "display_meaning",
        "meaning_units",
        "accepted_variants",
        "valid_but_off_target",
        "wrong_for_context_examples",
        "backward_build_units",
        "backward_build_spoken_prompts",
    ):
        value = update.get(key)
        if value is not None and target.get(key) != value:
            target[key] = value
            changed = True

    labels = update.get("meaning_unit_labels")
    if labels is not None:
        target.setdefault("support", {})
        if target["support"].get("meaning_unit_labels") != labels:
            target["support"]["meaning_unit_labels"] = labels
            changed = True

    notes = target.setdefault("notes", {})
    if notes.get("spoken_target") != update["spoken_target"]:
        notes["spoken_target"] = update["spoken_target"]
        changed = True

    return changed


def line_fields(update: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": update["canonical"],
        "transliteration": update["transliteration"],
        "audio_text": update["transliteration"],
        "tts_text": update["tts_text"],
        "meaning_units": update["meaning_units"],
    }


def update_dialogues(language_dir: Path, target_id: str, update: dict[str, Any]) -> int:
    path = language_dir / "dialogues.json"
    data = read_json(path)
    changes = 0
    fields = line_fields(update)
    ids = dialogue_ids(update["language"], update["dialogue_suffixes"])

    for dialogue in data.get("dialogues", []):
        if dialogue.get("id") not in ids and dialogue.get("target_id") != target_id:
            continue
        if dialogue.get("id") in ids and dialogue.get("target_id") != target_id:
            dialogue["target_id"] = target_id
            changes += 1
        for line in dialogue.get("lines", []):
            if line.get("line_type") != "learner_target":
                continue
            if line.get("target_id") != target_id:
                line["target_id"] = target_id
                changes += 1
            for key, value in fields.items():
                if line.get(key) != value:
                    line[key] = value
                    changes += 1

    if changes:
        write_json(path, data)
    return changes


def update_practice_cards(language_dir: Path, target_id: str, update: dict[str, Any]) -> int:
    path = language_dir / "practice_cards.json"
    data = read_json(path)
    changes = 0
    expected = update["tts_text"]
    transliteration = update["transliteration"]
    accepted = update["accepted_variants"]

    for card in data.get("practice_cards", []):
        if card.get("target_id") != target_id:
            continue
        if card.get("expected_response") != expected:
            card["expected_response"] = expected
            changes += 1
        if card.get("expected_transliteration") != transliteration:
            card["expected_transliteration"] = transliteration
            changes += 1
        scoring = card.get("scoring")
        if isinstance(scoring, dict):
            if scoring.get("accepted_responses") != accepted:
                scoring["accepted_responses"] = accepted
                changes += 1
            notes = scoring.get("notes")
            if isinstance(notes, list):
                new_notes = [
                    note.replace("one + please", "this one")
                    .replace("one plus please", "this one")
                    .replace("one and please", "this one")
                    for note in notes
                ]
                if notes != new_notes:
                    scoring["notes"] = new_notes
                    changes += 1
        contract = card.get("ai_scene_contract")
        if isinstance(contract, dict):
            examples = update["accepted_variants"]
            if contract.get("example_valid_responses") != examples:
                contract["example_valid_responses"] = examples
                changes += 1
            notes = ["Accept the target phrase for choosing the visible sandwich/item in the scene."]
            if contract.get("acceptance_notes") != notes:
                contract["acceptance_notes"] = notes
                changes += 1
            if target_id.endswith("one-local-food-please"):
                if contract.get("learner_role") != "customer choosing a visible sandwich":
                    contract["learner_role"] = "customer choosing a visible sandwich"
                    changes += 1
                if contract.get("learner_intention") != "Point to the visible sandwich/item and say this one.":
                    contract["learner_intention"] = "Point to the visible sandwich/item and say this one."
                    changes += 1
                required = contract.get("required_slots")
                if isinstance(required, dict):
                    new_required = {
                        "speech_act": "choose_visible_item",
                        "visible_item": "counter_display",
                    }
                    if required != new_required:
                        contract["required_slots"] = new_required
                        changes += 1
                target_function = contract.get("target_function")
                if isinstance(target_function, dict):
                    definition = "The learner chooses a visible food item."
                    if target_function.get("definition") != definition:
                        target_function["definition"] = definition
                        changes += 1

        signal = card.get("success_signal")
        if isinstance(signal, str):
            new_signal = signal.replace("ja-target-one-local-food-please", target_id)
            new_signal = new_signal.replace("one + please", "this one")
            new_signal = new_signal.replace("orders a simple food item politely", "chooses the visible sandwich/item")
            if new_signal != signal:
                card["success_signal"] = new_signal
                changes += 1

    if changes:
        write_json(path, data)
    return changes


def update_visual_beats(language_dir: Path, target_id: str, update: dict[str, Any]) -> int:
    path = language_dir / "visual_beats.json"
    if not path.exists():
        return 0
    data = read_json(path)
    changes = 0
    ids = dialogue_ids(update["language"], update["dialogue_suffixes"])
    for beat in data.get("visual_beats", []):
        if beat.get("dialogue_id") not in ids and beat.get("target_id") != target_id:
            continue
        if beat.get("dialogue_id") in ids and beat.get("target_id") != target_id:
            beat["target_id"] = target_id
            changes += 1
        if beat.get("line_text") != update["transliteration"]:
            beat["line_text"] = update["transliteration"]
            changes += 1
        if beat.get("line_meaning") != update["display_meaning"]:
            beat["line_meaning"] = update["display_meaning"]
            changes += 1
    if changes:
        write_json(path, data)
    return changes


def update_audio_manifest(language_dir: Path, language: str, update: dict[str, Any]) -> int:
    path = language_dir / "audio_assets.json"
    data = read_json(path)
    changes = 0
    ids = dialogue_ids(language, update["dialogue_suffixes"])
    for item in data.get("assets", []):
        if item.get("dialogue_id") not in ids or item.get("line_type") != "learner_target":
            continue
        if item.get("target_id") != update["target_id"]:
            item["target_id"] = update["target_id"]
            changes += 1
        if item.get("text") != update["tts_text"]:
            item["text"] = update["tts_text"]
            changes += 1
        if item.get("transliteration") != update["transliteration"]:
            item["transliteration"] = update["transliteration"]
            changes += 1
    if changes:
        write_json(path, data)
    return changes


def update_language_content(data_dir: Path, target_id: str, update: dict[str, Any]) -> int:
    language = update["language"]
    update["target_id"] = target_id
    language_dir = data_dir / "languages" / language
    changes = 0

    targets_path = language_dir / "targets.json"
    targets_data = read_json(targets_path)
    target = next(item for item in targets_data["targets"] if item["id"] == target_id)
    if update_target(target, update):
        write_json(targets_path, targets_data)
        changes += 1

    changes += update_dialogues(language_dir, target_id, update)
    changes += update_practice_cards(language_dir, target_id, update)
    changes += update_visual_beats(language_dir, target_id, update)
    changes += update_audio_manifest(language_dir, language, update)
    return changes


async def regenerate_dialogue_audio(data_dir: Path, project_dir: Path, language: str, update: dict[str, Any]) -> int:
    manifest = read_json(data_dir / "languages" / language / "audio_assets.json")
    ids = dialogue_ids(language, update["dialogue_suffixes"])
    created = 0
    for item in manifest.get("assets", []):
        if item.get("dialogue_id") not in ids or item.get("line_type") != "learner_target":
            continue
        profile = item.get("voice_profile") or voice_profile_for(language, item.get("speaker_role", ""))
        await synthesize_mp3(
            text=str(item["text"]),
            voice=profile["provider_voice"],
            rate=profile.get("rate", "+0%"),
            pitch=profile.get("pitch", "+0Hz"),
            out_path=repo_file_for_relative_path(project_dir, item["audio_path"]),
        )
        created += 1
        print(f"{language}: dialogue {item['audio_path']} ({item['text']})")
    return created


async def regenerate_backward_build(data_dir: Path, project_dir: Path, language: str, target_id: str) -> int:
    targets_payload = read_json(data_dir / "languages" / language / "targets.json")
    target = next(item for item in targets_payload["targets"] if item["id"] == target_id)
    profile = voice_profile_for(language, "learner")
    target_phrase = target.get("transliteration") or target.get("canonical") or ""
    units = backward_build_units(target=target, target_phrase=target_phrase)
    spoken_phrase = spoken_phrase_for_target(target)
    created = 0
    used_paths: set[str] = set()

    for build_index in backward_build_indices(len(units)):
        spoken_text = backward_build_entry_spoken_text(
            target=target,
            build_index=build_index,
            units=units,
            spoken_phrase=spoken_phrase,
        )
        if not spoken_text.strip():
            continue
        audio_path = backward_build_audio_relative_path(language, target_id, build_index)
        used_paths.add(audio_path)
        await synthesize_mp3(
            text=spoken_text,
            voice=profile["provider_voice"],
            rate=profile.get("rate", "+0%"),
            pitch=profile.get("pitch", "+0Hz"),
            out_path=repo_file_for_relative_path(project_dir, audio_path),
        )
        created += 1
        print(f"{language}: backward-build {audio_path} ({spoken_text})")

    bb_dir = repo_file_for_relative_path(
        project_dir,
        f"audio/generated/{language}/backward-build/{target_id}",
    )
    if bb_dir.exists():
        for path in bb_dir.glob("build-*.mp3"):
            relative_key = path.relative_to(project_dir / "model" / "assets" / "audio").as_posix()
            relative_key = f"audio/{relative_key}"
            if relative_key not in used_paths:
                path.unlink()
                print(f"{language}: removed stale {relative_key}")
    return created


async def main() -> None:
    data_dir = Path(DEFAULT_DATA_DIR)
    if not data_dir.is_absolute():
        data_dir = PROJECT_DIR / data_dir

    content_changes = 0
    dialogue_audio = 0
    backward_audio = 0

    for target_id, update in PHRASE_UPDATES.items():
        content_changes += update_language_content(data_dir, target_id, update)

    for target_id, update in PHRASE_UPDATES.items():
        language = update["language"]
        dialogue_audio += await regenerate_dialogue_audio(data_dir, PROJECT_DIR, language, update)
        backward_audio += await regenerate_backward_build(data_dir, PROJECT_DIR, language, target_id)

    print(
        f"Done. content updates: {content_changes}, "
        f"dialogue mp3s: {dialogue_audio}, backward-build mp3s: {backward_audio}"
    )


if __name__ == "__main__":
    asyncio.run(main())
