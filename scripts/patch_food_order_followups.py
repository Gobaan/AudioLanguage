"""Patch practice cards and visual beats after one-please food migration."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG_DIR = ROOT / "model" / "content" / "languages"

EXAMPLE_RESPONSES = {
    "en": ["One, please.", "One please.", "Can I have one, please?"],
    "ja": ["一つください", "一つください。", "ひとつください", "Hitotsu kudasai."],
    "zh": ["一个，谢谢", "一个，谢谢。", "Yi ge, xiexie."],
    "yue": ["一个，唔该", "一个，唔该。", "Jat go, m goi."],
    "ta": ["ஒரு, தயவு செய்து", "Oru, thayavu seithu."],
}

ACCEPTANCE_NOTES = {
    "en": [
        "Accept one + please even if the learner omits the comma or uses a short variant.",
        "Accept please-only when the learner is clearly pointing at one visible item.",
    ],
    "ja": [
        "Accept one + please even if the learner omits punctuation or uses kana-only forms.",
        "Accept romanized attempts such as hitotsu kudasai when clear.",
    ],
    "zh": [
        "Accept one + please even if the learner omits the comma or uses a short variant.",
        "Accept romanized attempts such as yi ge xiexie when clear.",
    ],
    "yue": [
        "Accept one + please even if the learner omits the comma or uses a short variant.",
        "Accept romanized attempts such as jat go m goi when clear.",
    ],
    "ta": [
        "Accept one + please even if the learner omits the comma or uses a short variant.",
        "Accept romanized attempts such as oru thayavu seithu when clear.",
    ],
}


def patch_practice_cards(lang: str) -> None:
    path = LANG_DIR / lang / "practice_cards.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for card in data.get("practice_cards", []):
        if card.get("correct_function_id") != "order_local_food":
            continue
        contract = card.setdefault("ai_scene_contract", {})
        contract["example_valid_responses"] = EXAMPLE_RESPONSES[lang]
        contract["acceptance_notes"] = ACCEPTANCE_NOTES[lang]
        intention = contract.get("learner_intention", "")
        if any(
            token in intention.lower()
            for token in ("sandwich", "baozi", "pineapple", "dosai", "dosa")
        ):
            contract["learner_intention"] = (
                f"Point to one visible item and order politely in {contract.get('language_being_practiced', lang)}."
            )
        changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_visual_beats(lang: str) -> None:
    path = LANG_DIR / lang / "visual_beats.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for beat in data.get("visual_beats", []):
        if beat.get("function_id") != "order_local_food":
            continue
        if beat.get("timing_role") != "learner_turn":
            continue
        beat["meaning_units"] = ["one", "please"]
        for mapping in beat.get("gesture_mapping", []):
            mapping["meaning_unit"] = "one,please"
            cue = mapping.get("visual_cue", "")
            if "sandwich" in cue or "baozi" in cue or "pineapple" in cue or "dosai" in cue:
                mapping["visual_cue"] = "learner points to one visible item and asks politely"
            elif "food" not in cue.lower() and "item" not in cue.lower():
                mapping["visual_cue"] = "learner points to one visible item and asks politely"
        changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_en_target_wrong_example() -> None:
    path = LANG_DIR / "en" / "targets.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for target in data["targets"]:
        if target["id"] == "en-target-excuse-me-attention":
            target["wrong_for_context_examples"] = [
                example.replace("One sandwich, please.", "One, please.")
                for example in target.get("wrong_for_context_examples", [])
            ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for lang in EXAMPLE_RESPONSES:
        patch_practice_cards(lang)
        patch_visual_beats(lang)
    patch_en_target_wrong_example()
    print("Patched practice cards and visual beats.")


if __name__ == "__main__":
    main()
