from dataclasses import dataclass, field

from app.conversation.judge import LocalCommunicationJudge
from app.conversation.models import (
    CoachResponse,
    CommunicationJudgement,
    ConversationContext,
    LearnerAttempt,
    SpeechInterpretation,
)
from app.conversation.speech import SpeechInterpreter


DETERMINISTIC_PASS_THRESHOLD = 0.8


@dataclass(frozen=True)
class ConversationCoach:
    """Runtime facade for one learner utterance inside one guided scene."""

    speech_interpreter: SpeechInterpreter = field(default_factory=SpeechInterpreter)
    communication_judge: LocalCommunicationJudge = field(default_factory=LocalCommunicationJudge)

    def evaluate_attempt(
        self,
        *,
        attempt: LearnerAttempt,
        context: ConversationContext,
    ) -> CoachResponse:
        interpretation = self.speech_interpreter.interpret(attempt, context)
        judgement = self.communication_judge.judge(
            interpretation=interpretation,
            context=context,
        )
        judgement = apply_deterministic_pass_guard(
            interpretation=interpretation,
            judgement=judgement,
            context=context,
        )
        return CoachResponse(
            transcript=interpretation.transcript,
            transcript_romanized=interpretation.romanized,
            communication=judgement,
            speech_available=interpretation.available,
            speech_feedback=interpretation.feedback,
            language_probability=interpretation.language_probability,
        )


def apply_deterministic_pass_guard(
    *,
    interpretation: SpeechInterpretation,
    judgement: CommunicationJudgement,
    context: ConversationContext,
) -> CommunicationJudgement:
    """Prevent an AI judge miss when speech clearly matches the target line."""
    if judgement.close_enough:
        return judgement

    if not interpretation.available or interpretation.score < DETERMINISTIC_PASS_THRESHOLD:
        return judgement

    return CommunicationJudgement(
        status="exact_line_match",
        close_enough=True,
        confidence=round(interpretation.score, 3),
        message="The spoken line matches the target phrase closely enough.",
        partner_response=judgement.partner_response or default_partner_response(context),
        next_action="continue",
    )


def default_partner_response(context: ConversationContext) -> str:
    if context.scene_contract and context.scene_contract.get("partner_role"):
        return "That worked."
    return ""
