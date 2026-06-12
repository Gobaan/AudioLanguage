from __future__ import annotations

import re
from typing import Any

from app.content.lessons import chunks_for_target, meaning_choice_difficulty, meaning_choices

LESSON_STEP_TYPES = [
    "scene_setup",
    "target_audio",
    "broad_meaning_guess",
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
    opener_frame = frame_for_line_type(frames, "world_opener") or first_frame(frames)
    learner_frame = frame_for_line_type(frames, "learner_target") or opener_frame
    response_frame = frame_for_line_type(frames, "world_response") or learner_frame
    opener_audio = opener_frame.get("audioUrl") if opener_frame else None
    opener_audio_text = opener_frame.get("audioText") if opener_frame else None
    target_audio = learner_line.get("audio")
    target_audio_text = learner_line.get("audio_text") or learner_line.get("transliteration") or learner_line.get("text")
    is_anchor_lesson = card.get("stage") == "guided_scene_production"

    steps = [
        step(
            "scene_setup",
            "SceneFrame",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="Listen.",
            audio=audio_behavior(opener_audio, autoplay=True, replayable=True, audio_text=opener_audio_text),
            mic=mic_off(),
            props={
                "initialFrameId": frames[0]["id"] if frames else None,
                "frames": frames,
            },
        )
    ]

    if is_anchor_lesson:
        steps.extend(
            [
                step(
                    "target_audio",
                    "AudioButton",
                    frame_id=learner_frame.get("id") if learner_frame else None,
                    frame_mode="single",
                    display_text="Listen to what they say.",
                    audio=audio_behavior(target_audio, autoplay=True, replayable=True, audio_text=target_audio_text),
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
                        "question": "What happened?",
                        "difficulty": meaning_choice_difficulty(card),
                        "choices": meaning_choices(target, card),
                    },
                ),
                step(
                    "repeat_with_mic",
                    "MicPrompt",
                    frame_id=learner_frame.get("id") if learner_frame else None,
                    frame_mode="single",
                    display_text="Now say it.",
                    audio=audio_behavior(
                        target_audio,
                        autoplay=True,
                        replayable=True,
                        play_before_mic=True,
                        audio_text=target_audio_text,
                    ),
                    mic=recording_mic(target_text, target_transliteration, starts_after_audio=True),
                    props={
                        "expectedText": target_text,
                        "expectedTransliteration": target_transliteration,
                        "text": localized_mic_text(card),
                    },
                ),
            ]
        )

        if should_include_backward_build(target=target, target_phrase=target_phrase):
            steps.append(
                step(
                    "backward_build",
                    "BackwardBuild",
                    frame_id=learner_frame.get("id") if learner_frame else None,
                    frame_mode="neutral",
                    display_text="Build it from the end.",
                    audio=audio_behavior(target_audio, autoplay=False, replayable=True, audio_text=target_audio_text),
                    mic=recording_mic(target_text, target_transliteration),
                    props={
                        "targetPhrase": target_phrase,
                        "chunks": chunks_for_target(target),
                        "prompts": backward_build_prompts(
                            target=target,
                            target_phrase=target_phrase,
                            target_audio=target_audio,
                        ),
                    },
                )
            )

        return steps

    steps.extend(
        [
            step(
                "broad_meaning_guess",
                "ChoicePrompt",
                frame_id=opener_frame.get("id") if opener_frame else None,
                frame_mode="single",
                display_text="What is the best response here?",
                audio=audio_behavior(opener_audio, autoplay=False, replayable=True, audio_text=opener_audio_text),
                mic=mic_off(),
                props={
                    "question": "What is the best response here?",
                    "difficulty": meaning_choice_difficulty(card),
                    "choices": meaning_choices(target, card),
                },
            ),
            step(
                "scene_recall",
                "SceneFrame",
                frame_id=opener_frame.get("id") if opener_frame else None,
                frame_mode="single",
                display_text="What would you say?",
                audio=audio_behavior(
                    opener_audio,
                    autoplay=True,
                    replayable=True,
                    play_before_mic=True,
                    audio_text=opener_audio_text,
                ),
                mic=recording_mic(target_text, target_transliteration, starts_after_audio=True),
                props={
                    "initialFrameId": opener_frame.get("id") if opener_frame else None,
                    "frames": frames,
                },
            ),
        ]
    )

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
    audio_text: str | None = None,
) -> dict[str, Any]:
    return {
        "url": url,
        "audioText": audio_text,
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
    units = backward_build_units(target=target, target_phrase=target_phrase)
    prompts = []
    for index in range(len(units) - 1, -1, -1):
        text = " ".join(units[index:])
        if index == 0:
            text = target_phrase
        prompts.append(
            {
                "id": f"{target['id']}-build-{index}",
                "text": text,
                "audioUrl": target_audio if index == 0 else None,
                "audioText": text,
                "mic": recording_mic(text, ""),
            }
        )
    return prompts


def should_include_backward_build(*, target: dict[str, Any], target_phrase: str) -> bool:
    return len(backward_build_units(target=target, target_phrase=target_phrase)) >= 3


def backward_build_units(*, target: dict[str, Any], target_phrase: str) -> list[str]:
    explicit_units = target.get("backward_build_units")
    if isinstance(explicit_units, list):
        units = [str(unit).strip() for unit in explicit_units if str(unit).strip()]
        if units:
            return units

    return re.findall(r"[\w']+", target_phrase, flags=re.UNICODE)


DEFAULT_AUDIO_LABELS = {"playLabel": "Play audio", "playingLabel": "Playing"}
DEFAULT_MIC_LABELS = {
    "prompt": "Try saying it",
    "listeningLabel": "Listening...",
    "startLabel": "Start",
}


def localized_audio_text(card: dict[str, Any]) -> dict[str, str]:
    return card.get("ui_labels", {}).get("audio", DEFAULT_AUDIO_LABELS)


def localized_mic_text(card: dict[str, Any]) -> dict[str, str]:
    return card.get("ui_labels", {}).get("mic", DEFAULT_MIC_LABELS)
