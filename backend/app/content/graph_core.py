from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataGraphError(ValueError):
    """Raised when the structured content graph cannot be loaded."""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DataGraphError(f"Missing content file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def index_by_id(data: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    items = data.get(key, [])
    return {str(item["id"]): item for item in items}


def required(
    items: dict[str, dict[str, Any]],
    item_id: str | None,
    label: str,
) -> dict[str, Any]:
    if item_id is None or item_id not in items:
        raise DataGraphError(f"Missing {label}: {item_id}")
    return items[item_id]


def public_path(path: str | None) -> str | None:
    if not path:
        return None
    return "/" + path.replace("\\", "/").lstrip("/")
