#!/usr/bin/env python3
"""Compare whether all MVP languages expose the same lesson set."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG_DIRS = ROOT / "model" / "content" / "languages"
LANGS = ["en", "ja", "zh", "yue", "ta"]


def load(lang: str, name: str) -> dict:
    return json.loads((LANG_DIRS / lang / name).read_text(encoding="utf-8"))


def main() -> None:
    print("=== MVP LESSON TABS (same tab ids?) ===")
    tab_sets: dict[str, dict[str, list[str]]] = {}
    for lang in LANGS:
        sess = load(lang, "practice_cards.json")["mvp_session"]
        tab_sets[lang] = {
            "main": [tab["id"] for tab in sess.get("lesson_tabs", [])],
            "delayed": [tab["id"] for tab in sess.get("delayed_lesson_tabs", [])],
        }
        print(f"  {lang}: main={tab_sets[lang]['main']}")
        print(f"        delayed={tab_sets[lang]['delayed']}")

    base = tab_sets["en"]
    for lang in LANGS[1:]:
        print(
            f"  {lang} vs en: "
            f"main={'same' if tab_sets[lang]['main'] == base['main'] else 'DIFFERENT'}, "
            f"delayed={'same' if tab_sets[lang]['delayed'] == base['delayed'] else 'DIFFERENT'}"
        )

    print("\n=== CARD COUNTS ===")
    for lang in LANGS:
        cards = load(lang, "practice_cards.json").get("practice_cards", [])
        by_stage: dict[str, int] = defaultdict(int)
        for card in cards:
            by_stage[str(card.get("stage", "?"))] += 1
        print(f"  {lang}: {len(cards)} cards -> {dict(by_stage)}")

    print("\n=== COMMUNICATIVE FUNCTIONS (same five + transfers?) ===")
    for lang in LANGS:
        targets = load(lang, "targets.json")["targets"]
        functions = sorted({str(target.get("function_id", "?")) for target in targets})
        print(f"  {lang}: {functions}")

    print("\n=== PER-TAB STAGE PARITY VS ENGLISH ===")
    en_cards = {card["id"]: card for card in load("en", "practice_cards.json")["practice_cards"]}
    en_tabs = load("en", "practice_cards.json")["mvp_session"]["lesson_tabs"]
    for lang in LANGS:
        cards = {card["id"]: card for card in load(lang, "practice_cards.json")["practice_cards"]}
        tabs = load(lang, "practice_cards.json")["mvp_session"]["lesson_tabs"]
        mismatches: list[str] = []
        for en_tab, tab in zip(en_tabs, tabs):
            if tab["id"] != en_tab["id"]:
                mismatches.append(f"tab order/id {tab['id']} != {en_tab['id']}")
                continue
            en_card = en_cards[en_tab["card_id"]]
            card = cards[tab["card_id"]]
            if card.get("stage") != en_card.get("stage"):
                mismatches.append(f"{tab['id']} stage {card.get('stage')} != {en_card.get('stage')}")
        status = "matches en" if not mismatches else f"{len(mismatches)} mismatches"
        print(f"  {lang}: {status}")
        for item in mismatches[:5]:
            print(f"    - {item}")


if __name__ == "__main__":
    main()
