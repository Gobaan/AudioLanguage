"""Build per-language TTS asset manifests from dialogue content."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from content_assets import (
    DEFAULT_DATA_DIR,
    iter_dialogue_lines,
    list_language_dirs,
    load_curriculum,
    load_language_data,
    resolve_audio_path,
    write_json,
)
from character_cast import character_for_role, partner_character_for_scene
from voice_registry import character_voice_profile_for


def build_manifest(data_dir: Path, project_dir: Path, language: str) -> dict[str, Any]:
    _, scenes_by_id = load_curriculum(data_dir)
    _, dialogues_payload = load_language_data(data_dir, language)
    assets: list[dict[str, Any]] = []
    skipped_empty_text: list[dict[str, Any]] = []

    for dialogue, line in iter_dialogue_lines(dialogues_payload):
        text = (line.get("tts_text") or line.get("text", "")).strip()
        if not text:
            skipped_empty_text.append(
                {
                    "dialogue_id": dialogue["id"],
                    "line_index": line["index"],
                    "line_type": line.get("line_type", ""),
                }
            )
            continue

        audio_path, status = resolve_audio_path(project_dir, language, dialogue, line)
        speaker_role = str(line.get("speaker_role", ""))
        scene = scenes_by_id.get(dialogue.get("scene_id"), {})
        speaking_character = character_for_role(speaker_role)
        partner_character = partner_character_for_scene(scene)
        voice_profile = character_voice_profile_for(
            language,
            speaking_character["character_id"],
            speaker_role,
        )
        asset = {
            "id": f"{dialogue['id']}-line-{line['index']}",
            "language": language,
            "dialogue_id": dialogue["id"],
            "dialogue_type": dialogue.get("type", ""),
            "function_id": dialogue.get("function_id", ""),
            "target_id": line.get("target_id") or dialogue.get("target_id", ""),
            "scene_id": dialogue.get("scene_id", ""),
            "line_index": line["index"],
            "line_type": line.get("line_type", ""),
            "visual_prompt_id": f"{dialogue['id']}-frame-{line['index']}",
            "speaker_role": speaker_role,
            "character_id": speaking_character["character_id"],
            "character_gender": speaking_character["gender"],
            "visual_reference": speaking_character["visual_reference"],
            "scene_partner_character_id": partner_character["character_id"],
            "scene_partner_visual_reference": partner_character["visual_reference"],
            "voice_id": voice_profile["id"],
            "voice_profile": voice_profile,
            "text": text,
            "transliteration": line.get("transliteration", ""),
            "audio_path": audio_path,
            "status": status,
            "native_review_required": bool(
                dialogues_payload.get("native_review_status") == "needs_native_review"
            ),
        }
        assets.append(asset)

    return {
        "language": language,
        "display_name": dialogues_payload.get("display_name", language),
        "script": dialogues_payload.get("script", ""),
        "source": "data/languages/{language}/dialogues.json".format(language=language),
        "asset_type": "tts_audio",
        "status_values": ["needs_generation", "generated", "reviewed"],
        "assets": assets,
        "skipped_empty_text": skipped_empty_text,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to build. Repeatable.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]

    for language in languages:
        manifest = build_manifest(data_dir, project_dir, language)
        output_path = data_dir / "languages" / language / "audio_assets.json"
        write_json(output_path, manifest)
        generated = sum(1 for item in manifest["assets"] if item["status"] == "generated")
        print(f"{language}: wrote {len(manifest['assets'])} audio assets ({generated} generated)")


if __name__ == "__main__":
    main()
