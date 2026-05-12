from app.conversation.models import CommunicationJudgement, ConversationContext, SpeechInterpretation
from app.speech.similarity import normalize_for_match, text_similarity


CLOSE_ENOUGH_THRESHOLD = 0.45
PARTIAL_THRESHOLD = 0.25


class LocalCommunicationJudge:
    """Beginner-friendly placeholder for a future AI context judge."""

    def judge(
        self,
        *,
        interpretation: SpeechInterpretation,
        context: ConversationContext,
    ) -> CommunicationJudgement:
        heard = normalize_for_match(interpretation.romanized)
        expected = normalize_for_match(context.target_romanized or context.target_text)

        if not heard:
            return CommunicationJudgement(
                status="unclear",
                close_enough=False,
                confidence=0.0,
                message="I could not hear a clear line. Try the whole line once more.",
                next_action="retry",
            )

        score = text_similarity(heard, expected)
        if score >= CLOSE_ENOUGH_THRESHOLD:
            meaning = f" for '{context.target_meaning}'" if context.target_meaning else ""
            return CommunicationJudgement(
                status="fits_scene",
                close_enough=True,
                confidence=round(score, 3),
                message=f"Close enough{meaning}. A person would likely understand the intention.",
                partner_response="That worked.",
                next_action="continue",
            )

        if score >= PARTIAL_THRESHOLD:
            return CommunicationJudgement(
                status="partly_heard",
                close_enough=False,
                confidence=round(score, 3),
                message="I heard part of the line, but it may not be clear enough for this scene yet.",
                next_action="retry",
            )

        return CommunicationJudgement(
            status="wrong_or_unclear",
            close_enough=False,
            confidence=round(score, 3),
            message="I heard a different line or could not connect it to this scene.",
            next_action="retry",
        )
