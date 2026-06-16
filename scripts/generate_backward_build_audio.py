"""Generate learner-voice MP3s for backward-build lesson prompts."""

from __future__ import annotations

import argparse
import asyncio
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
from content_assets import DEFAULT_DATA_DIR, iter_dialogue_lines, list_language_dirs, path_exists, read_json  # noqa: E402
from project_config.paths import repo_file_for_relative_path  # noqa: E402
from voice_registry import voice_profile_for  # noqa: E402


async def synthesize_mp3(
    *,
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_path: Path,
) -> None:
    import edge_tts

    out_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_path))


def tts_text_for_line(line: dict | None) -> str:
    if not line:
        return ""
    for key in ("tts_text", "text", "transliteration", "audio_text"):
        value = line.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def spoken_phrase_for_target(target: dict, learner_line: dict | None = None) -> str:
    explicit_prompts = target.get("backward_build_spoken_prompts")
    if isinstance(explicit_prompts, list) and explicit_prompts:
        return str(explicit_prompts[-1]).strip()
    learner_tts_text = tts_text_for_line(learner_line)
    if learner_tts_text:
        return learner_tts_text
    canonical = target.get("canonical")
    if isinstance(canonical, str) and canonical.strip():
        return canonical.strip()
    transliteration = target.get("transliteration")
    if isinstance(transliteration, str) and transliteration.strip():
        return transliteration.strip()
    return ""


MVP_BACKWARD_BUILD_TARGET_IDS = {
    "en-target-respond-hi",
    "en-target-my-name-is",
    "en-target-i-dont-understand",
    "en-target-excuse-me-attention",
    "en-target-one-local-food-please",
    "ta-target-respond-hi",
    "ta-target-my-name-is",
    "ta-target-i-dont-understand",
    "ta-target-excuse-me-attention",
    "ta-target-one-local-food-please",
    "zh-target-respond-hi",
    "zh-target-my-name-is",
    "zh-target-i-dont-understand",
    "zh-target-excuse-me-attention",
    "zh-target-one-local-food-please",
    "yue-target-respond-hi",
    "yue-target-my-name-is",
    "yue-target-i-dont-understand",
    "yue-target-excuse-me-attention",
    "yue-target-one-local-food-please",
    "ja-target-respond-hi",
    "ja-target-my-name-is",
    "ja-target-i-dont-understand",
    "ja-target-excuse-me-attention",
    "ja-target-one-local-food-please",
}


def language_codes(data_dir: Path, requested: list[str] | None) -> list[str]:
    if requested:
        return requested
    return [path.name for path in list_language_dirs(data_dir)]


def learner_lines_by_target(dialogues_payload: dict) -> dict[str, dict]:
    learner_lines: dict[str, dict] = {}
    for dialogue, line in iter_dialogue_lines(dialogues_payload):
        if line.get("line_type") != "learner_target":
            continue
        target_id = line.get("target_id") or dialogue.get("target_id")
        if isinstance(target_id, str) and target_id and target_id not in learner_lines:
            learner_lines[target_id] = line
    return learner_lines


async def generate_language(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    force: bool,
    mvp_only: bool,
) -> tuple[int, int]:
    targets_payload = read_json(data_dir / "languages" / language / "targets.json")
    dialogues_payload = read_json(data_dir / "languages" / language / "dialogues.json")
    learner_lines = learner_lines_by_target(dialogues_payload)
    profile = voice_profile_for(language, "learner")
    created = 0
    skipped = 0

    for target in targets_payload.get("targets", []):
        if mvp_only and target["id"] not in MVP_BACKWARD_BUILD_TARGET_IDS:
            continue

        target_phrase = target.get("transliteration") or target.get("canonical") or ""
        units = backward_build_units(target=target, target_phrase=target_phrase)
        if not units:
            continue

        spoken_phrase = spoken_phrase_for_target(target, learner_lines.get(target["id"]))
        for build_index in backward_build_indices(len(units)):
            spoken_text = backward_build_entry_spoken_text(
                target=target,
                build_index=build_index,
                units=units,
                spoken_phrase=spoken_phrase,
            )
            if not spoken_text.strip():
                continue

            audio_path = backward_build_audio_relative_path(language, target["id"], build_index)
            if path_exists(project_dir, audio_path) and not force:
                skipped += 1
                continue

            try:
                await synthesize_mp3(
                    text=spoken_text,
                    voice=profile["provider_voice"],
                    rate=profile.get("rate", "+0%"),
                    pitch=profile.get("pitch", "+0Hz"),
                    out_path=repo_file_for_relative_path(project_dir, audio_path),
                )
            except Exception as error:
                print(
                    f"{language}: failed {audio_path} "
                    f"({target['id']} build {build_index}): {error}"
                )
                continue

            created += 1
            print(f"{language}: {audio_path}")

    return created, skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to generate. Repeatable.")
    parser.add_argument("--force", action="store_true", help="Regenerate even when the MP3 already exists.")
    parser.add_argument(
        "--mvp-only",
        action="store_true",
        help="Only generate audio for MVP anchor backward-build targets.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    data_dir = args.data_dir if args.data_dir.is_absolute() else PROJECT_DIR / args.data_dir
    project_dir = args.project_dir if args.project_dir.is_absolute() else PROJECT_DIR / args.project_dir
    languages = language_codes(data_dir, args.language)

    total_created = 0
    total_skipped = 0
    for language in languages:
        created, skipped = await generate_language(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
            force=args.force,
            mvp_only=args.mvp_only,
        )
        total_created += created
        total_skipped += skipped
        print(f"{language}: created {created}, skipped {skipped}")

    print(f"Done. created {total_created}, skipped {total_skipped}")


if __name__ == "__main__":
    asyncio.run(main())
