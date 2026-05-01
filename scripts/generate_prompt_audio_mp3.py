from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


def add_repo_root_to_syspath() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))


add_repo_root_to_syspath()

from audiolanguage.paths import repo_paths  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate MP3 TTS files for prompts.json")
    p.add_argument("--force", action="store_true", help="Re-generate files even if they exist")
    p.add_argument(
        "--voice",
        default="en-US-JennyNeural",
        help="Edge TTS voice name for prompt audio",
    )
    return p.parse_args()


def load_prompts(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("prompts.json must be a JSON object of string values")
    out: dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        out[k] = v
    return out


async def synthesize_mp3(*, text: str, voice: str, out_path: Path) -> None:
    import edge_tts  # imported here so error message is clearer if missing

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(out_path))


async def generate_all(*, voice: str, force: bool) -> int:
    paths = repo_paths()
    prompts_file = paths.prompts_json
    if not prompts_file.exists():
        raise FileNotFoundError(f"Missing {prompts_file}")

    prompts = load_prompts(prompts_file)
    paths.prompts_audio_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    total = 0

    for key in sorted(prompts.keys()):
        total += 1
        text = prompts[key].strip()
        out_path = paths.prompt_mp3_path(key=key)

        if not text:
            skipped += 1
            continue

        if out_path.exists() and not force:
            skipped += 1
            continue

        await synthesize_mp3(text=text, voice=voice, out_path=out_path)
        created += 1
        print(f"[{created + skipped}/{total}] {out_path.as_posix()} ({voice}): {text}")

    print()
    print(f"Done. Created: {created}  Skipped: {skipped}")
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(generate_all(voice=args.voice, force=args.force))


if __name__ == "__main__":
    raise SystemExit(main())

