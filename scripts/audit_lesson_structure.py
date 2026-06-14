#!/usr/bin/env python3
"""Summarize frame counts, dialogue shape, and lesson step counts across MVP languages."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG_ROOT = ROOT / "model" / "content"
LANG_DIRS = LANG_ROOT / "languages"
PROJECT_DIR = ROOT
LANGS = ["en", "ja", "zh", "yue", "ta"]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.content.lessons import lesson_from_card  # noqa: E402
from app.content.session_hydration import load_language_session  # noqa: E402


def dialogue_frame_counts(lang: str) -> dict[str, int]:
    vb = json.loads((LANG_DIRS / lang / "visual_beats.json").read_text(encoding="utf-8"))
    counts: dict[str, int] = defaultdict(int)
    for beat in vb.get("visual_beats", []):
        counts[str(beat.get("dialogue_id", "?"))] += 1
    return dict(counts)


def dialogue_line_counts(lang: str) -> dict[str, int]:
    data = json.loads((LANG_DIRS / lang / "dialogues.json").read_text(encoding="utf-8"))
    return {dlg["id"]: len(dlg.get("lines", [])) for dlg in data.get("dialogues", [])}


def backward_build_steps(lang: str) -> dict[str, int]:
    data = json.loads((LANG_DIRS / lang / "targets.json").read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for target in data.get("targets", []):
        ladder = target.get("backward_build") or []
        out[target["id"]] = len(ladder)
    return out


def compare(label: str, ids: list[str], per_lang: dict[str, dict[str, int]]) -> None:
    print(f"\n=== {label} ===")
    mismatches = 0
    for item_id in ids:
        vals = {lang: per_lang[lang].get(item_id) for lang in LANGS}
        present = [v for v in vals.values() if v is not None]
        same = len(set(present)) <= 1
        if not same:
            mismatches += 1
        status = "OK" if same else "MISMATCH"
        print(f"  {item_id}: {vals} [{status}]")
    print(f"  ({len(ids)} items, {mismatches} mismatches)")


def lesson_step_counts(lang: str, card_id: str) -> int:
    session = load_language_session(data_dir=LANG_ROOT, project_dir=PROJECT_DIR, language=lang)
    card = next(card for card in session["cards"] if card["id"] == card_id)
    lesson = lesson_from_card(lang, card)
    return len(lesson.get("steps", []))


def main() -> None:
    all_frames = {lang: dialogue_frame_counts(lang) for lang in LANGS}
    all_lines = {lang: dialogue_line_counts(lang) for lang in LANGS}
    all_bb = {lang: backward_build_steps(lang) for lang in LANGS}

    dialogue_ids = sorted(set().union(*[set(d.keys()) for d in all_frames.values()]))
    target_ids = sorted(set().union(*[set(d.keys()) for d in all_bb.values()]))

    compare("FRAMES PER DIALOGUE (visual beats)", dialogue_ids, all_frames)
    compare("DIALOGUE LINE COUNTS", dialogue_ids, all_lines)
    compare("BACKWARD BUILD STEPS PER TARGET", target_ids, all_bb)

    print("\n=== UNIQUE FRAME COUNTS PER LANGUAGE ===")
    for lang in LANGS:
        unique = sorted(set(all_frames[lang].values()))
        print(f"  {lang}: {unique}")

    print("\n=== ESTIMATED SESSION TIME (practice_cards) ===")
    for lang in LANGS:
        pc = json.loads((LANG_DIRS / lang / "practice_cards.json").read_text(encoding="utf-8"))
        sess = pc.get("mvp_session", {})
        print(
            f"  {lang}: {sess.get('estimated_minutes')} min/session, "
            f"{len(sess.get('lesson_tabs', []))} main tabs, "
            f"{len(sess.get('delayed_lesson_tabs', []))} delayed tabs"
        )

    print("\n=== RUNTIME STEPS PER LESSON TAB (EN sample) ===")
    pc = json.loads((LANG_DIRS / "en" / "practice_cards.json").read_text(encoding="utf-8"))
    sess = pc.get("mvp_session", {})
    en_session = load_language_session(data_dir=LANG_ROOT, project_dir=PROJECT_DIR, language="en")
    cards_by_id = {card["id"]: card for card in en_session["cards"]}
    for tab in sess.get("lesson_tabs", []) + sess.get("delayed_lesson_tabs", []):
        card_id = tab["card_id"]
        card = cards_by_id[card_id]
        steps = lesson_step_counts("en", card_id)
        frames = all_frames["en"].get(card.get("dialogue_id", ""), "?")
        bb = all_bb["en"].get(card.get("target_id", ""), "?")
        print(
            f"  {tab['id']:20} stage={card.get('stage','?'):28} "
            f"frames={frames} bb={bb} runtime_steps={steps}"
        )


if __name__ == "__main__":
    main()
