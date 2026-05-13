"""Data-driven romanization utilities for learner feedback."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any


DATA_PATH = Path(__file__).with_name("romanization_data.json")
SCRIPT_PATTERNS = {
    "arabic": r"[\u0600-\u06FF]",
    "cyrillic": r"[\u0400-\u04FF]",
    "greek": r"[\u0370-\u03FF]",
    "hebrew": r"[\u0590-\u05FF]",
    "japanese": r"[\u3040-\u30FF\u3400-\u9FFF]",
    "tamil": r"[\u0B80-\u0BFF]",
}

LANGUAGE_SCRIPT_NAMES = {
    "ja": {"japanese"},
    "ta": {"tamil"},
}


def contains_language_script(value: str, language: str) -> bool:
    config = _language_config(language)
    pattern = config.get("char_pattern")
    return bool(pattern and re.search(str(pattern), value))


def romanize_text(value: str, language: str) -> str:
    config = _language_config(language)
    romanizer_type = config.get("type")
    if romanizer_type == "abugida":
        return _romanize_abugida(value, config)
    if romanizer_type == "kana":
        return _romanize_kana_text(value, config)
    return value


def contains_unexpected_known_script(value: str, language: str) -> bool:
    expected_scripts = LANGUAGE_SCRIPT_NAMES.get(language, set())
    if not expected_scripts:
        return False

    for script_name, pattern in SCRIPT_PATTERNS.items():
        if script_name not in expected_scripts and re.search(pattern, value):
            return True
    return False


def _romanize_abugida(value: str, config: dict[str, Any]) -> str:
    independent_vowels = config["independent_vowels"]
    consonants = config["consonants"]
    vowel_signs = config["vowel_signs"]
    virama = config["virama"]
    inherent_vowel = config.get("inherent_vowel", "a")

    output: list[str] = []
    index = 0

    while index < len(value):
        char = value[index]

        if char in independent_vowels:
            output.append(independent_vowels[char])
            index += 1
            continue

        if char in consonants:
            base = consonants[char]
            next_char = value[index + 1] if index + 1 < len(value) else ""
            if next_char == virama:
                output.append(base)
                index += 2
            elif next_char in vowel_signs:
                output.append(base + vowel_signs[next_char])
                index += 2
            else:
                output.append(base + inherent_vowel)
                index += 1
            continue

        if char in vowel_signs or char == virama:
            index += 1
            continue

        output.append(char)
        index += 1

    return " ".join("".join(output).split())


def _romanize_kana_text(value: str, config: dict[str, Any]) -> str:
    reading = _apply_reading_overrides(value, config.get("reading_overrides", {}))
    kana = _katakana_to_hiragana(reading, config)
    return _compact_romanized_text(_kana_to_romaji(kana, config), config)


def _apply_reading_overrides(value: str, overrides: dict[str, str]) -> str:
    output = value
    for phrase, reading in sorted(overrides.items(), key=lambda item: len(item[0]), reverse=True):
        output = output.replace(phrase, reading)
    return output


def _katakana_to_hiragana(value: str, config: dict[str, Any]) -> str:
    start, end = config.get("katakana_range", [0, -1])
    offset = int(config.get("katakana_to_hiragana_offset", 0))
    output: list[str] = []

    for char in value:
        codepoint = ord(char)
        if start <= codepoint <= end:
            output.append(chr(codepoint - offset))
        else:
            output.append(char)
    return "".join(output)


def _kana_to_romaji(value: str, config: dict[str, Any]) -> str:
    digraphs = config["kana_digraphs"]
    kana_romaji = config["kana_romaji"]
    small_tsu = set(config.get("small_tsu", []))
    long_vowel_mark = config.get("long_vowel_mark", "")

    output: list[str] = []
    index = 0
    geminate_next = False

    while index < len(value):
        char = value[index]

        if char in small_tsu:
            geminate_next = True
            index += 1
            continue

        if char == long_vowel_mark:
            output.append(_long_vowel_for(output))
            index += 1
            continue

        pair = value[index : index + 2]
        if pair in digraphs:
            output.append(_apply_gemination(digraphs[pair], geminate_next))
            geminate_next = False
            index += 2
            continue

        romaji = kana_romaji.get(char)
        if romaji:
            output.append(_apply_gemination(romaji, geminate_next))
        else:
            output.append(char)
        geminate_next = False
        index += 1

    return "".join(output)


def _apply_gemination(romaji: str, should_geminate: bool) -> str:
    if not should_geminate or not romaji:
        return romaji
    if romaji.startswith("ch"):
        return "c" + romaji
    return romaji[0] + romaji


def _long_vowel_for(output: list[str]) -> str:
    previous = "".join(output)
    for vowel in ("a", "i", "u", "e", "o"):
        if previous.endswith(vowel):
            return vowel
    return ""


def _compact_romanized_text(value: str, config: dict[str, Any]) -> str:
    punctuation = "".join(re.escape(mark) for mark in config.get("punctuation", []))
    if punctuation:
        value = re.sub(rf"([A-Za-z])([{punctuation}])", r"\1\2 ", value)
        value = re.sub(rf"([{punctuation}])([A-Za-z])", r"\1 \2", value)

    spaced = re.sub(r"\s+", " ", value).strip()
    for source, replacement in config.get("punctuation_replacements", {}).items():
        spaced = spaced.replace(source, replacement)
    return spaced


def _language_config(language: str) -> dict[str, Any]:
    return dict(_romanization_data().get(language, {}))


@lru_cache(maxsize=1)
def _romanization_data() -> dict[str, Any]:
    with DATA_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Romanization data must be a JSON object: {DATA_PATH}")
    return data
