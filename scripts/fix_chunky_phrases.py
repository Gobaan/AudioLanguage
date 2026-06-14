"""Shorten flagged MVP repair/introduce phrases and regenerate their audio."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
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

INTRODUCE_SUFFIXES = (
    "introduce-self",
    "introduce-class-transfer",
    "introduce-community-review",
)
REPAIR_SUFFIXES = (
    "repair-dont-understand",
    "repair-ticket-transfer",
    "repair-clinic-review",
)

TARGET_UPDATES: dict[str, dict[str, Any]] = {
    "en-target-my-name-is": {
        "language": "en",
        "dialogue_suffixes": INTRODUCE_SUFFIXES,
        "canonical": "I'm Anna.",
        "transliteration": "I'm Anna.",
        "display_meaning": "My name is Anna.",
        "meaning_units": ["name", "proper_noun"],
        "accepted_variants": ["My name is Anna.", "My name is Ana."],
        "remove_keys": ["backward_build_spoken_prompts", "backward_build_units", "backward_build_focus_units"],
    },
    "en-target-i-dont-understand": {
        "language": "en",
        "dialogue_suffixes": REPAIR_SUFFIXES,
        "canonical": "I don't understand.",
        "transliteration": "I don't understand.",
        "display_meaning": "I don't understand.",
        "meaning_units": ["not", "understand"],
        "accepted_variants": ["Sorry, I don't understand.", "Sorry, I do not understand."],
        "remove_keys": ["backward_build_spoken_prompts", "backward_build_units", "backward_build_focus_units"],
    },
    "zh-target-i-dont-understand": {
        "language": "zh",
        "dialogue_suffixes": REPAIR_SUFFIXES,
        "canonical": "我不懂。",
        "transliteration": "Wo bu dong.",
        "display_meaning": "I don't understand.",
        "meaning_units": ["not", "understand"],
        "accepted_variants": ["Bu hao yisi, wo bu dong.", "Duibuqi, wo bu dong."],
        "backward_build_spoken_prompts": ["懂。", "不懂。", "我不懂。"],
        "backward_build_units": ["Wo", "bu", "dong"],
        "remove_keys": ["backward_build_focus_units"],
    },
    "yue-target-i-dont-understand": {
        "language": "yue",
        "dialogue_suffixes": REPAIR_SUFFIXES,
        "canonical": "我唔明。",
        "transliteration": "Ngo m ming.",
        "display_meaning": "I don't understand.",
        "meaning_units": ["not", "understand"],
        "accepted_variants": ["M goi, ngo m ming.", "M hou ji si, ngo m ming."],
        "backward_build_spoken_prompts": ["明。", "唔明。", "我唔明。"],
        "backward_build_units": ["Ngo", "m", "ming"],
        "remove_keys": ["backward_build_focus_units"],
    },
}


def dialogue_ids(language: str, suffixes: tuple[str, ...]) -> set[str]:
    return {f"{language}-{suffix}" for suffix in suffixes}


def apply_target_update(target: dict[str, Any], update: dict[str, Any]) -> None:
    for key in ("canonical", "transliteration", "display_meaning", "meaning_units", "accepted_variants"):
        if key in update:
            target[key] = update[key]
    if "backward_build_spoken_prompts" in update:
        target["backward_build_spoken_prompts"] = update["backward_build_spoken_prompts"]
    if "backward_build_units" in update:
        target["backward_build_units"] = update["backward_build_units"]
    for key in update.get("remove_keys", []):
        target.pop(key, None)


def learner_line_from_target(target: dict[str, Any], update: dict[str, Any]) -> dict[str, str]:
    canonical = str(update["canonical"])
    transliteration = str(update.get("transliteration") or canonical)
    return {
        "text": canonical,
        "transliteration": transliteration,
        "audio_text": transliteration,
        "tts_text": canonical,
    }


def update_language_content(*, data_dir: Path, target_id: str, update: dict[str, Any]) -> int:
    language = update["language"]
    language_dir = data_dir / "languages" / language
    changes = 0

    targets_path = language_dir / "targets.json"
    targets_data = read_json(targets_path)
    target = next(item for item in targets_data["targets"] if item["id"] == target_id)
    apply_target_update(target, update)
    write_json(targets_path, targets_data)
    changes += 1

    line_fields = learner_line_from_target(target, update)
    dialogues_path = language_dir / "dialogues.json"
    dialogues_data = read_json(dialogues_path)
    for dialogue in dialogues_data.get("dialogues", []):
        if dialogue.get("target_id") != target_id:
            continue
        for line in dialogue.get("lines", []):
            if line.get("line_type") != "learner_target":
                continue
            for key, value in line_fields.items():
                if line.get(key) != value:
                    line[key] = value
                    changes += 1
            if line.get("meaning_units") != update.get("meaning_units"):
                line["meaning_units"] = update["meaning_units"]
                changes += 1
    write_json(dialogues_path, dialogues_data)

    manifest_path = language_dir / "audio_assets.json"
    manifest = read_json(manifest_path)
    dialogue_filter = dialogue_ids(language, update["dialogue_suffixes"])
    for item in manifest.get("assets", []):
        if item.get("dialogue_id") not in dialogue_filter:
            continue
        if item.get("line_type") != "learner_target":
            continue
        if item.get("text") != line_fields["tts_text"]:
            item["text"] = line_fields["tts_text"]
            changes += 1
        if item.get("transliteration") != line_fields["transliteration"]:
            item["transliteration"] = line_fields["transliteration"]
            changes += 1
    write_json(manifest_path, manifest)

    beats_path = language_dir / "visual_beats.json"
    if beats_path.exists():
        beats_data = read_json(beats_path)
        for beat in beats_data.get("visual_beats", []):
            if beat.get("target_id") != target_id:
                continue
            if beat.get("line_text") != line_fields["transliteration"]:
                beat["line_text"] = line_fields["transliteration"]
                changes += 1
        write_json(beats_path, beats_data)

    cards_path = language_dir / "practice_cards.json"
    cards_data = read_json(cards_path)
    for card in cards_data.get("practice_cards", []):
        if card.get("target_id") != target_id:
            continue
        if card.get("expected_response") != line_fields["tts_text"]:
            card["expected_response"] = line_fields["tts_text"]
            changes += 1
    write_json(cards_path, cards_data)

    return changes


def tts_text_for_line(line: dict) -> str:
    for key in ("tts_text", "text", "transliteration", "audio_text"):
        value = line.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


async def regenerate_dialogue_learner_lines(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    dialogue_filter: set[str],
) -> int:
    manifest = read_json(data_dir / "languages" / language / "audio_assets.json")
    created = 0
    for item in manifest.get("assets", []):
        if item.get("dialogue_id") not in dialogue_filter:
            continue
        if item.get("line_type") != "learner_target":
            continue
        if not str(item.get("text", "")).strip():
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


async def regenerate_backward_build(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    target_id: str,
) -> int:
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
    project_dir = PROJECT_DIR

    content_changes = 0
    dialogue_audio = 0
    backward_audio = 0

    for target_id, update in TARGET_UPDATES.items():
        content_changes += update_language_content(data_dir=data_dir, target_id=target_id, update=update)

    for target_id, update in TARGET_UPDATES.items():
        language = update["language"]
        dialogue_audio += await regenerate_dialogue_learner_lines(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
            dialogue_filter=dialogue_ids(language, update["dialogue_suffixes"]),
        )
        backward_audio += await regenerate_backward_build(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
            target_id=target_id,
        )

    print(
        f"Done. content touches: {content_changes}, "
        f"dialogue mp3s: {dialogue_audio}, backward-build mp3s: {backward_audio}"
    )


if __name__ == "__main__":
    asyncio.run(main())
