from __future__ import annotations

from typing import Any


LESSON_STEP_TYPES = [
    "scene_setup",
    "target_audio",
    "broad_meaning_guess",
    "translation_reveal",
    "audio_replay",
    "repeat_with_mic",
    "backward_build",
    "production_prompt",
    "scene_recall",
    "transfer_scene",
    "micro_note",
    "mini_roleplay",
    "audio_only_recognition",
    "different_speaker",
    "natural_speed",
    "similar_phrase_contrast",
    "schedule_review",
]


def lessons_from_session(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Return frontend lesson records derived from hydrated practice cards."""
    return [lesson_from_card(session["language"], card) for card in session.get("cards", [])]


def lesson_from_card(language: str, card: dict[str, Any]) -> dict[str, Any]:
    dialogue = card["dialogue"]
    target = card["target"]
    scene = card["scene"]
    learner_line = find_learner_line(dialogue.get("lines", []))
    frames = frame_data(dialogue.get("lines", []))

    return {
        "id": card["id"],
        "language": language,
        "title": lesson_title(card, target, scene),
        "mode": card.get("mode"),
        "stage": card.get("stage"),
        "player_component": player_component_for(card),
        "target": {
            "id": target["id"],
            "text": learner_line.get("text") or target.get("canonical", ""),
            "transliteration": learner_line.get("transliteration") or target.get("transliteration", ""),
            "meaning": target.get("display_meaning", ""),
        },
        "frames": frames,
        "steps": lesson_steps(card=card, target=target, scene=scene, learner_line=learner_line, frames=frames),
    }


def lesson_steps(
    *,
    card: dict[str, Any],
    target: dict[str, Any],
    scene: dict[str, Any],
    learner_line: dict[str, Any],
    frames: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    steps = [
        step(
            "scene_setup",
            "SceneFrame",
            {
                "initialFrameId": frames[0]["id"] if frames else None,
                "frames": frames,
            },
        ),
        step(
            "target_audio",
            "AudioButton",
            {
                "audioUrl": learner_line.get("audio"),
                "text": localized_audio_text(card),
            },
        ),
        step(
            "broad_meaning_guess",
            "ChoicePrompt",
            {
                "question": card.get("prompt") or "What does the learner need to do?",
                "choices": meaning_choices(target, card),
            },
        ),
        step(
            "translation_reveal",
            "TranslationReveal",
            {
                "translation": target.get("display_meaning", ""),
            },
        ),
        step(
            "audio_replay",
            "AudioButton",
            {
                "audioUrl": learner_line.get("audio"),
                "text": localized_audio_text(card),
            },
        ),
        step(
            "repeat_with_mic",
            "MicPrompt",
            {
                "expectedText": learner_line.get("text") or target.get("canonical", ""),
                "expectedTransliteration": learner_line.get("transliteration") or target.get("transliteration", ""),
                "text": localized_mic_text(card),
            },
        ),
        step(
            "backward_build",
            "BackwardBuild",
            {
                "targetPhrase": learner_line.get("transliteration") or target.get("transliteration", ""),
                "chunks": chunks_for_target(target),
            },
        ),
        step(
            "production_prompt",
            "ProductionPrompt",
            {
                "cue": card.get("prompt") or target.get("display_meaning", ""),
                "targetMeaning": target.get("display_meaning", ""),
                "micText": localized_mic_text(card),
            },
        ),
        step(
            "mini_roleplay",
            "MiniRoleplay",
            {
                "scenario": card.get("ai_scene_contract", {}).get("physical_scene") or scene.get("description", ""),
                "targetMeaning": target.get("display_meaning", ""),
            },
        ),
        step(
            "audio_only_recognition",
            "AudioOnlyRecognition",
            {
                "prompt": target.get("display_meaning", ""),
                "audioText": localized_audio_text(card),
                "micText": localized_mic_text(card),
            },
        ),
        step(
            "similar_phrase_contrast",
            "SimilarPhraseContrast",
            {
                "explanation": "Choose the phrase that matches this scene.",
                "choices": phrase_contrast_choices(target),
            },
        ),
        step(
            "schedule_review",
            "ProgressCard",
            {
                "title": "Review schedule",
                "metrics": review_metrics(card),
            },
        ),
    ]

    if card.get("stage") == "same_day_transfer":
        steps.insert(
            8,
            step(
                "transfer_scene",
                "SceneFrame",
                {
                    "initialFrameId": frames[0]["id"] if frames else None,
                    "frames": frames,
                },
            ),
        )
    if card.get("stage") == "delayed_review":
        steps.insert(
            8,
            step(
                "scene_recall",
                "SceneFrame",
                {
                    "initialFrameId": frames[0]["id"] if frames else None,
                    "frames": frames,
                },
            ),
        )

    return steps


def step(step_type: str, component: str, props: dict[str, Any]) -> dict[str, Any]:
    if step_type not in LESSON_STEP_TYPES:
        raise ValueError(f"Unknown lesson step type: {step_type}")
    return {
        "id": step_type,
        "type": step_type,
        "component": component,
        "props": props,
    }


def frame_data(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames = []
    for line in lines:
        frames.append(
            {
                "id": f"line-{line.get('index', len(frames))}",
                "lineIndex": line.get("index"),
                "imageUrl": line.get("visual"),
                "audioUrl": line.get("audio"),
                "title": line.get("line_type", "scene").replace("_", " ").title(),
                "speaker": line.get("speaker_role", ""),
                "text": line.get("text", ""),
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


def player_component_for(card: dict[str, Any]) -> str:
    if card.get("stage") == "delayed_review":
        return "TVLessonPlayer"
    return "TravellerLessonPlayer"


def meaning_choices(target: dict[str, Any], card: dict[str, Any]) -> list[dict[str, Any]]:
    choices = [{"id": target["id"], "label": target.get("display_meaning", target["id"]), "isCorrect": True}]
    contract = card.get("ai_scene_contract", {})
    for wrong_intent in contract.get("likely_wrong_intents", [])[:3]:
        wrong_id = wrong_intent.get("id", wrong_intent.get("definition", "wrong"))
        choices.append(
            {
                "id": str(wrong_id),
                "label": wrong_intent.get("definition", str(wrong_id)),
                "isCorrect": False,
            }
        )
    return choices


def phrase_contrast_choices(target: dict[str, Any]) -> list[dict[str, Any]]:
    choices = [
        {
            "id": f"{target['id']}-target",
            "label": target.get("transliteration") or target.get("canonical", target["id"]),
            "isCorrect": True,
        }
    ]
    for index, phrase in enumerate(target.get("valid_but_off_target", [])[:2]):
        choices.append({"id": f"{target['id']}-contrast-{index}", "label": phrase, "isCorrect": False})
    return choices


def chunks_for_target(target: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{target['id']}-chunk-{index}",
            "text": str(unit).replace("_", " "),
            "meaning": str(unit).replace("_", " "),
        }
        for index, unit in enumerate(target.get("meaning_units", []))
    ]


def review_metrics(card: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"label": "Stage", "value": str(card.get("stage", ""))},
        {"label": "Mode", "value": str(card.get("mode", ""))},
    ]


def localized_audio_text(card: dict[str, Any]) -> dict[str, str]:
    support_language = card.get("ai_scene_contract", {}).get("support_language", "English")
    if support_language == "Japanese":
        return {"playLabel": "音声を再生", "playingLabel": "再生中"}
    return {"playLabel": "Play audio", "playingLabel": "Playing"}


def localized_mic_text(card: dict[str, Any]) -> dict[str, str]:
    support_language = card.get("ai_scene_contract", {}).get("support_language", "English")
    if support_language == "Japanese":
        return {"prompt": "言ってみましょう", "listeningLabel": "聞いています...", "startLabel": "はじめる"}
    return {"prompt": "Try saying it", "listeningLabel": "Listening...", "startLabel": "Start"}
