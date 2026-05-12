import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.conversation.judge import LocalCommunicationJudge
from app.conversation.models import ConversationContext, SpeechInterpretation
from app.conversation.openai_adapter import build_judge_prompt, judgement_from_payload


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


if __name__ == "__main__":
    unittest.main()
