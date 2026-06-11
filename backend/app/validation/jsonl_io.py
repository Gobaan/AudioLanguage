from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import re
from typing import Any

logger = logging.getLogger(__name__)

SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


def safe_id(value: str) -> str:
    if not value or not SAFE_ID.match(value):
        raise ValueError(f"Unsafe id: {value!r}")
    return value


def safe_suffix(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in {".webm", ".wav", ".mp3", ".m4a", ".ogg"}:
        return suffix
    if content_type == "audio/wav":
        return ".wav"
    if content_type == "audio/ogg":
        return ".ogg"
    return ".webm"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False))
        file.write("\n")


def write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    if not items:
        path.unlink(missing_ok=True)
        return

    with path.open("w", encoding="utf-8") as file:
        for item in items:
            file.write(json.dumps(item, ensure_ascii=False))
            file.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    items = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping malformed JSONL line %s in %s", line_number, path)
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def relative_to_root(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def delete_file(path: Path) -> bool:
    if not path.exists():
        return False
    path.unlink()
    return True
