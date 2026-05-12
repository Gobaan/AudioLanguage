from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConversationContext:
    language: str
    scene_id: str = ""
    function_id: str = ""
    target_id: str = ""
    target_text: str = ""
    target_romanized: str = ""
    target_meaning: str = ""
    target_audio: str = ""
    scene_contract: dict[str, Any] | None = None


@dataclass(frozen=True)
class LearnerAttempt:
    audio_path: Path


@dataclass(frozen=True)
class SpeechInterpretation:
    transcript: str
    romanized: str
    score: float
    available: bool
    language_probability: float | None = None
    feedback: str = ""


@dataclass(frozen=True)
class CommunicationJudgement:
    status: str
    close_enough: bool
    confidence: float
    message: str
    partner_response: str = ""
    next_action: str = "retry"
    missing_slots: tuple[str, ...] = ()
    extra_intent: str | None = None


@dataclass(frozen=True)
class CoachResponse:
    transcript: str
    transcript_romanized: str
    communication: CommunicationJudgement
    speech_available: bool
    speech_feedback: str
    language_probability: float | None = None

    @property
    def is_successful(self) -> bool:
        return self.communication.close_enough

    @property
    def score(self) -> float:
        return self.communication.confidence

    def to_dict(self) -> dict:
        return {
            "transcript": self.transcript,
            "transcript_romanized": self.transcript_romanized,
            "communication": {
                "status": self.communication.status,
                "close_enough": self.communication.close_enough,
                "confidence": self.communication.confidence,
                "message": self.communication.message,
                "partner_response": self.communication.partner_response,
                "next_action": self.communication.next_action,
                "missing_slots": list(self.communication.missing_slots),
                "extra_intent": self.communication.extra_intent,
            },
            "speech_available": self.speech_available,
            "speech_feedback": self.speech_feedback,
            "language_probability": self.language_probability,
            "is_successful": self.is_successful,
            "score": self.score,
        }
