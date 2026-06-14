from __future__ import annotations

import hashlib
from typing import Any


def lessons_from_session(
    session: dict[str, Any],
    *,
    choice_order_seed: str | None = None,
) -> list[dict[str, Any]]:
    """Return frontend lesson records derived from hydrated practice cards."""
    return [
        lesson_from_card(session["language"], card, choice_order_seed=choice_order_seed)
        for card in session.get("cards", [])
    ]


def lesson_from_card(
    language: str,
    card: dict[str, Any],
    *,
    choice_order_seed: str | None = None,
) -> dict[str, Any]:
    from app.content.lesson_steps import lesson_steps

    dialogue = card["dialogue"]
    target = card["target"]
    scene = card["scene"]
    learner_line = find_learner_line(dialogue.get("lines", []))
    frames = frame_data(dialogue.get("lines", []))
    target_text = learner_line.get("display_text") or learner_line.get("text") or target.get("canonical", "")
    target_transliteration = learner_line.get("transliteration") or target.get("transliteration", "")

    return {
        "id": card["id"],
        "language": language,
        "title": lesson_title(card, target, scene),
        "mode": card.get("mode"),
        "stage": card.get("stage"),
        "target": {
            "id": target["id"],
            "text": target_transliteration or target_text,
            "transliteration": target_transliteration,
            "meaning": target.get("display_meaning", ""),
        },
        "frames": frames,
        "steps": lesson_steps(
            language=language,
            card=card,
            target=target,
            scene=scene,
            learner_line=learner_line,
            frames=frames,
            choice_order_seed=choice_order_seed,
        ),
    }


def frame_data(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames = []
    for line in lines:
        line_index = line.get("index", len(frames))
        display_text = line.get("display_text") or line.get("transliteration") or line.get("text", "")
        audio_text = line.get("audio_text") or line.get("transliteration") or line.get("text", "")
        frames.append(
            {
                "id": f"line-{line_index}",
                "lineIndex": line_index,
                "frameNumber": int(line_index) + 1,
                "imageUrl": line.get("visual"),
                "audioUrl": line.get("audio"),
                "audioText": audio_text,
                "title": line.get("line_type", "scene").replace("_", " ").title(),
                "speaker": line.get("speaker_role", ""),
                "text": display_text,
                "originalText": line.get("text", ""),
                "transliteration": line.get("transliteration", ""),
                "lineType": line.get("line_type", ""),
            }
        )
    return frames


def find_learner_line(lines: list[dict[str, Any]]) -> dict[str, Any]:
    for line in lines:
        if line.get("line_type") == "learner_target":
            return line
    return lines[0] if lines else {}


def lesson_title(card: dict[str, Any], target: dict[str, Any], scene: dict[str, Any]) -> str:
    if card.get("prompt"):
        return str(card["prompt"])
    meaning = target.get("display_meaning")
    environment = scene.get("environment")
    if meaning and environment:
        return f"{meaning} - {environment}"
    return str(meaning or card["id"])


def meaning_choices(
    target: dict[str, Any],
    card: dict[str, Any],
    *,
    choice_order_seed: str | None = None,
) -> list[dict[str, Any]]:
    distractor_set = card.get("distractors")
    if distractor_set:
        difficulty = meaning_choice_difficulty(card)
        levels = distractor_set.get("levels", {})
        distractors = levels.get(difficulty) or levels.get("easy", [])
        correct = distractor_set.get("correct") or {
            "id": target["id"],
            "label": target.get("display_meaning", target["id"]),
        }
        choices = [
            {
                "id": str(correct.get("id", target["id"])),
                "label": clean_choice_label(correct.get("label", target.get("display_meaning", target["id"]))),
                "isCorrect": True,
                "difficulty": difficulty,
            }
        ]
        for distractor in distractors:
            choices.append(
                {
                    "id": str(distractor.get("id", distractor.get("label", "distractor"))),
                    "label": clean_choice_label(distractor.get("label", distractor.get("id", "Distractor"))),
                    "isCorrect": False,
                    "difficulty": difficulty,
                }
            )
        if len(choices) > 1:
            return order_meaning_choices(choices, card, choice_order_seed)

    choices = [{"id": target["id"], "label": clean_choice_label(target.get("display_meaning", target["id"])), "isCorrect": True}]
    contract = card.get("ai_scene_contract", {})
    wrong_intents = contract.get("likely_wrong_intents") or contract.get("wrong_intents", [])
    for wrong_intent in wrong_intents[:3]:
        wrong_id = wrong_intent.get("id", wrong_intent.get("definition", "wrong"))
        choices.append(
            {
                "id": str(wrong_id),
                "label": clean_choice_label(wrong_intent.get("definition", str(wrong_id))),
                "isCorrect": False,
            }
        )
    return order_meaning_choices(choices, card, choice_order_seed)


def order_meaning_choices(
    choices: list[dict[str, Any]],
    card: dict[str, Any],
    choice_order_seed: str | None,
) -> list[dict[str, Any]]:
    if len(choices) <= 1:
        return choices

    seed = choice_order_seed or "default"
    card_id = str(card.get("id", "unknown-card"))
    ordered = sorted(
        choices,
        key=lambda choice: stable_choice_sort_key(seed, card_id, str(choice.get("id", ""))),
    )
    if ordered[0].get("isCorrect") and any(not choice.get("isCorrect") for choice in ordered):
        return ordered[1:] + ordered[:1]
    return ordered


def stable_choice_sort_key(seed: str, card_id: str, choice_id: str) -> str:
    value = f"{seed}:{card_id}:{choice_id}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def clean_choice_label(value: Any) -> str:
    label = str(value).strip()
    prefixes = (
        "The learner says that they ",
        "The learner says they ",
        "The learner says ",
        "Learner says that they ",
        "Learner says they ",
        "Learner says ",
    )
    for prefix in prefixes:
        if label.startswith(prefix):
            label = label[len(prefix) :]
            break

    return label[:1].upper() + label[1:] if label else label


def meaning_choice_difficulty(card: dict[str, Any]) -> str:
    explicit_difficulty = card.get("meaning_choice_difficulty")
    if explicit_difficulty:
        return str(explicit_difficulty)
    if card.get("stage") == "same_day_transfer":
        return "medium"
    if card.get("stage") == "delayed_review":
        return "hard"
    return "easy"


ANCHOR_MEANING_CHOICE_OVERRIDES: dict[str, dict[str, str]] = {
    "order_local_food": {
        "question": "What did they say?",
        "display_text": "What did they say?",
    },
}


def meaning_choice_question(card: dict[str, Any], target: dict[str, Any]) -> str:
    function_id = str(card.get("correct_function_id") or target.get("function_id") or "")
    if card.get("stage") == "guided_scene_production":
        override = ANCHOR_MEANING_CHOICE_OVERRIDES.get(function_id)
        if override:
            return override["question"]
    if card.get("stage") in {"same_day_transfer", "delayed_review"}:
        return "What is the best response here?"
    return "What happened?"


def meaning_choice_display_text(card: dict[str, Any], target: dict[str, Any]) -> str:
    function_id = str(card.get("correct_function_id") or target.get("function_id") or "")
    if card.get("stage") == "guided_scene_production":
        override = ANCHOR_MEANING_CHOICE_OVERRIDES.get(function_id)
        if override:
            return override["display_text"]
    if card.get("stage") in {"same_day_transfer", "delayed_review"}:
        return "What is the best response here?"
    return "What happened?"


def chunks_for_target(target: dict[str, Any]) -> list[dict[str, Any]]:
    labels = target.get("meaning_unit_labels", {})
    chunks = []
    for index, unit in enumerate(target.get("meaning_units", [])):
        unit_key = str(unit)
        chunks.append(
            {
                "id": f"{target['id']}-chunk-{index}",
                "text": str(labels.get(unit_key, unit_key.replace("_", " "))).strip(),
                "meaning": unit_key,
            }
        )
    return chunks
