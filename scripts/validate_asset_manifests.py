"""Validate generated audio and visual asset manifests."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from content_assets import iter_dialogue_lines, list_language_dirs, load_language_data, path_exists, read_json


def line_key(dialogue_id: str, line_index: int) -> tuple[str, int]:
    return dialogue_id, line_index


def validate_language(
    data_dir: Path,
    project_dir: Path,
    language: str,
    require_generated: bool,
) -> list[str]:
    errors: list[str] = []
    language_dir = data_dir / "languages" / language
    _, dialogues_payload = load_language_data(data_dir, language)

    spoken_lines = {
        line_key(dialogue["id"], line["index"])
        for dialogue, line in iter_dialogue_lines(dialogues_payload)
        if line.get("text", "").strip()
    }
    all_lines = {
        line_key(dialogue["id"], line["index"])
        for dialogue, line in iter_dialogue_lines(dialogues_payload)
    }

    audio_path = language_dir / "audio_assets.json"
    visual_path = language_dir / "visual_prompts.json"
    if not audio_path.exists():
        errors.append(f"{language}: missing audio_assets.json")
        audio_assets: list[dict[str, Any]] = []
    else:
        audio_assets = read_json(audio_path).get("assets", [])

    if not visual_path.exists():
        errors.append(f"{language}: missing visual_prompts.json")
        visual_prompts: list[dict[str, Any]] = []
    else:
        visual_prompts = read_json(visual_path).get("prompts", [])

    audio_keys = {line_key(item["dialogue_id"], item["line_index"]) for item in audio_assets}
    visual_keys = {line_key(item["dialogue_id"], item["line_index"]) for item in visual_prompts}

    missing_audio = sorted(spoken_lines - audio_keys)
    extra_audio = sorted(audio_keys - spoken_lines)
    missing_visual = sorted(all_lines - visual_keys)
    extra_visual = sorted(visual_keys - all_lines)

    for key in missing_audio:
        errors.append(f"{language}: missing audio asset for {key[0]} line {key[1]}")
    for key in extra_audio:
        errors.append(f"{language}: audio asset references unknown spoken line {key[0]} line {key[1]}")
    for key in missing_visual:
        errors.append(f"{language}: missing visual prompt for {key[0]} line {key[1]}")
    for key in extra_visual:
        errors.append(f"{language}: visual prompt references unknown line {key[0]} line {key[1]}")

    if require_generated:
        for item in audio_assets:
            if not path_exists(project_dir, item["audio_path"]):
                errors.append(f"{language}: missing generated audio file {item['audio_path']}")
        for item in visual_prompts:
            if not path_exists(project_dir, item["image_path"]):
                errors.append(f"{language}: missing generated image file {item['image_path']}")

    audio_status = Counter(item.get("status", "") for item in audio_assets)
    visual_status = Counter(item.get("status", "") for item in visual_prompts)
    print(
        f"{language}: audio={len(audio_assets)} {dict(audio_status)}; "
        f"visual={len(visual_prompts)} {dict(visual_status)}"
    )
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to validate. Repeatable.")
    parser.add_argument("--require-generated", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]

    errors: list[str] = []
    for language in languages:
        errors.extend(validate_language(data_dir, project_dir, language, args.require_generated))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("Asset manifests are structurally valid.")


if __name__ == "__main__":
    main()
