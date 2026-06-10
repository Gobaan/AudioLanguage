from __future__ import annotations

import sys
from pathlib import Path

def add_repo_root_to_syspath() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))


add_repo_root_to_syspath()

from content_assets import read_json  # noqa: E402
from project_config.paths import repo_paths  # noqa: E402


def expected_mp3_names(dialogues: dict) -> list[str]:
    names: list[str] = []
    for category in dialogues.get("categories", []):
        for scene in category.get("scenes", []):
            scene_id = scene.get("id")
            if not scene_id:
                continue
            for i in range(len(scene.get("lines", []))):
                names.append(f"{scene_id}-{i}.mp3")
    return names


def missing_files(names: list[str], folder: Path) -> list[str]:
    return [name for name in names if not (folder / name).exists()]


def print_summary(*, dialogues_file: Path, audio_folder: Path, expected: int, missing: int) -> None:
    print(f"Dialogues file: {dialogues_file}")
    print(f"Audio dir     : {audio_folder}")
    print(f"Expected MP3s : {expected}")
    print(f"Missing MP3s  : {missing}")


def print_missing(names: list[str], *, limit: int = 50) -> None:
    print(f"\nFirst {min(limit, len(names))} missing:")
    for name in names[:limit]:
        print(f"- {name}")
    if len(names) > limit:
        print(f"... and {len(names) - limit} more")


def main() -> int:
    dpath = repo_paths().dialogues_json
    if not dpath.exists():
        print(f"ERROR: Missing {dpath}")
        return 2

    adir = repo_paths().audio_dir
    adir.mkdir(parents=True, exist_ok=True)

    dialogues = read_json(dpath)
    expected = expected_mp3_names(dialogues)
    missing = missing_files(expected, adir)

    print_summary(
        dialogues_file=dpath,
        audio_folder=adir,
        expected=len(expected),
        missing=len(missing),
    )

    if missing:
        print_missing(missing, limit=50)
        return 1

    print("\nAll expected audio files are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
