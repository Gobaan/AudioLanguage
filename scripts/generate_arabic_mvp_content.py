"""Generate Arabic MVP content by localizing the Japanese MVP scaffold."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from content_assets import DEFAULT_DATA_DIR, read_json, write_json

REFERENCE_LANGUAGE = "ja"
TARGET_LANGUAGE = "ar"

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

TARGET_TRANSLATIONS: dict[str, dict[str, Any]] = {
    "respond-hi": {
        "canonical": "مرحبًا!",
        "transliteration": "Marhaban!",
        "display_meaning": "Respond to hi.",
        "accepted_variants": ["مرحبًا", "أهلًا", "السلام عليكم"],
    },
    "my-name-is": {
        "canonical": "اسمي آنا.",
        "transliteration": "Ismi Anna.",
        "display_meaning": "My name is Anna.",
        "accepted_variants": ["اسمي آنا", "أنا آنا"],
    },
    "i-dont-understand": {
        "canonical": "لا أفهم.",
        "transliteration": "La afham.",
        "display_meaning": "I don't understand.",
        "accepted_variants": ["لا أفهم", "عذرًا، لا أفهم"],
    },
    "excuse-me-attention": {
        "canonical": "عذرًا.",
        "transliteration": "Udhiran.",
        "display_meaning": "Excuse me.",
        "accepted_variants": ["عذرًا", "لو سمحت"],
    },
    "one-local-food-please": {
        "canonical": "هذا.",
        "transliteration": "Hatha.",
        "display_meaning": "This one.",
        "accepted_variants": ["هذا", "هذا من فضلك"],
        "backward_build_spoken_prompts": ["هذا."],
        "backward_build_units": ["Hatha"],
    },
}

LINE_TRANSLATIONS: dict[str, list[dict[str, str]]] = {
    "first-hi-response": [
        {"text": "مرحبًا!", "transliteration": "Marhaban!"},
        {"text": "مرحبًا!", "transliteration": "Marhaban!"},
        {"text": "سعيدٌ بلقائك.", "transliteration": "Saeedun biliqaika."},
    ],
    "introduce-self": [
        {"text": "ما اسمك؟", "transliteration": "Ma ismuki?"},
        {"text": "اسمي آنا.", "transliteration": "Ismi Anna."},
        {"text": "تشرفتُ بمعرفتك.", "transliteration": "Tasharraftu bimarifatik."},
    ],
    "repair-dont-understand": [
        {"text": "هذا هنا.", "transliteration": "Hatha huna."},
        {"text": "لا أفهم.", "transliteration": "La afham."},
        {"text": "لا بأس.", "transliteration": "La bas."},
    ],
    "excuse-me-attention": [
        {"text": "التالي، من فضلك.", "transliteration": "Altali, min fadlik."},
        {"text": "عذرًا.", "transliteration": "Udhiran."},
        {"text": "نعم، تفضل.", "transliteration": "Naam, tafaddal."},
    ],
    "order-local-food": [
        {"text": "ماذا تريد؟", "transliteration": "Madha turid?"},
        {"text": "هذا.", "transliteration": "Hatha."},
        {"text": "حسنًا.", "transliteration": "Hasanan."},
    ],
    "greeting-neighbor-transfer": [
        {"text": "أهلًا!", "transliteration": "Ahlan!"},
        {"text": "مرحبًا!", "transliteration": "Marhaban!"},
        {"text": "أهلًا.", "transliteration": "Ahlan."},
    ],
    "introduce-class-transfer": [
        {"text": "اسمك لو سمحت؟", "transliteration": "Ismuk law samaht?"},
        {"text": "اسمي آنا.", "transliteration": "Ismi Anna."},
        {"text": "تشرفتُ بمعرفتك.", "transliteration": "Tasharraftu bimarifatik."},
    ],
    "repair-ticket-transfer": [
        {"text": "اضغط هنا.", "transliteration": "Idghat huna."},
        {"text": "لا أفهم.", "transliteration": "La afham."},
        {"text": "لا بأس.", "transliteration": "La bas."},
    ],
    "excuse-me-cafe-transfer": [
        {"text": "لحظة من فضلك.", "transliteration": "Lahza min fadlik."},
        {"text": "عذرًا.", "transliteration": "Udhiran."},
        {"text": "نعم، تفضل.", "transliteration": "Naam, tafaddal."},
    ],
    "order-convenience-transfer": [
        {"text": "أي واحد؟", "transliteration": "Ayy wahid?"},
        {"text": "هذا.", "transliteration": "Hatha."},
        {"text": "حسنًا.", "transliteration": "Hasanan."},
    ],
    "greeting-entry-review": [
        {"text": "مرحبًا.", "transliteration": "Marhaban."},
        {"text": "مرحبًا!", "transliteration": "Marhaban!"},
        {"text": "أهلًا.", "transliteration": "Ahlan."},
    ],
    "introduce-community-review": [
        {"text": "ما اسمك؟", "transliteration": "Ma ismuki?"},
        {"text": "اسمي آنا.", "transliteration": "Ismi Anna."},
        {"text": "أهلًا بك.", "transliteration": "Ahlan biki."},
    ],
    "repair-clinic-review": [
        {"text": "هذا هنا.", "transliteration": "Hatha huna."},
        {"text": "لا أفهم.", "transliteration": "La afham."},
        {"text": "سأساعدك.", "transliteration": "Sausaeduk."},
    ],
    "excuse-me-station-review": [
        {"text": "التالي.", "transliteration": "Altali."},
        {"text": "عذرًا.", "transliteration": "Udhiran."},
        {"text": "نعم.", "transliteration": "Naam."},
    ],
    "order-bakery-review": [
        {"text": "ماذا تختار؟", "transliteration": "Madha takhtar?"},
        {"text": "هذا.", "transliteration": "Hatha."},
        {"text": "حسنًا.", "transliteration": "Hasanan."},
    ],
}

MVP_TARGET_SUFFIXES = {
    "respond-hi",
    "my-name-is",
    "i-dont-understand",
    "excuse-me-attention",
    "one-local-food-please",
}


def replace_prefix(value: str, source_lang: str, target_lang: str) -> str:
    if value.startswith(f"{source_lang}-"):
        return f"{target_lang}-{value[len(source_lang) + 1:]}"
    return value


def localize_ids(value: Any, source_lang: str, target_lang: str) -> Any:
    if isinstance(value, str):
        return replace_prefix(value, source_lang, target_lang)
    if isinstance(value, list):
        return [localize_ids(item, source_lang, target_lang) for item in value]
    if isinstance(value, dict):
        return {key: localize_ids(item, source_lang, target_lang) for key, item in value.items()}
    return value


def dialogue_suffix(dialogue_id: str, language: str) -> str:
    prefix = f"{language}-"
    if dialogue_id.startswith(prefix):
        return dialogue_id[len(prefix) :]
    return dialogue_id


def target_suffix(target_id: str) -> str:
    if "-target-" not in target_id:
        return target_id
    return target_id.split("-target-", 1)[1]


def localized_target_from_reference(reference_target: dict[str, Any]) -> dict[str, Any]:
    localized = localize_ids(copy.deepcopy(reference_target), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
    suffix = target_suffix(str(localized["id"]))
    translated = TARGET_TRANSLATIONS[suffix]
    localized["canonical"] = translated["canonical"]
    localized["transliteration"] = translated["transliteration"]
    localized["display_meaning"] = translated["display_meaning"]
    localized["accepted_variants"] = translated["accepted_variants"]
    localized["notes"] = {**localized.get("notes", {}), "native_review_required": True}
    if "backward_build_spoken_prompts" in translated:
        localized["backward_build_spoken_prompts"] = translated["backward_build_spoken_prompts"]
    if "backward_build_units" in translated:
        localized["backward_build_units"] = translated["backward_build_units"]
    return localized


def localized_dialogue_from_reference(reference_dialogue: dict[str, Any]) -> dict[str, Any]:
    localized = localize_ids(copy.deepcopy(reference_dialogue), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
    suffix = dialogue_suffix(str(localized["id"]), TARGET_LANGUAGE)
    translated_lines = LINE_TRANSLATIONS[suffix]
    for index, line in enumerate(localized.get("lines", [])):
        translated = translated_lines[index]
        line["text"] = translated["text"]
        line["transliteration"] = translated["transliteration"]
        if line.get("line_type") == "learner_target":
            line["target_id"] = str(localized.get("target_id"))
            if suffix in {"introduce-self", "introduce-class-transfer", "introduce-community-review"}:
                # Force an initial /i/ pronunciation for "ismi" in TTS while
                # keeping learner-facing text simple.
                line["tts_text"] = "اِسمي آنا."
            if suffix in {"order-local-food", "order-convenience-transfer", "order-bakery-review"}:
                line["audio_text"] = translated["transliteration"]
                line["tts_text"] = translated["text"]
    return localized


def update_card_language_content(card: dict[str, Any], target_lookup: dict[str, dict[str, Any]]) -> None:
    card["expected_response"] = target_lookup[card["target_id"]]["canonical"]
    target_transliteration = target_lookup[card["target_id"]]["transliteration"]
    if card.get("target_id", "").endswith("one-local-food-please"):
        card["expected_transliteration"] = target_transliteration
    ai_contract = card.get("ai_scene_contract", {})
    if isinstance(ai_contract, dict):
        ai_contract["language_being_practiced"] = "Arabic"
        ai_contract["learner_intention"] = str(ai_contract.get("learner_intention", "")).replace(
            "Japanese", "Arabic"
        )
        ai_contract["example_valid_responses"] = target_lookup[card["target_id"]]["accepted_variants"]


def generate_language_files(data_dir: Path) -> None:
    reference_dir = data_dir / "languages" / REFERENCE_LANGUAGE
    target_dir = data_dir / "languages" / TARGET_LANGUAGE
    target_dir.mkdir(parents=True, exist_ok=True)

    reference_targets = read_json(reference_dir / "targets.json")
    reference_dialogues = read_json(reference_dir / "dialogues.json")
    reference_practice = read_json(reference_dir / "practice_cards.json")
    reference_visual_beats = read_json(reference_dir / "visual_beats.json")
    reference_audio_assets = read_json(reference_dir / "audio_assets.json")
    reference_visual_prompts = read_json(reference_dir / "visual_prompts.json")

    mvp_reference_cards = set(reference_practice["mvp_session"]["cards"])
    selected_dialogue_ids = {f"{REFERENCE_LANGUAGE}-{suffix}" for suffix in MVP_DIALOGUE_SUFFIXES}

    localized_targets = []
    for target in reference_targets.get("targets", []):
        suffix = target_suffix(str(target.get("id", "")))
        if suffix not in MVP_TARGET_SUFFIXES:
            continue
        localized_targets.append(localized_target_from_reference(target))
    target_lookup = {target["id"]: target for target in localized_targets}

    localized_dialogues = []
    for dialogue in reference_dialogues.get("dialogues", []):
        if dialogue.get("id") not in selected_dialogue_ids:
            continue
        localized_dialogues.append(localized_dialogue_from_reference(dialogue))
    dialogue_lookup = {dialogue["id"]: dialogue for dialogue in localized_dialogues}

    localized_cards = []
    for card in reference_practice.get("practice_cards", []):
        if card.get("id") not in mvp_reference_cards:
            continue
        localized = localize_ids(copy.deepcopy(card), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
        update_card_language_content(localized, target_lookup)
        localized_cards.append(localized)

    localized_session = localize_ids(copy.deepcopy(reference_practice["mvp_session"]), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
    localized_session["name"] = "Arabic starter anchor, transfer, and review test"
    localized_session["goal"] = (
        "Test whether five short Arabic chunks transfer from anchor scenes into new visual "
        "contexts and delayed review scenes."
    )

    localized_visual_beats = []
    for beat in reference_visual_beats.get("visual_beats", []):
        if beat.get("dialogue_id") not in selected_dialogue_ids:
            continue
        localized = localize_ids(copy.deepcopy(beat), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
        dialogue_id = str(localized["dialogue_id"])
        line_index = int(localized["line_index"])
        localized["line_text"] = dialogue_lookup[dialogue_id]["lines"][line_index]["text"]
        localized_visual_beats.append(localized)

    localized_audio_assets = []
    for asset in reference_audio_assets.get("assets", []):
        if asset.get("dialogue_id") not in selected_dialogue_ids:
            continue
        localized = localize_ids(copy.deepcopy(asset), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
        dialogue_id = str(localized["dialogue_id"])
        line_index = int(localized["line_index"])
        line = dialogue_lookup[dialogue_id]["lines"][line_index]
        localized["text"] = line["text"]
        localized["transliteration"] = line.get("transliteration", "")
        localized["voice_id"] = f"ar-{localized['character_id']}"
        voice_profile = localized.get("voice_profile", {})
        if isinstance(voice_profile, dict):
            voice_profile["id"] = localized["voice_id"]
        localized_audio_assets.append(localized)

    localized_visual_prompts = []
    for prompt in reference_visual_prompts.get("prompts", []):
        if prompt.get("dialogue_id") not in selected_dialogue_ids:
            continue
        localized = localize_ids(copy.deepcopy(prompt), REFERENCE_LANGUAGE, TARGET_LANGUAGE)
        localized_visual_prompts.append(localized)

    targets_payload = {
        "language": TARGET_LANGUAGE,
        "display_name": "Arabic",
        "metadata": {
            "description": "Arabic starter and transfer scenes.",
            "scene_sets": ["mvp", "delayed"],
            "sort_order": 3,
        },
        "script": "Arabic",
        "native_review_status": "needs_native_review",
        "targets": localized_targets,
    }

    dialogues_payload = {
        "language": TARGET_LANGUAGE,
        "display_name": "Arabic",
        "script": "Arabic",
        "native_review_status": "needs_native_review",
        "dialogues": localized_dialogues,
    }

    practice_payload = {
        "language": TARGET_LANGUAGE,
        "display_name": "Arabic",
        "script": "Arabic",
        "native_review_status": "needs_native_review",
        "mvp_session": localized_session,
        "practice_cards": localized_cards,
    }

    visual_beats_payload = {
        "language": TARGET_LANGUAGE,
        "display_name": "Arabic",
        "script": "Arabic",
        "native_review_status": "needs_native_review",
        "visual_beats": localized_visual_beats,
    }

    audio_assets_payload = {
        **copy.deepcopy(reference_audio_assets),
        "language": TARGET_LANGUAGE,
        "display_name": "Arabic",
        "script": "Arabic",
        "source": "data/languages/ar/dialogues.json",
        "assets": localized_audio_assets,
    }

    visual_prompts_payload = {
        **copy.deepcopy(reference_visual_prompts),
        "language": TARGET_LANGUAGE,
        "display_name": "Arabic",
        "script": "Arabic",
        "source": [
            "data/curriculum/functions.json",
            "data/curriculum/scenes.json",
            "data/languages/ar/targets.json",
            "data/languages/ar/dialogues.json",
        ],
        "prompts": localized_visual_prompts,
    }

    write_json(target_dir / "targets.json", targets_payload)
    write_json(target_dir / "dialogues.json", dialogues_payload)
    write_json(target_dir / "practice_cards.json", practice_payload)
    write_json(target_dir / "visual_beats.json", visual_beats_payload)
    write_json(target_dir / "audio_assets.json", audio_assets_payload)
    write_json(target_dir / "visual_prompts.json", visual_prompts_payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    generate_language_files(data_dir)
    print("Generated Arabic MVP language content.")


if __name__ == "__main__":
    main()
