from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.content.models import ContentGraph, DialogueCard, DialogueCategory, DialogueLine


DEFAULT_REVIEW_MODES = ["listen", "echo", "produce_from_visual"]


def load_content_graph(dialogues_path: Path) -> ContentGraph:
    """Load dialogue source JSON into the app's content graph model."""
    data = json.loads(dialogues_path.read_text(encoding="utf-8"))
    categories = [
        load_category(category)
        for category in data.get("categories", [])
    ]
    return ContentGraph(categories=categories)


def load_category(category: dict[str, Any]) -> DialogueCategory:
    category_id = str(category["id"])
    category_label = str(category["label"])

    return DialogueCategory(
        id=category_id,
        label=category_label,
        scenes=[
            load_dialogue_card(
                scene=scene,
                category_id=category_id,
                category_label=category_label,
            )
            for scene in category.get("scenes", [])
        ],
    )


def load_dialogue_card(
    *,
    scene: dict[str, Any],
    category_id: str,
    category_label: str,
) -> DialogueCard:
    scene_id = str(scene["id"])
    lines = [
        load_dialogue_line(scene_id=scene_id, line_index=index, line=line)
        for index, line in enumerate(scene.get("lines", []))
    ]

    return DialogueCard(
        id=scene_id,
        situation=str(scene["situation"]),
        difficulty=int(scene.get("difficulty", 1)),
        lines=lines,
        category=category_id,
        category_label=category_label,
        type=str(scene.get("type", "anchor")),
        function_id=scene.get("function_id"),
        target_id=scene.get("target_id"),
        review_modes=list(scene.get("review_modes", DEFAULT_REVIEW_MODES)),
    )


def load_dialogue_line(
    *,
    scene_id: str,
    line_index: int,
    line: dict[str, Any],
) -> DialogueLine:
    speaker = str(line["speaker"])

    return DialogueLine(
        speaker=speaker,
        text=str(line["text"]),
        audio=f"/audio/{scene_id}-{line_index}.mp3",
        visual=f"/visuals/{scene_id}/frame-{line_index}.png",
        is_learner_target=speaker == "learner",
    )
