from dataclasses import dataclass, field

from app.conversation.judge import LocalCommunicationJudge
from app.conversation.models import CoachResponse, ConversationContext, LearnerAttempt
from app.conversation.speech import SpeechInterpreter


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
        return CoachResponse(
            transcript=interpretation.transcript,
            transcript_romanized=interpretation.romanized,
            communication=judgement,
            speech_available=interpretation.available,
            speech_feedback=interpretation.feedback,
            language_probability=interpretation.language_probability,
        )
