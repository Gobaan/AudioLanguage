"""One-time content migration: food order targets -> one + please only."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG_DIR = ROOT / "model" / "content" / "languages"

TARGET_ID_SUFFIX = "one-local-food-please"

LANG_PHRASES = {
    "en": {
        "canonical": "One, please.",
        "transliteration": "One, please.",
        "display_meaning": "One, please.",
        "tts_text": "One, please.",
        "meaning_units": ["one", "please"],
        "accepted_variants": ["One please.", "Can I have one, please?"],
        "valid_but_off_target": ["Please.", "I want one."],
        "backward_build_spoken_prompts": ["please.", "One,", "One, please."],
        "backward_build_units": ["please", "One", "please"],
        "old_literals": [
            "One sandwich, please.",
            "Can I have one sandwich, please?",
            "A sandwich, please.",
            "I want a sandwich.",
            "One local food item, please.",
        ],
    },
    "ja": {
        "canonical": "一つください。",
        "transliteration": "Hitotsu kudasai.",
        "display_meaning": "One, please.",
        "tts_text": "一つください。",
        "meaning_units": ["one", "please"],
        "accepted_variants": [
            "ひとつください。",
            "一つお願いします。",
            "Hitotsu onegaishimasu.",
        ],
        "valid_but_off_target": ["ください。", "一つ。"],
        "backward_build_spoken_prompts": ["ください。", "一つ、", "一つください。"],
        "backward_build_units": ["kudasai", "Hitotsu", "kudasai"],
        "old_literals": [
            "Sandoicchi kudasai.",
            "サンドイッチください。",
            "サンドイッチをください。",
            "サンドイッチお願いします。",
            "サンドイッチを一つください。",
            "Sandwich, please.",
        ],
    },
    "zh": {
        "canonical": "一个，谢谢。",
        "transliteration": "Yi ge, xiexie.",
        "display_meaning": "One, please.",
        "tts_text": "一个，谢谢。",
        "meaning_units": ["one", "please"],
        "accepted_variants": ["Yi ge xiexie.", "一个谢谢。"],
        "valid_but_off_target": ["谢谢。", "一个。"],
        "backward_build_spoken_prompts": ["谢谢。", "一个，", "一个，谢谢。"],
        "backward_build_units": ["xiexie", "Yi ge", "xiexie"],
        "old_literals": [
            "Yi ge baozi, xiexie.",
            "Baozi, xiexie.",
            "Yi ge baozi.",
            "One baozi, please.",
        ],
    },
    "yue": {
        "canonical": "一个，唔该。",
        "transliteration": "Jat go, m goi.",
        "display_meaning": "One, please.",
        "tts_text": "一个，唔该。",
        "meaning_units": ["one", "please"],
        "accepted_variants": ["Jat go m goi.", "一个唔该。"],
        "valid_but_off_target": ["M goi.", "一个。"],
        "backward_build_spoken_prompts": ["唔该。", "一个，", "一个，唔该。"],
        "backward_build_units": ["m goi", "Jat go", "m goi"],
        "old_literals": [
            "Jat go bo lo baau, m goi.",
            "Bo lo baau, m goi.",
            "Jat go bo lo baau.",
            "One pineapple bun, please.",
        ],
    },
    "ta": {
        "canonical": "ஒரு, தயவு செய்து.",
        "transliteration": "Oru, thayavu seithu.",
        "display_meaning": "One, please.",
        "tts_text": "ஒரு, தயவு செய்து.",
        "meaning_units": ["one", "please"],
        "accepted_variants": ["Oru thayavu seithu.", "ஒரு தயavu seithu."],
        "valid_but_off_target": ["Thayavu seithu.", "Oru."],
        "backward_build_spoken_prompts": [
            "thayavu seithu.",
            "Oru,",
            "Oru, thayavu seithu.",
        ],
        "backward_build_units": ["thayavu seithu", "Oru", "thayavu seithu"],
        "old_literals": [
            "Oru dosai, thayavu seithu.",
            "Dosai, thayavu seithu.",
            "One dosa, please.",
        ],
    },
}

CONTRACT_REPLACEMENTS = [
    (r"Ask for a sandwich politely", "Point to one visible item and order politely"),
    (r"Order one sandwich politely", "Order one visible item politely"),
    (r"Ask for the sandwich politely", "Point to one visible item and order politely"),
    (r"Order a sandwich politely", "Order one visible item politely"),
    (r"Ask for a baozi politely", "Point to one visible item and order politely"),
    (r"Order one baozi politely", "Order one visible item politely"),
    (r"Ask for a pineapple bun politely", "Point to one visible item and order politely"),
    (r"Order one pineapple bun politely", "Order one visible item politely"),
    (r"Ask for a dosai politely", "Point to one visible item and order politely"),
    (r"Order one dosai politely", "Order one visible item politely"),
    (r"Ask for a sandwich politely in Cantonese", "Point to one visible item and order politely in Cantonese"),
    (r"Ask for a sandwich politely in English", "Point to one visible item and order politely in English"),
    (r"Ask for a sandwich politely in Japanese", "Point to one visible item and order politely in Japanese"),
    (r"Ask for a sandwich politely in Mandarin", "Point to one visible item and order politely in Mandarin"),
    (r"Ask for a sandwich politely in Tamil", "Point to one visible item and order politely in Tamil"),
    (r'"item": "sandwich"', '"visible_item": "counter_display"'),
    (r'"item": "baozi"', '"visible_item": "counter_display"'),
    (r'"item": "pineapple bun"', '"visible_item": "counter_display"'),
    (r'"item": "dosai"', '"visible_item": "counter_display"'),
    (
        "Accept an order for a sandwich even if the particle is omitted.",
        "Accept one + please even if the learner omits the comma or uses a short variant.",
    ),
    (
        "Accept an order for a sandwich even if the word one is omitted.",
        "Accept please-only or one + please variants when intent is clear.",
    ),
    (
        "Accept an order for a baozi even if the particle is omitted.",
        "Accept one + please even if the learner omits the comma or uses a short variant.",
    ),
    (
        "Accept romanized attempts such as sandoicchi kudasai when clear.",
        "Accept romanized attempts such as hitotsu kudasai when clear.",
    ),
]


def update_target(target: dict, phrase: dict) -> None:
    target["canonical"] = phrase["canonical"]
    target["transliteration"] = phrase["transliteration"]
    target["display_meaning"] = phrase["display_meaning"]
    target["meaning_units"] = phrase["meaning_units"]
    target["accepted_variants"] = phrase["accepted_variants"]
    if phrase.get("valid_but_off_target"):
        target["valid_but_off_target"] = phrase["valid_but_off_target"]
    target["backward_build_spoken_prompts"] = phrase["backward_build_spoken_prompts"]
    target["backward_build_units"] = phrase["backward_build_units"]
    notes = target.setdefault("notes", {})
    notes["spoken_target"] = "one + please; food item is scene-visible only"
    if "semantic_slots" in target and "required" in target["semantic_slots"]:
        required = target["semantic_slots"]["required"]
        required.pop("item", None)
        required.setdefault("visible_item", "counter_display")


def replace_literals_in_obj(obj, mapping: dict[str, str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "meaning_units" and value == ["one", "food_item", "please"]:
                obj[key] = ["one", "please"]
            elif isinstance(value, str):
                for old, new in mapping.items():
                    if value == old:
                        obj[key] = new
                        break
                    elif old in value:
                        obj[key] = value.replace(old, new)
            else:
                replace_literals_in_obj(value, mapping)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            if isinstance(item, str):
                for old, new in mapping.items():
                    if item == old:
                        obj[index] = new
                        break
                    elif old in item:
                        obj[index] = item.replace(old, new)
            else:
                replace_literals_in_obj(item, mapping)


def update_json_file(path: Path, mapping: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in mapping.items():
        text = text.replace(old, new)
    for pattern, replacement in CONTRACT_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    text = text.replace('"one",\n            "food_item",\n            "please"', '"one",\n            "please"')
    text = text.replace('"one",\n        "food_item",\n        "please"', '"one",\n        "please"')
    text = text.replace('"one",\n          "food_item",\n          "please"', '"one",\n          "please"')
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed: list[str] = []
    for lang, phrase in LANG_PHRASES.items():
        lang_root = LANG_DIR / lang
        mapping = {old: phrase["transliteration"] if old.isascii() and "please" in old.lower() else (
            phrase["canonical"] if any(ord(c) > 127 for c in old) else phrase["transliteration"]
        ) for old in phrase["old_literals"]}
        # Fix mapping to use correct new form per old string
        mapping = {
            "One sandwich, please.": phrase["transliteration"],
            "Can I have one sandwich, please?": phrase["accepted_variants"][-1] if lang == "en" else phrase["transliteration"],
            "A sandwich, please.": phrase["valid_but_off_target"][0] if lang == "en" else phrase["transliteration"],
            "I want a sandwich.": phrase["valid_but_off_target"][-1] if lang == "en" else phrase["transliteration"],
            "One local food item, please.": phrase["display_meaning"],
            "Sandoicchi kudasai.": phrase["transliteration"],
            "サンドイッチください。": phrase["canonical"],
            "サンドイッチをください。": phrase["accepted_variants"][0],
            "サンドイッチお願いします。": phrase["accepted_variants"][1],
            "サンドイッチを一つください。": phrase["accepted_variants"][1],
            "Sandwich, please.": phrase["display_meaning"],
            "Yi ge baozi, xiexie.": phrase["transliteration"],
            "Baozi, xiexie.": phrase["accepted_variants"][0],
            "Yi ge baozi.": phrase["valid_but_off_target"][-1],
            "One baozi, please.": phrase["display_meaning"],
            "Jat go bo lo baau, m goi.": phrase["transliteration"],
            "Bo lo baau, m goi.": phrase["accepted_variants"][0],
            "Jat go bo lo baau.": phrase["valid_but_off_target"][-1],
            "One pineapple bun, please.": phrase["display_meaning"],
            "Oru dosai, thayavu seithu.": phrase["transliteration"],
            "Dosai, thayavu seithu.": phrase["accepted_variants"][0],
            "One dosa, please.": phrase["display_meaning"],
        }

        targets_path = lang_root / "targets.json"
        targets_data = json.loads(targets_path.read_text(encoding="utf-8"))
        for target in targets_data["targets"]:
            if target["id"].endswith(TARGET_ID_SUFFIX) or target["id"] == f"{lang}-target-one-local-food-please":
                update_target(target, phrase)
                changed.append(str(targets_path))
        targets_path.write_text(json.dumps(targets_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        for name in ("dialogues.json", "practice_cards.json", "audio_assets.json", "visual_beats.json", "visual_prompts.json"):
            path = lang_root / name
            if path.exists() and update_json_file(path, mapping):
                changed.append(str(path))

        # Ensure learner lines use tts_text where present
        dialogues_path = lang_root / "dialogues.json"
        dialogues_data = json.loads(dialogues_path.read_text(encoding="utf-8"))
        for dialogue in dialogues_data.get("dialogues", []):
            if dialogue.get("function_id") != "order_local_food":
                continue
            for line in dialogue.get("lines", []):
                if line.get("line_type") != "learner_target":
                    continue
                line["text"] = phrase["canonical"]
                line["transliteration"] = phrase["transliteration"]
                line["audio_text"] = phrase["transliteration"]
                line["tts_text"] = phrase["tts_text"]
                line["meaning_units"] = phrase["meaning_units"]
        dialogues_path.write_text(
            json.dumps(dialogues_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed.append(str(dialogues_path))

    print("Updated files:")
    for path in sorted(set(changed)):
        print(f"  {path}")


if __name__ == "__main__":
    main()
