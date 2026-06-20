from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from app.validation.jsonl_io import append_jsonl, now_iso, read_jsonl

MAX_RECOMMENDED_PHRASE_LENGTH = 250


class RecommendedPhraseStore:
    def __init__(self, storage_dir: Path):
        self.path = storage_dir / "recommended_phrases.jsonl"

    def add(self, phrase: str, *, client_ip: str, location_flag: str) -> dict[str, Any]:
        normalized_phrase = normalize_recommended_phrase(phrase)
        item = {
            "id": str(uuid.uuid4()),
            "phrase": normalized_phrase,
            "recommendedAt": now_iso(),
            "clientIp": client_ip or None,
            "locationFlag": location_flag,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        append_jsonl(self.path, item)
        return item

    def list(self) -> list[dict[str, Any]]:
        return read_jsonl(self.path)

    def summary(self, index: int = 0) -> dict[str, Any]:
        phrases = self.list()
        count = len(phrases)
        if count == 0:
            return {"count": 0, "index": 0, "phrase": None}

        safe_index = min(max(index, 0), count - 1)
        return {
            "count": count,
            "index": safe_index,
            "phrase": phrases[safe_index],
        }


def normalize_recommended_phrase(value: str) -> str:
    phrase = " ".join(str(value or "").split())
    if not phrase:
        raise ValueError("Recommended phrase is required")
    if len(phrase) > MAX_RECOMMENDED_PHRASE_LENGTH:
        raise ValueError("Recommended phrase must be 250 characters or fewer")
    return phrase
