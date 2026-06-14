"""Regenerate dialogue and backward-build audio for one-please food order content."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

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

LANGS = ["en", "ja", "zh", "yue", "ta"]
FOOD_DIALOGUE_SUFFIXES = (
    "order-local-food",
    "order-convenience-transfer",
    "order-bakery-review",
)
FOOD_TARGET_ID = {
    "en": "en-target-one-local-food-please",
    "ja": "ja-target-one-local-food-please",
    "zh": "zh-target-one-local-food-please",
    "yue": "yue-target-one-local-food-please",
    "ta": "ta-target-one-local-food-please",
}


def food_dialogue_ids(language: str) -> set[str]:
    return {f"{language}-{suffix}" for suffix in FOOD_DIALOGUE_SUFFIXES}


def tts_text_for_line(line: dict) -> str:
    for key in ("tts_text", "text", "transliteration", "audio_text"):
        value = line.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def sync_food_learner_manifest_entries(*, data_dir: Path, language: str) -> int:
    language_dir = data_dir / "languages" / language
    dialogues = {
        dialogue["id"]: dialogue
        for dialogue in read_json(language_dir / "dialogues.json").get("dialogues", [])
    }
    manifest_path = language_dir / "audio_assets.json"
    manifest = read_json(manifest_path)
    updated = 0
    target_ids = food_dialogue_ids(language)

    for item in manifest.get("assets", []):
        dialogue_id = str(item.get("dialogue_id", ""))
        if dialogue_id not in target_ids:
            continue
        if item.get("line_type") != "learner_target":
            continue

        dialogue = dialogues.get(dialogue_id)
        if not dialogue:
            continue
        line = next(
            (
                candidate
                for candidate in dialogue.get("lines", [])
                if candidate.get("line_type") == "learner_target"
            ),
            None,
        )
        if not line:
            continue

        spoken = tts_text_for_line(line)
        if not spoken:
            continue

        if item.get("text") != spoken:
            item["text"] = spoken
            updated += 1
        transliteration = line.get("transliteration") or line.get("audio_text") or ""
        if item.get("transliteration") != transliteration:
            item["transliteration"] = transliteration
            updated += 1

    if updated:
        write_json(manifest_path, manifest)
    return updated


async def regenerate_food_dialogue_lines(*, data_dir: Path, project_dir: Path, language: str) -> int:
    manifest = read_json(data_dir / "languages" / language / "audio_assets.json")
    target_ids = food_dialogue_ids(language)
    created = 0

    for item in manifest.get("assets", []):
        if item.get("dialogue_id") not in target_ids:
            continue
        if item.get("line_type") != "learner_target":
            continue
        if not str(item.get("text", "")).strip():
            continue

        profile = item.get("voice_profile") or voice_profile_for(language, item.get("speaker_role", ""))
        audio_path = item["audio_path"]
        await synthesize_mp3(
            text=str(item["text"]),
            voice=profile["provider_voice"],
            rate=profile.get("rate", "+0%"),
            pitch=profile.get("pitch", "+0Hz"),
            out_path=repo_file_for_relative_path(project_dir, audio_path),
        )
        created += 1
        print(f"{language}: dialogue {audio_path} ({item['text']})")

    return created


async def regenerate_food_backward_build(*, data_dir: Path, project_dir: Path, language: str) -> int:
    targets_payload = read_json(data_dir / "languages" / language / "targets.json")
    target_id = FOOD_TARGET_ID[language]
    target = next(item for item in targets_payload.get("targets", []) if item["id"] == target_id)
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
    total_manifest_updates = 0
    total_dialogue = 0
    total_backward = 0

    for language in LANGS:
        total_manifest_updates += sync_food_learner_manifest_entries(
            data_dir=data_dir,
            language=language,
        )
        total_dialogue += await regenerate_food_dialogue_lines(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
        )
        total_backward += await regenerate_food_backward_build(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
        )

    print(
        f"Done. manifest fields updated: {total_manifest_updates}, "
        f"dialogue mp3s: {total_dialogue}, backward-build mp3s: {total_backward}"
    )


if __name__ == "__main__":
    asyncio.run(main())
