from __future__ import annotations

import re
from typing import Any

from app.content.graph_core import public_path
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
    language: str,
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

    if is_anchor_lesson:
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
            ),
            step(
                "broad_meaning_guess",
                "ChoicePrompt",
                frame_id=response_frame.get("id") if response_frame else None,
                frame_mode="single",
                display_text="What happened?",
                audio=audio_behavior(target_audio, autoplay=False, replayable=True, audio_text=target_audio_text),
                mic=mic_off(),
                props={
                    "question": "What happened?",
                    "difficulty": meaning_choice_difficulty(card),
                    "choices": meaning_choices(target, card),
                },
            ),
        ]

        steps.append(
            backward_build_step(
                card=card,
                target=target,
                learner_line=learner_line,
                learner_frame=learner_frame,
                target_text=target_text,
                target_transliteration=target_transliteration,
                target_phrase=target_phrase,
                target_audio=target_audio,
                target_audio_text=target_audio_text,
                language=language,
            )
        )

        return steps

    return transfer_review_steps(
        card=card,
        target=target,
        frames=frames,
        opener_frame=opener_frame,
        learner_frame=learner_frame,
        response_frame=response_frame,
        opener_audio=opener_audio,
        opener_audio_text=opener_audio_text,
        target_text=target_text,
        target_transliteration=target_transliteration,
    )


def transfer_review_steps(
    *,
    card: dict[str, Any],
    target: dict[str, Any],
    frames: list[dict[str, Any]],
    opener_frame: dict[str, Any] | None,
    learner_frame: dict[str, Any] | None,
    response_frame: dict[str, Any] | None,
    opener_audio: str | None,
    opener_audio_text: str | None,
    target_text: str,
    target_transliteration: str,
) -> list[dict[str, Any]]:
    playback_flow = card.get("playback_flow")
    if not isinstance(playback_flow, list) or not playback_flow:
        raise ValueError(f"Practice card '{card.get('id')}' is missing playback_flow for transfer/review.")

    record_before_model = _record_before_model_line(playback_flow)
    include_world_response = _includes_world_response_feedback(playback_flow)

    return [
        step(
            "scene_setup",
            "SceneFrame",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="Listen.",
            audio=audio_behavior(opener_audio, autoplay=True, replayable=True, audio_text=opener_audio_text),
            mic=mic_off(),
            props={
                "initialFrameId": opener_frame.get("id") if opener_frame else None,
                "frames": frames,
                "stopAtLineType": "world_opener",
                "playbackFlow": playback_flow,
            },
        ),
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
                "revealDialogueAfterChoice": False,
                "revealDialogueOnIncorrectOnly": True,
            },
        ),
        step(
            "scene_recall",
            "ProductionPrompt",
            frame_id=opener_frame.get("id") if opener_frame else None,
            frame_mode="single",
            display_text="What would you say?",
            audio=audio_behavior(None, autoplay=False, replayable=False, play_before_mic=False),
            mic=recording_mic(target_text, target_transliteration, starts_after_audio=False),
            props={
                "playbackFlow": playback_flow,
                "recordBeforeModelLine": record_before_model,
                "playModelLineAfterAttempt": True,
                "playWorldResponseAfterAttempt": include_world_response,
                "showDialogueRevealAfterAttempt": True,
            },
        ),
    ]


def _record_before_model_line(playback_flow: list[dict[str, Any]]) -> bool:
    record_index = next(
        (index for index, item in enumerate(playback_flow) if item.get("type") == "record_attempt"),
        -1,
    )
    if record_index < 0:
        return True

    for item in playback_flow[:record_index]:
        if item.get("type") == "play_line" and item.get("line_type") == "learner_target":
            return False
    return True


def _includes_world_response_feedback(playback_flow: list[dict[str, Any]]) -> bool:
    record_index = next(
        (index for index, item in enumerate(playback_flow) if item.get("type") == "record_attempt"),
        -1,
    )
    if record_index < 0:
        return False

    for item in playback_flow[record_index + 1 :]:
        if item.get("type") == "play_line" and item.get("line_type") == "world_response":
            return True
    return False


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


def learner_spoken_phrase(*, learner_line: dict[str, Any], target: dict[str, Any]) -> str:
    for key in ("tts_text", "text", "audio_text"):
        value = learner_line.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    canonical = target.get("canonical")
    if isinstance(canonical, str) and canonical.strip():
        return canonical.strip()
    return ""


def backward_build_audio_relative_path(language: str, target_id: str, build_index: int) -> str:
    return f"audio/generated/{language}/backward-build/{target_id}/build-{build_index}.mp3"


def backward_build_step(
    *,
    card: dict[str, Any],
    target: dict[str, Any],
    learner_line: dict[str, Any],
    learner_frame: dict[str, Any] | None,
    target_text: str,
    target_transliteration: str,
    target_phrase: str,
    target_audio: str | None,
    target_audio_text: str | None,
    language: str,
) -> dict[str, Any]:
    return step(
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
                target_text=target_text,
                target_transliteration=target_transliteration,
                language=language,
                spoken_phrase=learner_spoken_phrase(
                    learner_line=learner_line,
                    target=target,
                ),
            ),
        },
    )


def backward_build_indices(unit_count: int) -> list[int]:
    if unit_count >= 3:
        return list(range(unit_count - 1, -1, -1))
    return [0]


def backward_build_prompts(
    *,
    target: dict[str, Any],
    target_phrase: str,
    target_text: str,
    target_transliteration: str,
    language: str,
    spoken_phrase: str | None = None,
) -> list[dict[str, Any]]:
    units = backward_build_units(target=target, target_phrase=target_phrase)
    spoken = spoken_phrase or target_phrase
    prompts = []
    for index in backward_build_indices(len(units)):
        text = " ".join(units[index:])
        if index == 0:
            text = target_phrase
        spoken_text = backward_build_entry_spoken_text(
            target=target,
            build_index=index,
            units=units,
            spoken_phrase=spoken,
        )
        expected_text = target_text if index == 0 else text
        expected_transliteration = target_transliteration if index == 0 else text
        prompts.append(
            {
                "id": f"{target['id']}-build-{index}",
                "text": text,
                "audioUrl": public_path(
                    backward_build_audio_relative_path(language, target["id"], index)
                ),
                "audioText": spoken_text,
                "mic": recording_mic(expected_text, expected_transliteration),
            }
        )
    return prompts


def backward_build_entry_spoken_text(
    *,
    target: dict[str, Any],
    build_index: int,
    units: list[str],
    spoken_phrase: str,
) -> str:
    explicit_prompts = target.get("backward_build_spoken_prompts")
    if isinstance(explicit_prompts, list) and explicit_prompts:
        prompt_position = (len(units) - 1) - build_index
        if 0 <= prompt_position < len(explicit_prompts):
            spoken = str(explicit_prompts[prompt_position]).strip()
            if spoken:
                return spoken

    spoken_units = backward_build_spoken_units(target=target, spoken_phrase=spoken_phrase)
    if len(spoken_units) == len(units):
        text = " ".join(spoken_units[build_index:])
        if build_index == 0:
            return spoken_phrase
        return text

    text = " ".join(units[build_index:])
    if build_index == 0:
        return spoken_phrase or text
    return text


def backward_build_spoken_units(*, target: dict[str, Any], spoken_phrase: str) -> list[str]:
    explicit_units = target.get("backward_build_spoken_units")
    if isinstance(explicit_units, list):
        units = [str(unit).strip() for unit in explicit_units if str(unit).strip()]
        if units:
            return units

    if isinstance(target.get("backward_build_spoken_prompts"), list):
        return []

    if re.search(r"[\s,，;]", spoken_phrase):
        parts = re.split(r"[\s,，;]+", spoken_phrase.strip())
        units = [
            part.strip(".,!?。！？\"'")
            for part in parts
            if part.strip(".,!?。！？\"'")
        ]
        if units:
            return units

    return backward_build_units(target={}, target_phrase=spoken_phrase)


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
