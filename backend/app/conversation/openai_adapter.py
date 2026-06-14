from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any

from app.conversation.models import (
    CommunicationJudgement,
    ConversationContext,
    LearnerAttempt,
    SpeechInterpretation,
)
from app.speech.display import learner_facing_transcript as romanized_learner_transcript
from app.speech.similarity import normalize_for_match, text_similarity


TRANSCRIBE_MODEL_ENV = "AUDIO_LANGUAGE_TRANSCRIBE_MODEL"
JUDGE_MODEL_ENV = "AUDIO_LANGUAGE_JUDGE_MODEL"

DEFAULT_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_JUDGE_MODEL = "gpt-5-nano"


class OpenAIUnavailable(RuntimeError):
    """Raised when the OpenAI adapter is configured but cannot run."""


@dataclass(frozen=True)
class OpenAISpeechInterpreter:
    """Transcribe learner audio with OpenAI's speech-to-text endpoint."""

    model: str = DEFAULT_TRANSCRIBE_MODEL

    def interpret(self, attempt: LearnerAttempt, context: ConversationContext) -> SpeechInterpretation:
        client = build_openai_client()
        with attempt.audio_path.open("rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=os.environ.get(TRANSCRIBE_MODEL_ENV, self.model),
                file=audio_file,
                language=context.language or None,
                prompt=build_transcription_prompt(context),
            )

        transcript = str(getattr(transcription, "text", "") or "").strip()
        romanized = romanized_learner_transcript(
            transcript,
            language=context.language or "",
            target_romanized=context.target_romanized or context.target_text,
            language_label=language_display_name(context.language),
        )
        expected = context.target_romanized or context.target_text
        score = text_similarity(normalize_for_match(romanized), normalize_for_match(expected))
        return SpeechInterpretation(
            transcript=transcript,
            romanized=romanized,
            score=round(score, 3),
            available=bool(transcript),
            feedback="",
        )


@dataclass(frozen=True)
class OpenAICommunicationJudge:
    """Judge one learner utterance against a structured scene contract."""

    model: str = DEFAULT_JUDGE_MODEL

    def judge(
        self,
        *,
        interpretation: SpeechInterpretation,
        context: ConversationContext,
    ) -> CommunicationJudgement:
        if not interpretation.romanized and not interpretation.transcript:
            return CommunicationJudgement(
                status="unclear",
                close_enough=False,
                confidence=0.0,
                message="I could not hear a clear response. Try again.",
                next_action="retry",
            )

        client = build_openai_client()
        response = client.responses.create(
            model=os.environ.get(JUDGE_MODEL_ENV, self.model),
            input=build_judge_prompt(interpretation=interpretation, context=context),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "conversation_judgement",
                    "schema": JUDGE_OUTPUT_SCHEMA,
                    "strict": True,
                }
            },
        )
        payload = parse_response_json(response)
        return judgement_from_payload(payload)


def build_openai_client():
    if not os.environ.get("OPENAI_API_KEY"):
        raise OpenAIUnavailable("OPENAI_API_KEY is not set.")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise OpenAIUnavailable("Install the openai package to enable the AI judge.") from error

    return OpenAI()


def build_transcription_prompt(context: ConversationContext) -> str:
    expected_values = [
        value
        for value in [context.target_text, context.target_romanized, context.target_meaning]
        if value
    ]
    expected_hint = "; ".join(expected_values) or "the learner's short response"
    language_name = language_display_name(context.language)
    if context.language in {"zh", "yue"}:
        return (
            f"The learner is practicing {language_name} using beginner romanization. "
            f"They are attempting this short guided-scene response: {expected_hint}. "
            "Return Latin letters only, using pinyin-style romanization with spaces between syllables. "
            "Do not use Chinese characters."
        )
    return (
        f"The learner is practicing {language_name}. "
        f"They are attempting this short guided-scene response: {expected_hint}. "
        "Prefer the practiced language over unrelated scripts when the audio is uncertain. "
        "If the learner approximates the phrase with an accent, transcribe the closest intended phrase."
    )


def learner_facing_transcript(transcript: str, context: ConversationContext) -> str:
    return romanized_learner_transcript(
        transcript,
        language=context.language or "",
        target_romanized=context.target_romanized or context.target_text,
        language_label=language_display_name(context.language),
    )


def language_display_name(language: str) -> str:
    return {
        "en": "English",
        "ja": "Japanese",
        "zh": "Mandarin Chinese",
        "yue": "Cantonese",
        "ta": "Tamil",
    }.get(language, language or "target language")


def build_judge_prompt(
    *,
    interpretation: SpeechInterpretation,
    context: ConversationContext,
) -> str:
    scene_contract = context.scene_contract or fallback_scene_contract(context)
    learner_attempt = {
        "heard_as": interpretation.transcript,
        "heard_as_romanized": interpretation.romanized,
        "language_probability": interpretation.language_probability,
    }

    return (
        "You are a language-learning conversation judge for one guided scene.\n"
        "Your job is to decide whether the learner's attempt satisfies the scene's target intention.\n"
        "Be generous for beginner utterances that accomplish the communicative job.\n"
        "Ignore punctuation, capitalization, and uncertain transcription punctuation when judging intent.\n"
        "Do not invent a new lesson, change the scene, or continue a free conversation.\n"
        "Judge only the current learner turn.\n"
        "If the attempt fits the scene, include a short in-character partner_response.\n"
        "If the learner says a valid sentence that does not satisfy the required slots, mark it off_target.\n\n"
        f"Scene contract:\n{json.dumps(scene_contract, ensure_ascii=False, indent=2)}\n\n"
        f"Learner attempt:\n{json.dumps(learner_attempt, ensure_ascii=False, indent=2)}\n\n"
        "Return only JSON matching the provided schema."
    )


def fallback_scene_contract(context: ConversationContext) -> dict[str, Any]:
    return {
        "language_being_practiced": context.language,
        "scene_id": context.scene_id,
        "target_function": {
            "id": context.function_id,
            "definition": context.target_meaning or context.target_text,
        },
        "learner_intention": context.target_meaning or context.target_text,
        "required_slots": {
            "meaning": context.target_meaning or context.target_text,
        },
        "example_valid_responses": [
            value for value in [context.target_text, context.target_romanized] if value
        ],
    }


def parse_response_json(response: Any) -> dict[str, Any]:
    output_text = getattr(response, "output_text", None)
    if not output_text:
        output_text = response.output[0].content[0].text
    return json.loads(output_text)


def judgement_from_payload(payload: dict[str, Any]) -> CommunicationJudgement:
    intent_match = str(payload.get("intent_match", "unclear"))
    fits_scene = bool(payload.get("fits_scene", False))
    confidence = confidence_for(intent_match, fits_scene)
    missing_slots = tuple(str(slot) for slot in payload.get("missing_slots", []))
    close_enough = fits_scene and intent_match in {"exact", "close"}
    partner_response = str(payload.get("partner_response", ""))
    if close_enough and not partner_response:
        partner_response = "Nice to see you."
    return CommunicationJudgement(
        status=intent_match,
        close_enough=close_enough,
        confidence=confidence,
        message=str(payload.get("learner_feedback", "")),
        partner_response=partner_response,
        next_action=str(payload.get("next_action", "retry")),
        missing_slots=missing_slots,
        extra_intent=payload.get("extra_intent"),
    )


def confidence_for(intent_match: str, fits_scene: bool) -> float:
    if intent_match == "exact" and fits_scene:
        return 0.98
    if intent_match == "close" and fits_scene:
        return 0.82
    if intent_match == "off_target":
        return 0.25
    return 0.0


JUDGE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "heard_as": {"type": "string"},
        "language_detected": {"type": ["string", "null"]},
        "intent_match": {
            "type": "string",
            "enum": ["exact", "close", "off_target", "unclear"],
        },
        "fits_scene": {"type": "boolean"},
        "missing_slots": {
            "type": "array",
            "items": {"type": "string"},
        },
        "extra_intent": {"type": ["string", "null"]},
        "learner_feedback": {"type": "string"},
        "partner_response": {"type": "string"},
        "next_action": {
            "type": "string",
            "enum": ["continue", "retry", "show_hint"],
        },
    },
    "required": [
        "heard_as",
        "language_detected",
        "intent_match",
        "fits_scene",
        "missing_slots",
        "extra_intent",
        "learner_feedback",
        "partner_response",
        "next_action",
    ],
}
