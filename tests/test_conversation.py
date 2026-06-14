import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.conversation.judge import LocalCommunicationJudge
from app.conversation.coach import apply_deterministic_pass_guard
from app.conversation.models import CommunicationJudgement, ConversationContext, SpeechInterpretation
from app.conversation.openai_adapter import (
    build_judge_prompt,
    build_transcription_prompt,
    judgement_from_payload,
    learner_facing_transcript,
)


class LocalCommunicationJudgeTests(unittest.TestCase):
    def test_accepts_close_beginner_attempt(self):
        judge = LocalCommunicationJudge()

        result = judge.judge(
            interpretation=SpeechInterpretation(
                transcript="",
                romanized="vanakkam eppadi irukeenga",
                score=0.0,
                available=True,
            ),
            context=ConversationContext(
                language="ta",
                target_romanized="Vanakkam! Eppadi irukkireergal?",
                target_meaning="Hello! How are you?",
            ),
        )

        self.assertTrue(result.close_enough)
        self.assertEqual(result.status, "fits_scene")

    def test_returns_unclear_when_no_speech_was_heard(self):
        judge = LocalCommunicationJudge()

        result = judge.judge(
            interpretation=SpeechInterpretation(
                transcript="",
                romanized="",
                score=0.0,
                available=False,
            ),
            context=ConversationContext(
                language="ta",
                target_romanized="Vanakkam! Eppadi irukkireergal?",
            ),
        )

        self.assertFalse(result.close_enough)
        self.assertEqual(result.status, "unclear")


class DeterministicPassGuardTests(unittest.TestCase):
    def test_overrides_false_judge_when_transcript_matches_target(self):
        guarded = apply_deterministic_pass_guard(
            interpretation=SpeechInterpretation(
                transcript="\u3042\u3093\u306a\u3067\u3059\u3002",
                romanized="annadesu.",
                score=0.941,
                available=True,
            ),
            judgement=CommunicationJudgement(
                status="off_target",
                close_enough=False,
                confidence=0.25,
                message="Not the expected intent.",
            ),
            context=ConversationContext(
                language="ja",
                target_romanized="Anna desu.",
                scene_contract={"partner_role": "classmate"},
            ),
        )

        self.assertTrue(guarded.close_enough)
        self.assertEqual(guarded.status, "exact_line_match")
        self.assertEqual(guarded.next_action, "continue")

    def test_keeps_judge_failure_when_transcript_is_not_close(self):
        judgement = CommunicationJudgement(
            status="off_target",
            close_enough=False,
            confidence=0.25,
            message="Not the expected intent.",
        )

        guarded = apply_deterministic_pass_guard(
            interpretation=SpeechInterpretation(
                transcript="arigatou",
                romanized="arigatou",
                score=0.2,
                available=True,
            ),
            judgement=judgement,
            context=ConversationContext(language="ja", target_romanized="Anna desu."),
        )

        self.assertIs(guarded, judgement)


class OpenAIPromptAdapterTests(unittest.TestCase):
    def test_build_judge_prompt_includes_scene_contract_and_attempt(self):
        prompt = build_judge_prompt(
            interpretation=SpeechInterpretation(
                transcript="Hi, how are you?",
                romanized="Hi, how are you?",
                score=0.0,
                available=True,
            ),
            context=ConversationContext(
                language="en",
                scene_contract={
                    "target_function": {
                        "id": "respond_to_greeting",
                        "definition": "Respond appropriately when someone says hi.",
                    },
                    "required_slots": {"speech_act": "greeting_response"},
                },
            ),
        )

        self.assertIn("respond_to_greeting", prompt)
        self.assertIn("greeting_response", prompt)
        self.assertIn("Hi, how are you?", prompt)
        self.assertIn("Ignore punctuation", prompt)
        self.assertIn("Return only JSON", prompt)

    def test_judgement_from_payload_maps_structured_result(self):
        judgement = judgement_from_payload({
            "heard_as": "Hi",
            "language_detected": "en",
            "intent_match": "exact",
            "fits_scene": True,
            "missing_slots": [],
            "extra_intent": None,
            "learner_feedback": "That worked.",
            "partner_response": "Nice to see you!",
            "next_action": "continue",
        })

        self.assertTrue(judgement.close_enough)
        self.assertEqual(judgement.status, "exact")
        self.assertEqual(judgement.partner_response, "Nice to see you!")
        self.assertEqual(judgement.next_action, "continue")

    def test_build_transcription_prompt_includes_expected_language_context(self):
        prompt = build_transcription_prompt(
            ConversationContext(
                language="ja",
                target_text="\u3053\u3093\u306b\u3061\u306f\uff01",
                target_romanized="Konnichiwa!",
                target_meaning="Respond to a greeting.",
            )
        )

        self.assertIn("Japanese", prompt)
        self.assertIn("Konnichiwa", prompt)
        self.assertIn("unrelated scripts", prompt)

    def test_learner_facing_transcript_hides_unrelated_script(self):
        transcript = "\u05e1\u05de\u05d9\u05dd \u05d0\u05e1\u05df \u05d5\u05db\u05e8\u05d9\u05dd \u05d0\u05e1\u05df"
        display = learner_facing_transcript(
            transcript,
            ConversationContext(language="ja", target_romanized="Konnichiwa!"),
        )

        self.assertEqual(display, "unclear Japanese attempt")

    def test_learner_facing_transcript_prefers_romanized_chinese(self):
        display = learner_facing_transcript(
            "\u6211\u4e0d\u61c2\u3002",
            ConversationContext(language="zh", target_romanized="Wo bu dong."),
        )

        self.assertEqual(display, "Wo bu dong.")


if __name__ == "__main__":
    unittest.main()
