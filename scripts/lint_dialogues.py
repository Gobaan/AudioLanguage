"""Lint dialogue content files for structural and beginner-quality issues."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from content_assets import DEFAULT_DATA_DIR, list_language_dirs, read_json

LATIN_SCRIPTS = {"english", "latin"}
OPENING_LINE_MAX_WORDS = 6
RESPONSE_LINE_MAX_WORDS = 5
FORBIDDEN_OPENER_TERMS = (
    "fill",
    "form",
    "press",
    "nirapp",
    "azhuth",
    "tian",
    "an zheli",
    "tin",
    "aam",
)
FORBIDDEN_RESPONSE_TERMS = (
    "help",
    "udhav",
    "bang",
    "bong",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, type=Path)
    parser.add_argument("--language", action="append", help="Language code to lint. Repeatable.")
    parser.add_argument(
        "--strict-beginner-shape",
        action="store_true",
        help="Require one world_opener, one learner_target, one world_response per dialogue.",
    )
    return parser.parse_args()


def normalize_word_count(text: str) -> int:
    cleaned = re.sub(r"[.,!?،؛。！？]", " ", text)
    return len([part for part in cleaned.split() if part.strip()])


def learner_facing_line_text(line: dict[str, Any]) -> str:
    return str(
        line.get("transliteration")
        or line.get("audio_text")
        or line.get("display_text")
        or line.get("text")
        or ""
    ).strip()


def has_non_latin_script(script_name: str) -> bool:
    return script_name.strip().lower() not in LATIN_SCRIPTS


def lint_dialogue(
    *,
    language: str,
    dialogue: dict[str, Any],
    strict_beginner_shape: bool,
    require_transliteration: bool,
) -> list[str]:
    errors: list[str] = []
    dialogue_id = str(dialogue.get("id", "<missing-id>"))
    lines = dialogue.get("lines")
    if not isinstance(lines, list) or not lines:
        return [f"{language}:{dialogue_id}: missing non-empty lines array"]

    indices: list[int] = []
    openers: list[dict[str, Any]] = []
    learner_targets: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []

    for line in lines:
        line_index = line.get("index")
        if not isinstance(line_index, int):
            errors.append(f"{language}:{dialogue_id}: line has non-integer index: {line_index!r}")
            continue
        indices.append(line_index)
        line_type = str(line.get("line_type", ""))
        text = str(line.get("text", "")).strip()
        if not text:
            errors.append(f"{language}:{dialogue_id}: line {line_index} missing text")
        if "???" in text:
            errors.append(f"{language}:{dialogue_id}: line {line_index} contains placeholder text")

        if require_transliteration:
            transliteration = str(line.get("transliteration", "")).strip()
            if not transliteration:
                errors.append(f"{language}:{dialogue_id}: line {line_index} missing transliteration")

        if line_type == "world_opener":
            openers.append(line)
        elif line_type == "learner_target":
            learner_targets.append(line)
            line_target = line.get("target_id")
            dialogue_target = dialogue.get("target_id")
            if line_target and dialogue_target and str(line_target) != str(dialogue_target):
                errors.append(
                    f"{language}:{dialogue_id}: line {line_index} learner target_id "
                    f"{line_target!r} does not match dialogue target_id {dialogue_target!r}"
                )
        elif line_type == "world_response":
            responses.append(line)

    if indices:
        ordered = sorted(indices)
        expected = list(range(len(ordered)))
        if ordered != expected:
            errors.append(
                f"{language}:{dialogue_id}: line indexes must be contiguous starting at 0, got {ordered}"
            )

    if strict_beginner_shape:
        if len(openers) != 1:
            errors.append(f"{language}:{dialogue_id}: expected 1 world_opener, found {len(openers)}")
        if len(learner_targets) != 1:
            errors.append(f"{language}:{dialogue_id}: expected 1 learner_target, found {len(learner_targets)}")
        if len(responses) != 1:
            errors.append(f"{language}:{dialogue_id}: expected 1 world_response, found {len(responses)}")

    if len(openers) == 1:
        opener_text = learner_facing_line_text(openers[0])
        if normalize_word_count(opener_text) > OPENING_LINE_MAX_WORDS:
            errors.append(
                f"{language}:{dialogue_id}: opener exceeds {OPENING_LINE_MAX_WORDS} words: {opener_text!r}"
            )
        lower = opener_text.lower()
        if any(term in lower for term in FORBIDDEN_OPENER_TERMS):
            errors.append(f"{language}:{dialogue_id}: opener includes forbidden directive term: {opener_text!r}")

    if len(responses) == 1:
        response_text = learner_facing_line_text(responses[0])
        if normalize_word_count(response_text) > RESPONSE_LINE_MAX_WORDS:
            errors.append(
                f"{language}:{dialogue_id}: world response exceeds {RESPONSE_LINE_MAX_WORDS} words: {response_text!r}"
            )
        lower = response_text.lower()
        if any(term in lower for term in FORBIDDEN_RESPONSE_TERMS):
            errors.append(f"{language}:{dialogue_id}: response includes forbidden help term: {response_text!r}")

    return errors


def lint_language(data_dir: Path, language: str, strict_beginner_shape: bool) -> list[str]:
    language_dir = data_dir / "languages" / language
    dialogues_path = language_dir / "dialogues.json"
    targets_path = language_dir / "targets.json"

    errors: list[str] = []
    if not dialogues_path.exists():
        return [f"{language}: missing dialogues.json"]
    if not targets_path.exists():
        return [f"{language}: missing targets.json"]

    dialogues_payload = read_json(dialogues_path)
    targets_payload = read_json(targets_path)
    script_name = str(targets_payload.get("script", ""))
    require_transliteration = has_non_latin_script(script_name)

    dialogues = dialogues_payload.get("dialogues", [])
    if not isinstance(dialogues, list):
        return [f"{language}: dialogues.json has non-list 'dialogues' field"]

    for dialogue in dialogues:
        if not isinstance(dialogue, dict):
            errors.append(f"{language}: dialogue entry is not an object")
            continue
        errors.extend(
            lint_dialogue(
                language=language,
                dialogue=dialogue,
                strict_beginner_shape=strict_beginner_shape,
                require_transliteration=require_transliteration,
            )
        )

    return errors


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]
    all_errors: list[str] = []
    for language in languages:
        errors = lint_language(
            data_dir=data_dir,
            language=language,
            strict_beginner_shape=args.strict_beginner_shape,
        )
        all_errors.extend(errors)
        if errors:
            print(f"{language}: {len(errors)} dialogue lint issue(s)")
        else:
            print(f"{language}: ok")

    if all_errors:
        for error in all_errors:
            print(error)
        raise SystemExit(1)

    print("Dialogue lint passed.")


if __name__ == "__main__":
    main()
