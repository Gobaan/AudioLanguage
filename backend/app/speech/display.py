"""Learner-facing romanized text for speech feedback."""

from __future__ import annotations

import re

from app.speech.language import has_unexpected_script, romanize_for_language

HAN_PATTERN = re.compile(r"[\u3400-\u9FFF]")
ROMANIZED_TRANSCRIPT_LANGUAGES = {"ja", "ta", "zh", "yue"}


def contains_han(value: str) -> bool:
    return bool(HAN_PATTERN.search(value))


def latin_only(value: str) -> str:
    return " ".join(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", value)).strip()


def learner_romanized_only(value: str, *, language: str, target_romanized: str = "") -> str:
    latin = latin_only(value)
    if latin:
        return latin
    if contains_han(value) and target_romanized:
        return target_romanized
    return value


def learner_facing_transcript(
    transcript: str,
    *,
    language: str,
    target_romanized: str = "",
    language_label: str = "target language",
) -> str:
    if not transcript:
        return ""
    if has_unexpected_script(transcript, language):
        return f"unclear {language_label} attempt"

    romanized = romanize_for_language(transcript, language)
    if language in ROMANIZED_TRANSCRIPT_LANGUAGES:
        return learner_romanized_only(romanized, language=language, target_romanized=target_romanized)
    return romanized
