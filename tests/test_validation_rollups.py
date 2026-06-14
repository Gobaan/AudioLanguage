import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.validation.rollups import filter_scorecard_attempts, learner_audio_for_attempts, learner_line_for_attempts


class ScorecardRollupTests(unittest.TestCase):
    def test_scorecard_keeps_only_final_backward_build_attempt(self):
        attempts = filter_scorecard_attempts(
            [
                {
                    "attemptId": "chunk-1",
                    "lessonId": "en-card-introduce-self-dialogue-practice",
                    "stepId": "backward_build",
                    "targetId": "en-target-my-name-is",
                    "buildPromptText": "Anna.",
                    "receivedAt": "2026-06-13T10:00:00Z",
                },
                {
                    "attemptId": "final-1",
                    "lessonId": "en-card-introduce-self-dialogue-practice",
                    "stepId": "backward_build",
                    "targetId": "en-target-my-name-is",
                    "expectedText": "I'm Anna.",
                    "receivedAt": "2026-06-13T10:01:00Z",
                },
                {
                    "attemptId": "recall-1",
                    "lessonId": "en-card-introduce-class-transfer-same_day_transfer",
                    "stepId": "scene_recall",
                    "targetId": "en-target-my-name-is",
                    "receivedAt": "2026-06-13T10:02:00Z",
                },
            ]
        )

        self.assertEqual([attempt["attemptId"] for attempt in attempts], ["final-1", "recall-1"])

    def test_learner_line_for_attempts_uses_full_phrase(self):
        learner_line = learner_line_for_attempts(
            [
                {"expectedTransliteration": "dong", "expectedText": "dong"},
                {"expectedTransliteration": "Wo bu dong.", "expectedText": "我不懂。"},
            ]
        )

        self.assertEqual(learner_line, "Wo bu dong.")

    def test_learner_audio_for_attempts_prefers_full_phrase(self):
        learner_audio = learner_audio_for_attempts(
            [
                {
                    "expectedTransliteration": "dong",
                    "targetAudioUrl": "/audio/generated/zh/backward-build/chunk.mp3",
                },
                {
                    "expectedTransliteration": "Wo bu dong.",
                    "targetAudioUrl": "/audio/generated/zh/dialogue/line-1.mp3",
                },
            ]
        )

        self.assertEqual(learner_audio, "/audio/generated/zh/dialogue/line-1.mp3")

    def test_learner_audio_for_attempts_prefers_dialogue_over_backward_build(self):
        learner_audio = learner_audio_for_attempts(
            [
                {
                    "expectedTransliteration": "Wo bu dong.",
                    "targetAudioUrl": "/audio/generated/zh/backward-build/zh-target-i-dont-understand/build-3.mp3",
                },
                {
                    "expectedTransliteration": "Wo bu dong.",
                    "targetAudioUrl": "/audio/generated/zh/repair-dont-understand/line-1.mp3",
                },
            ]
        )

        self.assertEqual(learner_audio, "/audio/generated/zh/repair-dont-understand/line-1.mp3")


if __name__ == "__main__":
    unittest.main()
