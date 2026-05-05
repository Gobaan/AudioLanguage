"""Export visual manifest prompts into tool-friendly text files."""

from __future__ import annotations

import argparse
from pathlib import Path

from content_assets import list_language_dirs, read_json


def export_language(data_dir: Path, project_dir: Path, language: str, prompt_kind: str) -> int:
    manifest_path = data_dir / "languages" / language / "visual_prompts.json"
    manifest = read_json(manifest_path)
    exported = 0

    for item in manifest.get("prompts", []):
        prompt = item["localized_prompt"] if prompt_kind == "localized" else item["shared_prompt"]

        image_prompt_path = project_dir / item["image_prompt_path"]
        video_prompt_path = project_dir / item["video_prompt_path"]
        image_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        video_prompt_path.parent.mkdir(parents=True, exist_ok=True)

        image_prompt_path.write_text(prompt + "\n", encoding="utf-8")
        video_prompt_path.write_text(
            "\n".join(
                [
                    prompt,
                    "",
                    "Video direction:",
                    "Animate this as a short 2-4 second visual beat. Keep the camera stable,",
                    "make gestures readable, preserve character continuity, and do not add subtitles.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        exported += 2

    return exported


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to export. Repeatable.")
    parser.add_argument("--prompt-kind", choices=["localized", "shared"], default="localized")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]

    total = 0
    for language in languages:
        count = export_language(data_dir, project_dir, language, args.prompt_kind)
        total += count
        print(f"{language}: exported {count} prompt files")
    print(f"Done. Exported {total} prompt files.")


if __name__ == "__main__":
    main()
