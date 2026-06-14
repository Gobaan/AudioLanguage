"""Equalize MVP sessions, dialogues, visual beats, and practice cards across languages."""

from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from content_assets import DEFAULT_DATA_DIR, read_json, write_json

LANGUAGES = ["en", "ja", "ta", "zh", "yue"]
REFERENCE_LANGUAGE = "ja"

MVP_DIALOGUE_SUFFIXES = [
    "first-hi-response",
    "introduce-self",
    "repair-dont-understand",
    "excuse-me-attention",
    "order-local-food",
    "greeting-neighbor-transfer",
    "introduce-class-transfer",
    "repair-ticket-transfer",
    "excuse-me-cafe-transfer",
    "order-convenience-transfer",
    "greeting-entry-review",
    "introduce-community-review",
    "repair-clinic-review",
    "excuse-me-station-review",
    "order-bakery-review",
]

DISPLAY_NAMES = {
    "en": "English",
    "ja": "Japanese",
    "ta": "Tamil",
    "zh": "Mandarin",
    "yue": "Cantonese",
}

# Fallback line sources when a language is missing a canonical MVP dialogue.
DIALOGUE_ALIASES: dict[str, dict[str, str]] = {
    "ta": {
        "first-hi-response": "ta-greeting-neighbor-transfer",
        "repair-dont-understand": "ta-repair-dont-understand",
    },
}

EN_FALLBACK_DIALOGUES: dict[str, dict[str, Any]] = {
    "excuse-me-attention": {
        "asset_slug": "excuse-me-attention",
        "type": "anchor",
        "function_id": "get_attention_politely",
        "target_id": "en-target-excuse-me-attention",
        "scene_id": "station-information-desk",
        "review_modes": ["listen", "produce_from_visual", "ai_guided_response"],
        "lines": [
            {
                "index": 0,
                "speaker_role": "staff",
                "line_type": "world_opener",
                "text": "Next, please.",
                "meaning_units": ["attention"],
            },
            {
                "index": 1,
                "speaker_role": "learner",
                "line_type": "learner_target",
                "target_id": "en-target-excuse-me-attention",
                "text": "Excuse me.",
                "meaning_units": ["attention_request", "polite_softener"],
            },
            {
                "index": 2,
                "speaker_role": "staff",
                "line_type": "world_response",
                "text": "Yes, go ahead.",
                "meaning_units": ["acknowledgement"],
            },
        ],
    },
    "excuse-me-cafe-transfer": {
        "asset_slug": "excuse-me-cafe-transfer",
        "type": "transfer",
        "function_id": "get_attention_politely",
        "target_id": "en-target-excuse-me-attention",
        "scene_id": "cafe-counter-attention",
        "review_modes": ["produce_from_visual", "ai_guided_response"],
        "lines": [
            {
                "index": 0,
                "speaker_role": "barista",
                "line_type": "world_opener",
                "text": "One moment, please.",
                "meaning_units": ["wait"],
            },
            {
                "index": 1,
                "speaker_role": "learner",
                "line_type": "learner_target",
                "target_id": "en-target-excuse-me-attention",
                "text": "Excuse me.",
                "meaning_units": ["attention_request", "polite_softener"],
            },
            {
                "index": 2,
                "speaker_role": "barista",
                "line_type": "world_response",
                "text": "Yes, how can I help?",
                "meaning_units": ["acknowledgement"],
            },
        ],
    },
}

TA_FALLBACK_DIALOGUES: dict[str, dict[str, Any]] = {
    "excuse-me-attention": {
        "lines": [
            {
                "index": 0,
                "speaker_role": "staff",
                "line_type": "world_opener",
                "text": "அடுத்தவர், தயவுசெய்து.",
                "transliteration": "Aduththavar, thayavu seythu.",
                "meaning_units": ["attention"],
            },
            {
                "index": 1,
                "speaker_role": "learner",
                "line_type": "learner_target",
                "target_id": "ta-target-excuse-me-attention",
                "text": "மன்னிக்கவும்.",
                "transliteration": "Mannikkavum.",
                "meaning_units": ["attention_request", "polite_softener"],
            },
            {
                "index": 2,
                "speaker_role": "staff",
                "line_type": "world_response",
                "text": "ஆமாம், சொல்லுங்கள்.",
                "transliteration": "Aamam, sollungal.",
                "meaning_units": ["acknowledgement"],
            },
        ],
    },
    "excuse-me-cafe-transfer": {
        "lines": [
            {
                "index": 0,
                "speaker_role": "barista",
                "line_type": "world_opener",
                "text": "சிறிது நேரம் காத்திருங்கள்.",
                "transliteration": "Sirithu neram kaathirungal.",
                "meaning_units": ["wait"],
            },
            {
                "index": 1,
                "speaker_role": "learner",
                "line_type": "learner_target",
                "target_id": "ta-target-excuse-me-attention",
                "text": "மன்னிக்கவும்.",
                "transliteration": "Mannikkavum.",
                "meaning_units": ["attention_request", "polite_softener"],
            },
            {
                "index": 2,
                "speaker_role": "barista",
                "line_type": "world_response",
                "text": "ஆமாம், என்ன வேண்டும்?",
                "transliteration": "Aamam, enna vendum?",
                "meaning_units": ["acknowledgement"],
            },
        ],
    },
    "order-convenience-transfer": {
        "lines": [
            {
                "index": 0,
                "speaker_role": "cashier",
                "line_type": "world_opener",
                "text": "என்ன வேண்டும்?",
                "transliteration": "Enna vendum?",
                "meaning_units": ["question"],
            },
            {
                "index": 1,
                "speaker_role": "learner",
                "line_type": "learner_target",
                "target_id": "ta-target-one-local-food-please",
                "text": "ஒரு சாண்ட்விச், தயவுசெய்து.",
                "transliteration": "Oru sandwich, thayavu seythu.",
                "meaning_units": ["food_item", "please"],
            },
            {
                "index": 2,
                "speaker_role": "cashier",
                "line_type": "world_response",
                "text": "சரி.",
                "transliteration": "Sari.",
                "meaning_units": ["acknowledgement"],
            },
        ],
    },
}

TARGET_FALLBACKS: dict[str, dict[str, Any]] = {
    "en-target-excuse-me-attention": {
        "function_id": "get_attention_politely",
        "canonical": "Excuse me.",
        "display_meaning": "Excuse me.",
        "meaning_units": ["attention_request", "polite_softener"],
        "accepted_variants": ["Excuse me", "Pardon me."],
        "valid_but_off_target": ["Thank you."],
        "wrong_for_context_examples": ["Hi!", "One sandwich, please."],
        "semantic_slots": {
            "required": {"speech_act": "attention_request"},
            "optional": {"politeness": True},
        },
        "notes": {"register": "polite-basic"},
    },
    "ta-target-respond-hi": {
        "function_id": "respond_to_greeting",
        "canonical": "Vanakkam!",
        "transliteration": "Vanakkam!",
        "display_meaning": "Respond to hello.",
        "meaning_units": ["hello", "response"],
        "accepted_variants": ["Vanakkam.", "Vanakkam!"],
        "wrong_for_context_examples": ["Nandri.", "En peyar Anna."],
        "notes": {"register": "friendly-basic", "native_review_required": True},
    },
    "zh-target-respond-hi": {
        "function_id": "respond_to_greeting",
        "canonical": "Ni hao!",
        "transliteration": "Ni hao!",
        "display_meaning": "Respond to hello.",
        "meaning_units": ["hello", "response"],
        "accepted_variants": ["Ni hao.", "Hai.", "Hello."],
        "wrong_for_context_examples": ["Zai jian.", "Xiexie."],
        "notes": {"register": "friendly-basic", "native_review_required": True},
    },
    "yue-target-respond-hi": {
        "function_id": "respond_to_greeting",
        "canonical": "Nei hou!",
        "transliteration": "Nei hou!",
        "display_meaning": "Respond to hello.",
        "meaning_units": ["hello", "response"],
        "accepted_variants": ["Nei hou.", "Halo."],
        "wrong_for_context_examples": ["Zoi gin.", "M goi."],
        "notes": {"register": "friendly-basic", "native_review_required": True},
    },
    "ta-target-excuse-me-attention": {
        "function_id": "get_attention_politely",
        "canonical": "Mannikkavum.",
        "transliteration": "Mannikkavum.",
        "display_meaning": "Excuse me.",
        "meaning_units": ["attention_request", "polite_softener"],
        "accepted_variants": ["Mannikkavum", "Mannippu."],
        "wrong_for_context_examples": ["Vanakkam!", "Nandri."],
        "notes": {"register": "polite-basic", "native_review_required": True},
    },
}


def replace_prefix(value: str, source_lang: str, target_lang: str) -> str:
    if value.startswith(f"{source_lang}-"):
        return f"{target_lang}-{value[len(source_lang) + 1:]}"
    return value


def localize_object(value: Any, source_lang: str, target_lang: str) -> Any:
    if isinstance(value, str):
        localized = replace_prefix(value, source_lang, target_lang)
        if source_lang == "ja" and target_lang != "ja":
            localized = localized.replace("Japanese", DISPLAY_NAMES[target_lang])
        return localized
    if isinstance(value, list):
        return [localize_object(item, source_lang, target_lang) for item in value]
    if isinstance(value, dict):
        return {key: localize_object(item, source_lang, target_lang) for key, item in value.items()}
    return value


def dialogue_id(language: str, suffix: str) -> str:
    return f"{language}-{suffix}"


def index_dialogues(dialogues_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in dialogues_payload.get("dialogues", [])}


def ensure_target(targets_payload: dict[str, Any], language: str, target_id: str, fallback: dict[str, Any] | None) -> None:
    targets = targets_payload.setdefault("targets", [])
    if any(item.get("id") == target_id for item in targets):
        return
    if fallback is None:
        return
    targets.append({"id": target_id, **fallback})


REVIEW_ANCHOR_SUFFIX = {
    "greeting-entry-review": "first-hi-response",
    "introduce-community-review": "introduce-self",
    "repair-clinic-review": "repair-dont-understand",
    "excuse-me-station-review": "excuse-me-attention",
    "order-bakery-review": "order-local-food",
}


def dialogue_has_reference_language_text(dialogue: dict[str, Any], language: str) -> bool:
    if language == REFERENCE_LANGUAGE:
        return False
    for line in dialogue.get("lines", []):
        text = str(line.get("text", ""))
        if any("\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff" for char in text):
            return True
    return False


def build_dialogue(
    *,
    language: str,
    suffix: str,
    reference_dialogue: dict[str, Any],
    existing_dialogue: dict[str, Any] | None,
    alias_dialogue: dict[str, Any] | None,
    fallback_dialogue: dict[str, Any] | None,
    all_dialogues: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dialogue = copy.deepcopy(reference_dialogue)
    dialogue["id"] = dialogue_id(language, suffix)
    if existing_dialogue:
        for key in ("asset_slug", "type", "function_id", "target_id", "scene_id", "review_modes", "lines"):
            if key in existing_dialogue:
                dialogue[key] = copy.deepcopy(existing_dialogue[key])
    elif alias_dialogue:
        for key in ("asset_slug", "type", "function_id", "target_id", "scene_id", "review_modes"):
            dialogue[key] = copy.deepcopy(reference_dialogue[key])
        localized_target = replace_prefix(str(reference_dialogue.get("target_id", "")), REFERENCE_LANGUAGE, language)
        dialogue["target_id"] = localized_target
        dialogue["lines"] = copy.deepcopy(alias_dialogue["lines"])
        for line in dialogue["lines"]:
            if line.get("line_type") == "learner_target":
                line["target_id"] = localized_target
    elif fallback_dialogue:
        dialogue.update(copy.deepcopy(fallback_dialogue))
        dialogue["id"] = dialogue_id(language, suffix)
    dialogue["asset_slug"] = dialogue.get("asset_slug") or reference_dialogue.get("asset_slug")
    anchor_suffix = REVIEW_ANCHOR_SUFFIX.get(suffix)
    if anchor_suffix and not existing_dialogue and not alias_dialogue and not fallback_dialogue:
        anchor = all_dialogues.get(dialogue_id(language, anchor_suffix))
        if anchor:
            dialogue["lines"] = copy.deepcopy(anchor["lines"])
    dialogue = localize_object(dialogue, REFERENCE_LANGUAGE, language)
    return dialogue


def sync_visual_beats(language: str, reference_beats: list[dict[str, Any]], dialogues: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    for beat in reference_beats:
        ref_dialogue_id = str(beat.get("dialogue_id", ""))
        suffix = ref_dialogue_id.removeprefix(f"{REFERENCE_LANGUAGE}-")
        if suffix not in MVP_DIALOGUE_SUFFIXES:
            continue
        localized = copy.deepcopy(beat)
        localized["id"] = replace_prefix(str(beat["id"]), REFERENCE_LANGUAGE, language)
        localized["dialogue_id"] = dialogue_id(language, suffix)
        dialogue = dialogues[localized["dialogue_id"]]
        if dialogue.get("target_id"):
            localized["target_id"] = dialogue["target_id"]
        if dialogue.get("function_id"):
            localized["function_id"] = dialogue["function_id"]
        if dialogue.get("scene_id"):
            localized["scene_id"] = dialogue["scene_id"]
        line_index = int(localized.get("line_index", 0))
        line = dialogue["lines"][line_index]
        localized["line_text"] = line.get("text", "")
        beats.append(localized)
    return beats


def sync_practice_cards(language: str, reference_cards: list[dict[str, Any]], reference_session: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ref_cards_by_id = {card["id"]: card for card in reference_cards}
    mvp_card_ids = list(reference_session.get("cards", []))
    localized_cards = []
    for card_id in mvp_card_ids:
        card = copy.deepcopy(ref_cards_by_id[card_id])
        localized_cards.append(localize_object(card, REFERENCE_LANGUAGE, language))

    session = copy.deepcopy(reference_session)
    session["id"] = replace_prefix(str(session["id"]), REFERENCE_LANGUAGE, language)
    session["name"] = session["name"].replace("Japanese", DISPLAY_NAMES[language])
    session["goal"] = session["goal"].replace("Japanese", DISPLAY_NAMES[language])
    session["cards"] = [replace_prefix(card_id, REFERENCE_LANGUAGE, language) for card_id in mvp_card_ids]
    session["lesson_tabs"] = localize_object(session.get("lesson_tabs", []), REFERENCE_LANGUAGE, language)
    session["delayed_lesson_tabs"] = localize_object(session.get("delayed_lesson_tabs", []), REFERENCE_LANGUAGE, language)
    return session, localized_cards


def sync_visual_prompt_shared_prompts(data_dir: Path) -> None:
    reference = read_json(data_dir / "languages" / REFERENCE_LANGUAGE / "visual_prompts.json")
    ref_by_key = {
        (item["dialogue_id"].removeprefix(f"{REFERENCE_LANGUAGE}-"), int(item["line_index"])): item.get("shared_prompt", "")
        for item in reference.get("prompts", [])
    }
    for language in LANGUAGES:
        if language == REFERENCE_LANGUAGE:
            continue
        path = data_dir / "languages" / language / "visual_prompts.json"
        if not path.exists():
            continue
        payload = read_json(path)
        for item in payload.get("prompts", []):
            suffix = str(item["dialogue_id"]).removeprefix(f"{language}-")
            key = (suffix, int(item["line_index"]))
            shared_prompt = ref_by_key.get(key)
            if shared_prompt:
                item["shared_prompt"] = shared_prompt
        write_json(path, payload)


def equalize_language(data_dir: Path, language: str) -> None:
    if language == REFERENCE_LANGUAGE:
        return

    ref_lang_dir = data_dir / "languages" / REFERENCE_LANGUAGE
    lang_dir = data_dir / "languages" / language

    ref_dialogues_payload = read_json(ref_lang_dir / "dialogues.json")
    ref_dialogues = index_dialogues(ref_dialogues_payload)
    dialogues_payload = read_json(lang_dir / "dialogues.json")
    dialogues = index_dialogues(dialogues_payload)

    targets_payload = read_json(lang_dir / "targets.json")
    aliases = DIALOGUE_ALIASES.get(language, {})

    updated_dialogues: dict[str, dict[str, Any]] = {}
    for suffix in MVP_DIALOGUE_SUFFIXES:
        ref_id = dialogue_id(REFERENCE_LANGUAGE, suffix)
        target_id = dialogue_id(language, suffix)
        reference_dialogue = ref_dialogues[ref_id]
        existing = dialogues.get(target_id)
        if existing and dialogue_has_reference_language_text(existing, language):
            existing = None
        alias = dialogues.get(aliases.get(suffix, ""))
        fallback = EN_FALLBACK_DIALOGUES.get(suffix) if language == "en" else None
        ta_lines = TA_FALLBACK_DIALOGUES.get(suffix) if language == "ta" else None
        if ta_lines and not existing:
            fallback = copy.deepcopy(ta_lines)
            for line in fallback["lines"]:
                if line.get("target_id"):
                    line["target_id"] = str(line["target_id"]).replace("ta-", f"{language}-")
        elif fallback:
            fallback = copy.deepcopy(fallback)
        if fallback and "target_id" in fallback:
            fallback["target_id"] = fallback["target_id"].replace("en-", f"{language}-")
            for line in fallback.get("lines", []):
                if isinstance(line, dict) and line.get("target_id"):
                    line["target_id"] = line["target_id"].replace("en-", f"{language}-")
        dialogue = build_dialogue(
            language=language,
            suffix=suffix,
            reference_dialogue=reference_dialogue,
            existing_dialogue=existing,
            alias_dialogue=alias,
            fallback_dialogue=fallback,
            all_dialogues={**dialogues, **updated_dialogues},
        )
        updated_dialogues[target_id] = dialogue
        target_key = str(dialogue.get("target_id", ""))
        if target_key:
            fallback_key = target_key.replace(f"{language}-", "en-")
            ensure_target(
                targets_payload,
                language,
                target_key,
                TARGET_FALLBACKS.get(target_key) or TARGET_FALLBACKS.get(fallback_key),
            )

    remaining = [dialogue for dialogue_id_key, dialogue in dialogues.items() if dialogue_id_key not in updated_dialogues]
    dialogues_payload["dialogues"] = remaining + list(updated_dialogues.values())
    write_json(lang_dir / "dialogues.json", dialogues_payload)

    ref_visual_beats = read_json(ref_lang_dir / "visual_beats.json").get("visual_beats", [])
    visual_payload = read_json(lang_dir / "visual_beats.json")
    visual_payload["visual_beats"] = sync_visual_beats(language, ref_visual_beats, updated_dialogues)
    write_json(lang_dir / "visual_beats.json", visual_payload)

    ref_practice = read_json(ref_lang_dir / "practice_cards.json")
    practice_payload = read_json(lang_dir / "practice_cards.json")
    session, localized_cards = sync_practice_cards(language, ref_practice.get("practice_cards", []), ref_practice["mvp_session"])
    cards_by_id = {card["id"]: card for card in practice_payload.get("practice_cards", [])}
    for card in localized_cards:
        cards_by_id[card["id"]] = card
        target_id = card.get("target_id")
        if target_id:
            fallback_key = str(target_id).replace(f"{language}-", "en-")
            ensure_target(
                targets_payload,
                language,
                str(target_id),
                TARGET_FALLBACKS.get(str(target_id)) or TARGET_FALLBACKS.get(fallback_key),
            )
    practice_payload["mvp_session"] = session
    practice_payload["practice_cards"] = list(cards_by_id.values())
    write_json(lang_dir / "practice_cards.json", practice_payload)
    write_json(lang_dir / "targets.json", targets_payload)

    print(f"{language}: synced {len(updated_dialogues)} MVP dialogues, {len(localized_cards)} cards")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, type=Path)
    parser.add_argument("--language", action="append")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    languages = args.language or [lang for lang in LANGUAGES if lang != REFERENCE_LANGUAGE]
    for language in languages:
        equalize_language(data_dir, language)
    sync_visual_prompt_shared_prompts(data_dir)
    print("MVP content equalized.")


if __name__ == "__main__":
    main()
