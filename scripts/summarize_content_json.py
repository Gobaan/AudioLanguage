#!/usr/bin/env python3
"""Print a compact summary of model/content JSON files for agent navigation."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTENT_ROOT = PROJECT_ROOT / "model" / "content"
SKIPPED_DIRS = {"__pycache__", "ai_chunks"}


@dataclass(frozen=True)
class JsonFileSummary:
    path: str
    bytes: int
    shape: str


def summarize_model_content_json(
    content_root: Path = DEFAULT_CONTENT_ROOT,
    *,
    language: str | None = None,
    min_bytes: int = 0,
    largest: int | None = None,
) -> list[JsonFileSummary]:
    """Return compact summaries without printing large JSON payloads."""
    summaries: list[JsonFileSummary] = []
    for path in sorted(content_root.rglob("*.json")):
        if any(part in SKIPPED_DIRS for part in path.relative_to(content_root).parts):
            continue
        if language and not is_language_file(path, content_root, language):
            continue
        if path.stat().st_size < min_bytes:
            continue
        summaries.append(summarize_json_file(path, content_root))
    if largest is not None:
        summaries = sorted(summaries, key=lambda summary: summary.bytes, reverse=True)[:largest]
        summaries = sorted(summaries, key=lambda summary: summary.path)
    return summaries


def is_language_file(path: Path, content_root: Path, language: str) -> bool:
    language_root = content_root / "languages" / language
    return path.is_relative_to(language_root)


def summarize_json_file(path: Path, content_root: Path) -> JsonFileSummary:
    payload = json.loads(path.read_text(encoding="utf-8"))
    relative_path = path.relative_to(content_root).as_posix()
    return JsonFileSummary(
        path=relative_path,
        bytes=path.stat().st_size,
        shape=describe_json_shape(payload),
    )


def describe_json_shape(payload: Any) -> str:
    if isinstance(payload, list):
        return f"list[{len(payload)}]"
    if not isinstance(payload, dict):
        return type(payload).__name__

    parts: list[str] = []
    for key, value in payload.items():
        if isinstance(value, list):
            parts.append(f"{key}[{len(value)}]")
        elif isinstance(value, dict):
            parts.append(f"{key}{{{len(value)}}}")
        else:
            parts.append(f"{key}:{type(value).__name__}")
    return ", ".join(parts)


def render_table(summaries: list[JsonFileSummary]) -> str:
    if not summaries:
        return "No JSON files found."

    path_width = max(len("path"), *(len(summary.path) for summary in summaries))
    bytes_width = max(len("bytes"), *(len(str(summary.bytes)) for summary in summaries))
    lines = [f"{'path'.ljust(path_width)}  {'bytes'.rjust(bytes_width)}  shape"]
    lines.append(f"{'-' * path_width}  {'-' * bytes_width}  -----")
    for summary in summaries:
        lines.append(f"{summary.path.ljust(path_width)}  {str(summary.bytes).rjust(bytes_width)}  {summary.shape}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize model/content JSON files without dumping large payloads."
    )
    parser.add_argument(
        "--content-root",
        type=Path,
        default=DEFAULT_CONTENT_ROOT,
        help="Content root to scan. Defaults to model/content.",
    )
    parser.add_argument(
        "--language",
        help="Limit output to one model/content/languages/{language} folder.",
    )
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=0,
        help="Only show JSON files at least this many bytes.",
    )
    parser.add_argument(
        "--largest",
        type=int,
        help="Only show the N largest matching JSON files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        render_table(
            summarize_model_content_json(
                args.content_root,
                language=args.language,
                min_bytes=args.min_bytes,
                largest=args.largest,
            )
        )
    )


if __name__ == "__main__":
    main()
