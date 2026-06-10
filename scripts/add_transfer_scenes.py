"""Add same-day transfer scenes to language content files.

This is a maintenance helper for the current MVP content graph. It only adds
missing transfer dialogues/cards/tabs and leaves existing entries unchanged.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LANG_DIR = ROOT / "model" / "content" / "languages"


TRANSFER_SCENES: dict[str, dict[str, Any]] = {
    "en": {
        "hello-transfer": {
            "asset_slug": "greeting-neighbor-transfer",
            "scene_id": "neighbor-gate",
            "speaker_role": "neighbor",
            "source_card": "hello",
            "lines": ["Hi!", "Hi!", "Good to see you."],
        },
        "introduce-transfer": {
            "asset_slug": "introduce-class-transfer",
            "scene_id": "language-class-name-tags",
            "speaker_role": "class_partner",
            "source_card": "introduce",
            "lines": ["What's your name?", "My name is Anna.", "Nice to meet you, Anna."],
        },
        "repair-transfer": {
            "asset_slug": "repair-ticket-transfer",
            "scene_id": "ticket-machine-help",
            "speaker_role": "station_helper",
            "source_card": "repair",
            "lines": ["Press here, please.", "Sorry, I don't understand.", "No problem. I'll help."],
        },
        "food-order-transfer": {
            "asset_slug": "order-convenience-transfer",
            "scene_id": "convenience-store-sandwich",
            "speaker_role": "cashier",
            "source_card": "food-order",
            "lines": ["What would you like?", "One sandwich, please.", "Sure."],
        },
    },
    "ta": {
        "hello-transfer": {
            "asset_slug": "greeting-neighbor-transfer",
            "scene_id": "neighbor-gate",
            "speaker_role": "neighbor",
            "source_card": "hello",
            "lines": [
                ("Vanakkam!", "வணக்கம்!"),
                ("Vanakkam! Nalama?", "வணக்கம்! நலமா?"),
                ("Nalam, nandri.", "நலம், நன்றி."),
            ],
        },
        "introduce-transfer": {
            "asset_slug": "introduce-class-transfer",
            "scene_id": "language-class-name-tags",
            "speaker_role": "class_partner",
            "source_card": "introduce",
            "lines": [
                ("Ungal peyar enna?", "உங்கள் பெயர் என்ன?"),
                ("En peyar Anna.", "என் பெயர் Anna."),
                ("Sandhosham, Anna.", "சந்தோஷம், Anna."),
            ],
        },
        "repair-transfer": {
            "asset_slug": "repair-ticket-transfer",
            "scene_id": "ticket-machine-help",
            "speaker_role": "station_helper",
            "source_card": "repair",
            "lines": [
                ("Inge azhuthunga.", "இங்கே அழுத்துங்க."),
                ("Mannikkavum, enakku puriyala.", "மன்னிக்கவும், எனக்கு புரியல."),
                ("Parava illai. Naan udhavi panren.", "பரவாயில்லை. நான் உதவி பண்றேன்."),
            ],
        },
    },
    "yue": {
        "hello-transfer": {
            "asset_slug": "greeting-neighbor-transfer",
            "scene_id": "neighbor-gate",
            "speaker_role": "neighbor",
            "source_card": "hello",
            "lines": [
                ("Nei hou!", "你好！"),
                ("Nei hou!", "你好！"),
                ("Hou aa.", "好呀。"),
            ],
        },
        "introduce-transfer": {
            "asset_slug": "introduce-class-transfer",
            "scene_id": "language-class-name-tags",
            "speaker_role": "class_partner",
            "source_card": "introduce",
            "lines": [
                ("Nei giu mat meng?", "你叫乜名？"),
                ("Ngo giu Anna.", "我叫 Anna。"),
                ("Hou hoi sam sik nei, Anna.", "好開心識你，Anna。"),
            ],
        },
        "repair-transfer": {
            "asset_slug": "repair-ticket-transfer",
            "scene_id": "ticket-machine-help",
            "speaker_role": "station_helper",
            "source_card": "repair",
            "lines": [
                ("M goi aam ni dou.", "唔該撳呢度。"),
                ("M hou ji si, ngo m ming.", "唔好意思，我唔明。"),
                ("M gan yiu. Ngo bong nei.", "唔緊要。我幫你。"),
            ],
        },
        "excuse-me-transfer": {
            "asset_slug": "excuse-me-cafe-transfer",
            "scene_id": "cafe-counter-attention",
            "speaker_role": "barista",
            "source_card": "excuse-me",
            "lines": [
                ("Dang jat dang.", "等一等。"),
                ("M goi.", "唔該。"),
                ("Hai, nei hou.", "係，你好。"),
            ],
        },
        "food-order-transfer": {
            "asset_slug": "order-convenience-transfer",
            "scene_id": "convenience-store-sandwich",
            "speaker_role": "cashier",
            "source_card": "food-order",
            "lines": [
                ("Nei yiu mat?", "你要乜？"),
                ("Jat go bo lo baau, m goi.", "一個菠蘿包，唔該。"),
                ("Hou aa.", "好呀。"),
            ],
        },
    },
    "zh": {
        "hello-transfer": {
            "asset_slug": "greeting-neighbor-transfer",
            "scene_id": "neighbor-gate",
            "speaker_role": "neighbor",
            "source_card": "hello",
            "lines": [
                ("Ni hao!", "你好！"),
                ("Ni hao!", "你好！"),
                ("Hao de.", "好的。"),
            ],
        },
        "introduce-transfer": {
            "asset_slug": "introduce-class-transfer",
            "scene_id": "language-class-name-tags",
            "speaker_role": "class_partner",
            "source_card": "introduce",
            "lines": [
                ("Ni jiao shenme mingzi?", "你叫什么名字？"),
                ("Wo jiao Anna.", "我叫 Anna。"),
                ("Hen gaoxing renshi ni, Anna.", "很高兴认识你，Anna。"),
            ],
        },
        "repair-transfer": {
            "asset_slug": "repair-ticket-transfer",
            "scene_id": "ticket-machine-help",
            "speaker_role": "station_helper",
            "source_card": "repair",
            "lines": [
                ("Qing an zheli.", "请按这里。"),
                ("Bu hao yisi, wo bu dong.", "不好意思，我不懂。"),
                ("Mei guanxi. Wo bang ni.", "没关系。我帮你。"),
            ],
        },
        "excuse-me-transfer": {
            "asset_slug": "excuse-me-cafe-transfer",
            "scene_id": "cafe-counter-attention",
            "speaker_role": "barista",
            "source_card": "excuse-me",
            "lines": [
                ("Qing deng yixia.", "请等一下。"),
                ("Qing wen.", "请问。"),
                ("Hao, ni hao.", "好，你好。"),
            ],
        },
        "food-order-transfer": {
            "asset_slug": "order-convenience-transfer",
            "scene_id": "convenience-store-sandwich",
            "speaker_role": "cashier",
            "source_card": "food-order",
            "lines": [
                ("Ni yao shenme?", "你要什么？"),
                ("Yi ge baozi, xiexie.", "一个包子，谢谢。"),
                ("Hao de.", "好的。"),
            ],
        },
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_line(index: int, role: str, line_type: str, target_id: str | None, text_spec: Any) -> dict[str, Any]:
    if isinstance(text_spec, tuple):
        text, tts_text = text_spec
    else:
        text, tts_text = text_spec, text_spec
    line: dict[str, Any] = {
        "index": index,
        "speaker_role": role,
        "line_type": line_type,
        "text": text,
        "transliteration": text,
        "audio_text": text,
        "meaning_units": [],
    }
    if tts_text != text:
        line["tts_text"] = tts_text
    if target_id:
        line["target_id"] = target_id
    return line


def transfer_card_from_source(language: str, tab_id: str, dialogue_id: str, source_card: dict[str, Any]) -> dict[str, Any]:
    card = deepcopy(source_card)
    card["id"] = f"{language}-card-{tab_id}-same_day_transfer"
    card["dialogue_id"] = dialogue_id
    card["stage"] = "same_day_transfer"
    card["prompt"] = "Use the new scene. Say your part when prompted, then hear the model line."
    card["success_signal"] = f"learner reuses {card['target_id']} in a same day transfer scene"
    card["playback_flow"] = [
        {"type": "play_line", "line_type": "world_opener", "state": "partner_cue"},
        {"type": "record_attempt", "line_type": "learner_target", "judgement": "deferred"},
        {"type": "play_line", "line_type": "learner_target", "state": "model_line"},
        {"type": "play_line", "line_type": "world_response", "state": "social_response", "optional": True},
    ]
    contract = card.get("ai_scene_contract")
    if isinstance(contract, dict):
        contract["learner_intention"] = contract.get("learner_intention", "").replace(" in English.", f" in {display_name(language)}.")
    return card


def display_name(language: str) -> str:
    return {"en": "English", "ta": "Tamil", "yue": "Cantonese", "zh": "Mandarin"}.get(language, language)


def add_transfers(language: str, transfers: dict[str, dict[str, Any]]) -> None:
    lang_dir = LANG_DIR / language
    dialogues_path = lang_dir / "dialogues.json"
    cards_path = lang_dir / "practice_cards.json"
    dialogues_payload = read_json(dialogues_path)
    cards_payload = read_json(cards_path)

    dialogues = dialogues_payload.setdefault("dialogues", [])
    dialogue_ids = {item["id"] for item in dialogues}
    cards = cards_payload.setdefault("practice_cards", [])
    cards_by_id = {item["id"]: item for item in cards}
    tabs = cards_payload.setdefault("mvp_session", {}).setdefault("lesson_tabs", [])
    tab_by_id = {tab["id"]: tab for tab in tabs if isinstance(tab, dict) and "id" in tab}

    for tab_id, spec in transfers.items():
        source_tab = tab_by_id.get(spec["source_card"])
        if not source_tab:
            continue
        source_card = cards_by_id[source_tab["card_id"]]
        dialogue_id = f"{language}-{spec['asset_slug']}"
        target_id = source_card["target_id"]
        partner_role = spec["speaker_role"]
        lines = spec["lines"]

        if dialogue_id not in dialogue_ids:
            dialogues.append(
                {
                    "id": dialogue_id,
                    "asset_slug": spec["asset_slug"],
                    "type": "transfer",
                    "function_id": source_card["correct_function_id"],
                    "target_id": target_id,
                    "scene_id": spec["scene_id"],
                    "review_modes": ["produce_from_visual", "ai_guided_response"],
                    "lines": [
                        build_line(0, partner_role, "world_opener", None, lines[0]),
                        build_line(1, "learner", "learner_target", target_id, lines[1]),
                        build_line(2, partner_role, "world_response", None, lines[2]),
                    ],
                }
            )
            dialogue_ids.add(dialogue_id)

        card_id = f"{language}-card-{tab_id}-same_day_transfer"
        if card_id not in cards_by_id:
            cards.append(transfer_card_from_source(language, tab_id, dialogue_id, source_card))
            cards_by_id[card_id] = cards[-1]

        if tab_id not in tab_by_id:
            tabs.append({"id": tab_id, "label": f"Scene {len(tabs) + 1}", "card_id": card_id})
            tab_by_id[tab_id] = tabs[-1]

        session_cards = cards_payload["mvp_session"].setdefault("cards", [])
        if card_id not in session_cards:
            session_cards.append(card_id)

    write_json(dialogues_path, dialogues_payload)
    write_json(cards_path, cards_payload)


def main() -> None:
    for language, transfers in TRANSFER_SCENES.items():
        add_transfers(language, transfers)


if __name__ == "__main__":
    main()
