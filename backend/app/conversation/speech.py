from app.conversation.models import ConversationContext, LearnerAttempt, SpeechInterpretation
from app.speech.language import phonetic_for_language
from app.speech.transcription import transcribe_speech


class SpeechInterpreter:
    """Transcribe learner audio into a readable target-language approximation."""

    def interpret(self, attempt: LearnerAttempt, context: ConversationContext) -> SpeechInterpretation:
        expected_romanized = context.target_romanized or phonetic_for_language(
            context.target_text,
            context.language,
        )
        details = transcribe_speech(
            attempt.audio_path,
            language=context.language,
            expected_romanized=expected_romanized,
        )
        return SpeechInterpretation(
            transcript=details["transcript"],
            romanized=details["romanized"],
            score=details["score"] if details["available"] else 0.0,
            available=details["available"],
            language_probability=details["language_probability"],
            feedback=details["feedback"],
        )
