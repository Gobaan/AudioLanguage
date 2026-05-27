"""Generate MP3 files from a language audio asset manifest using Edge TTS."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from content_assets import list_language_dirs, path_exists, read_json
from project_config.paths import repo_file_for_relative_path
from voice_registry import voice_profile_for


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


async def generate_language(
    data_dir: Path,
    project_dir: Path,
    language: str,
    force: bool,
    limit: int | None,
    dialogue_ids: set[str] | None,
) -> tuple[int, int]:
    manifest = read_json(data_dir / "languages" / language / "audio_assets.json")
    created = 0
    skipped = 0
    for item in manifest.get("assets", []):
        if dialogue_ids and item.get("dialogue_id") not in dialogue_ids:
            continue
        if limit is not None and created >= limit:
            break

        profile = item.get("voice_profile") or voice_profile_for(language, item.get("speaker_role", ""))
        audio_path = item["audio_path"]
        if path_exists(project_dir, audio_path) and not force:
            skipped += 1
        else:
            await synthesize_mp3(
                text=item["text"],
                voice=profile["provider_voice"],
                rate=profile.get("rate", "+0%"),
                pitch=profile.get("pitch", "+0Hz"),
                out_path=repo_file_for_relative_path(project_dir, audio_path),
            )
            created += 1
            print(
                f"{language}: {audio_path} "
                f"({profile['id']}: {profile['provider_voice']}, "
                f"rate {profile.get('rate', '+0%')}, pitch {profile.get('pitch', '+0Hz')})"
            )

    return created, skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="model/content", type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to generate. Repeatable.")
    parser.add_argument("--dialogue-id", action="append", help="Only generate audio for this dialogue id. Repeatable.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, help="Maximum files to create per language.")
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]

    for language in languages:
        created, skipped = await generate_language(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
            force=args.force,
            limit=args.limit,
            dialogue_ids=set(args.dialogue_id) if args.dialogue_id else None,
        )
        print(f"{language}: created {created}, skipped {skipped}")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
