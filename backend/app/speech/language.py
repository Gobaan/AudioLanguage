"""Language-specific pronunciation display helpers."""

from __future__ import annotations

from app.speech.romanization import (
    contains_language_script,
    contains_unexpected_known_script,
    romanize_text,
)


def phonetic_for_language(value: str, language: str) -> str:
    return romanize_for_language(value, language)


def romanize_for_language(value: str, language: str) -> str:
    if contains_language_script(value, language):
        return romanize_text(value, language)
    return value


def contains_tamil(value: str) -> bool:
    return contains_language_script(value, "ta")


def contains_japanese(value: str) -> bool:
    return contains_language_script(value, "ja")


def tamil_to_latin(value: str) -> str:
    return romanize_text(value, "ta")


def japanese_to_romaji(value: str) -> str:
    return romanize_text(value, "ja")


def has_unexpected_script(value: str, language: str) -> bool:
    return contains_unexpected_known_script(value, language)
