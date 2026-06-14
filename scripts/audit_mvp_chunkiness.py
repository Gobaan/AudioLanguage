"""Audit MVP anchor learner phrases for backward-build chunkiness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.content.lesson_steps import backward_build_prompts, backward_build_units

LANGS = ["en", "ja", "zh", "yue", "ta"]
ANCHOR_TABS = ["hello", "introduce", "repair", "excuse-me", "food-order"]
FLAG_BB = 4
WATCH_BB = 3


def audit_lang(lang: str) -> list[dict]:
    root = Path("model/content/languages") / lang
    targets = {t["id"]: t for t in json.loads((root / "targets.json").read_text(encoding="utf-8"))["targets"]}
    pc = json.loads((root / "practice_cards.json").read_text(encoding="utf-8"))
    cards = {c["id"]: c for c in pc.get("practice_cards", [])}
    rows = []
    for tab in pc["mvp_session"]["lesson_tabs"]:
        if tab["id"] not in ANCHOR_TABS:
            continue
        card = cards[tab["card_id"]]
        target = targets[card["target_id"]]
        phrase = target.get("transliteration") or target.get("canonical", "")
        units = backward_build_units(target=target, target_phrase=phrase)
        prompts = backward_build_prompts(
            target=target,
            target_phrase=phrase,
            target_text=target["canonical"],
            target_transliteration=phrase,
            language=lang,
        )
        focus = target.get("backward_build_focus_units") or []
        rows.append(
            {
                "lang": lang,
                "tab": tab["id"],
                "function": target.get("function_id"),
                "phrase": phrase,
                "meaning": target.get("display_meaning", ""),
                "units": len(units),
                "bb_steps": len(prompts),
                "first_step": prompts[0].get("focusLabel") or prompts[0].get("audioText") if prompts else "",
                "last_step": prompts[-1].get("text") if prompts else "",
            }
        )
    return rows


def main() -> None:
    rows = []
    for lang in LANGS:
        rows.extend(audit_lang(lang))

    print("MVP ANCHOR CHUNK AUDIT (5 scenes x 5 languages)")
    print(f"FLAG: bb_steps >= {FLAG_BB}  |  WATCH: bb_steps == {WATCH_BB}")
    print()
    for lang in LANGS:
        print(f"=== {lang.upper()} ===")
        for row in [r for r in rows if r["lang"] == lang]:
            if row["bb_steps"] >= FLAG_BB:
                flag = " [FLAG]"
            elif row["bb_steps"] == WATCH_BB:
                flag = " [watch]"
            else:
                flag = ""
            print(f"  {row['tab']}{flag}: {row['phrase']}")
            print(f"    {row['meaning']} | bb={row['bb_steps']} | ladder: {row['first_step']} -> {row['last_step']}")
        print()

    flagged = [r for r in rows if r["bb_steps"] >= FLAG_BB]
    watch = [r for r in rows if r["bb_steps"] == WATCH_BB]

    print("=== FLAGGED (>=4 BB steps) ===")
    if not flagged:
        print("  none")
    for row in sorted(flagged, key=lambda r: (-r["bb_steps"], r["lang"], r["tab"])):
        print(f"  {row['lang']} {row['tab']}: {row['phrase']} ({row['bb_steps']} steps)")

    print()
    print("=== WATCH (3 BB steps — acceptable if chunks are short) ===")
    for row in sorted(watch, key=lambda r: (r["lang"], r["tab"])):
        print(f"  {row['lang']} {row['tab']}: {row['phrase']}")


if __name__ == "__main__":
    main()
