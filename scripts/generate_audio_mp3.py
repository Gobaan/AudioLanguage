from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path

def add_repo_root_to_syspath() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))


add_repo_root_to_syspath()

from audiolanguage.paths import repo_paths  # noqa: E402


@dataclass(frozen=True, slots=True)
class Voices:
    feminine: str
    masculine: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate MP3 TTS files for dialogues.json")
    p.add_argument("--force", action="store_true", help="Re-generate files even if they exist")
    p.add_argument(
        "--feminine-voice",
        default="en-US-JennyNeural",
        help="Edge TTS voice name for learner (feminine) lines",
    )
    p.add_argument(
        "--masculine-voice",
        default="en-US-GuyNeural",
        help="Edge TTS voice name for other (masculine) lines",
    )
    return p.parse_args()


def load_dialogues(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_lines(dialogues: dict):
    for category in dialogues.get("categories", []):
        for scene in category.get("scenes", []):
            scene_id = scene.get("id")
            lines = scene.get("lines", [])
            for index, line in enumerate(lines):
                yield scene_id, index, line


def speaker_voice(line: dict, voices: Voices) -> str:
    speaker = (line.get("speaker") or "").strip().lower()
    if speaker == "learner":
        return voices.feminine
    return voices.masculine


async def synthesize_mp3(*, text: str, voice: str, out_path: Path) -> None:
    import edge_tts  # imported here so error message is clearer if missing

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(out_path))


async def generate_all(*, voices: Voices, force: bool) -> int:
    paths = repo_paths()
    dialogues_file = paths.dialogues_json
    audio_dir = paths.audio_dir

    if not dialogues_file.exists():
        raise FileNotFoundError(f"Missing {dialogues_file}")

    audio_dir.mkdir(parents=True, exist_ok=True)
    dialogues = load_dialogues(dialogues_file)

    created = 0
    skipped = 0
    total = 0

    for scene_id, index, line in iter_lines(dialogues):
        if not scene_id:
            continue
        total += 1

        out_path = paths.mp3_path(scene_id=scene_id, line_index=index)
        if out_path.exists() and not force:
            skipped += 1
            continue

        text = (line.get("text") or "").strip()
        if not text:
            skipped += 1
            continue

        voice = speaker_voice(line, voices)
        await synthesize_mp3(text=text, voice=voice, out_path=out_path)
        created += 1
        print(f"[{created + skipped}/{total}] {out_path.name} ({voice}): {text}")

    print()
    print(f"Done. Created: {created}  Skipped: {skipped}")
    return 0


def main() -> int:
    args = parse_args()
    voices = Voices(feminine=args.feminine_voice, masculine=args.masculine_voice)
    return asyncio.run(generate_all(voices=voices, force=args.force))


if __name__ == "__main__":
    raise SystemExit(main())

