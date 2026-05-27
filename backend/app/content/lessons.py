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
    target_text = learner_line.get("text") or target.get("canonical", "")
    target_transliteration = learner_line.get("transliteration") or target.get("transliteration", "")
    target_phrase = target_transliteration or target_text
    target_meaning = target.get("display_meaning", "")
    opener_frame = frame_for_line_type(frames, "world_opener") or first_frame(frames)
    learner_frame = frame_for_line_type(frames, "learner_target") or opener_frame
    response_frame = frame_for_line_type(frames, "world_response") or learner_frame
    opener_audio = opener_frame.get("audioUrl") if opener_frame else None
    target_audio = learner_line.get("audio")

    steps = [
        step(
            "scene_setup",
            "SceneFrame",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="Listen.",
            audio=audio_behavior(opener_audio, autoplay=True, replayable=True),
            mic=mic_off(),
            props={
                "initialFrameId": frames[0]["id"] if frames else None,
                "frames": frames,
            },
        ),
        step(
            "target_audio",
            "AudioButton",
            frame_id=learner_frame.get("id") if learner_frame else None,
            frame_mode="single",
            display_text="Listen to what they say.",
            audio=audio_behavior(target_audio, autoplay=True, replayable=True),
            mic=mic_off(),
            props={
                "audioUrl": target_audio,
                "text": localized_audio_text(card),
            },
        ),
        step(
            "broad_meaning_guess",
            "ChoicePrompt",
            frame_id=response_frame.get("id") if response_frame else None,
            frame_mode="single",
            display_text="What happened?",
            audio=audio_behavior(target_audio, autoplay=False, replayable=True),
            mic=mic_off(),
            props={
                "question": card.get("prompt") or "What does the learner need to do?",
                "choices": meaning_choices(target, card),
            },
        ),
        step(
            "translation_reveal",
            "TranslationReveal",
            frame_id=learner_frame.get("id") if learner_frame else None,
            frame_mode="strip",
            display_text=target_text,
            audio=audio_behavior(target_audio, autoplay=True, replayable=True),
            mic=mic_off(),
            props={
                "translation": target_meaning,
                "usage": target_meaning,
            },
        ),
        step(
            "audio_replay",
            "AudioButton",
            frame_id=learner_frame.get("id") if learner_frame else None,
            frame_mode="single",
            display_text="Listen again.",
            audio=audio_behavior(target_audio, autoplay=True, replayable=True),
            mic=mic_off(),
            props={
                "audioUrl": target_audio,
                "text": localized_audio_text(card),
            },
        ),
        step(
            "repeat_with_mic",
            "MicPrompt",
            frame_id=learner_frame.get("id") if learner_frame else None,
            frame_mode="single",
            display_text="Now say it.",
            audio=audio_behavior(target_audio, autoplay=True, replayable=True, play_before_mic=True),
            mic=recording_mic(target_text, target_transliteration, starts_after_audio=True),
            props={
                "expectedText": target_text,
                "expectedTransliteration": target_transliteration,
                "text": localized_mic_text(card),
            },
        ),
        step(
            "backward_build",
            "BackwardBuild",
            frame_id=learner_frame.get("id") if learner_frame else None,
            frame_mode="neutral",
            display_text="Build it from the end.",
            audio=audio_behavior(target_audio, autoplay=False, replayable=True),
            mic=recording_mic(target_text, target_transliteration),
            props={
                "targetPhrase": target_phrase,
                "chunks": chunks_for_target(target),
                "prompts": backward_build_prompts(target=target, target_phrase=target_phrase, target_audio=target_audio),
            },
        ),
        step(
            "production_prompt",
            "ProductionPrompt",
            frame_id=None,
            frame_mode="neutral",
            display_text=f"How do you say: {prompt_text(target_meaning)}?",
            audio=audio_behavior(None, autoplay=False, replayable=False),
            mic=recording_mic(target_text, target_transliteration),
            props={
                "cue": card.get("prompt") or target.get("display_meaning", ""),
                "targetMeaning": target_meaning,
                "micText": localized_mic_text(card),
            },
        ),
        step(
            "scene_recall",
            "SceneFrame",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="What would you say?",
            audio=audio_behavior(opener_audio, autoplay=True, replayable=True, play_before_mic=True),
            mic=recording_mic(target_text, target_transliteration, starts_after_audio=True),
            props={
                "initialFrameId": opener_frame.get("id") if opener_frame else None,
                "frames": frames,
            },
        ),
    ]

    return steps


def step(
    step_type: str,
    component: str,
    *,
    frame_id: str | None,
    frame_mode: str,
    display_text: str,
    audio: dict[str, Any],
    mic: dict[str, Any],
    props: dict[str, Any],
) -> dict[str, Any]:
    if step_type not in LESSON_STEP_TYPES:
        raise ValueError(f"Unknown lesson step type: {step_type}")
    return {
        "id": step_type,
        "type": step_type,
        "component": component,
        "frameId": frame_id,
        "frameMode": frame_mode,
        "displayText": display_text,
        "audio": audio,
        "mic": mic,
        "props": props,
    }


def first_frame(frames: list[dict[str, Any]]) -> dict[str, Any] | None:
    return frames[0] if frames else None


def frame_for_line_type(frames: list[dict[str, Any]], line_type: str) -> dict[str, Any] | None:
    for frame in frames:
        if frame.get("lineType") == line_type:
            return frame
    return None


def audio_behavior(
    url: str | None,
    *,
    autoplay: bool,
    replayable: bool,
    play_before_mic: bool = False,
) -> dict[str, Any]:
    return {
        "url": url,
        "autoplay": autoplay,
        "replayable": replayable,
        "playBeforeMic": play_before_mic,
    }


def mic_off() -> dict[str, Any]:
    return {
        "enabled": False,
        "record": False,
        "scoring": "none",
    }


def recording_mic(
    expected_text: str,
    expected_transliteration: str,
    *,
    starts_after_audio: bool = False,
) -> dict[str, Any]:
    return {
        "enabled": True,
        "record": True,
        "startsAfterAudio": starts_after_audio,
        "expectedText": expected_text,
        "expectedTransliteration": expected_transliteration,
        "scoring": "deferred",
        "continueOnRecord": True,
        "blockingFeedback": False,
    }


def backward_build_prompts(
    *,
    target: dict[str, Any],
    target_phrase: str,
    target_audio: str | None,
) -> list[dict[str, Any]]:
    units = [str(unit).replace("_", " ") for unit in target.get("meaning_units", [])]
    prompts = []
    for index in range(len(units)):
        text = " ".join(units[index:])
        prompts.append(
            {
                "id": f"{target['id']}-build-{index}",
                "text": text,
                "audioUrl": target_audio,
                "mic": recording_mic(text, ""),
            }
        )
    prompts.append(
        {
            "id": f"{target['id']}-build-full",
            "text": target_phrase,
            "audioUrl": target_audio,
            "mic": recording_mic(target_phrase, ""),
        }
    )
    return prompts


def prompt_text(value: str) -> str:
    return value.rstrip(" .?!")


def frame_data(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames = []
    for line in lines:
        line_index = line.get("index", len(frames))
        frames.append(
            {
                "id": f"line-{line_index}",
                "lineIndex": line_index,
                "frameNumber": int(line_index) + 1,
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
