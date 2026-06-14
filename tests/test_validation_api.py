import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.conversation.models import CoachResponse, CommunicationJudgement, ConversationContext
from app.deps import get_conversation_coach
from app.validation import ValidationStore
from app.validation.scoring import attempt_expected_phrase
from test_support import app


class FakeConversationCoach:
    def evaluate_attempt(self, *, attempt, context):
        return CoachResponse(
            transcript="こんにちは",
            transcript_romanized=context.target_romanized,
            communication=CommunicationJudgement(
                status="exact",
                close_enough=True,
                confidence=0.98,
                message="Understood.",
                next_action="continue",
            ),
            speech_available=True,
            speech_feedback="",
        )


class CapturingConversationCoach(FakeConversationCoach):
    last_context: ConversationContext | None = None

    def evaluate_attempt(self, *, attempt, context):
        CapturingConversationCoach.last_context = context
        return super().evaluate_attempt(attempt=attempt, context=context)


@contextmanager
def fake_conversation_coach():
    app.dependency_overrides[get_conversation_coach] = lambda: FakeConversationCoach()
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_conversation_coach, None)


class ValidationApiTests(unittest.TestCase):
    def test_validation_session_saves_events_and_attempts_locally(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.validation.validation_store", store), fake_conversation_coach():
                client = TestClient(app)
                session_response = client.post(
                    "/api/validation/sessions",
                    json={
                        "sessionId": "test-session",
                        "participantId": "local-test",
                        "language": "ja",
                        "sceneSet": "mvp",
                        "lessonPage": "hello",
                    },
                )
                event_response = client.post(
                    "/api/validation/sessions/test-session/events",
                    json={
                        "type": "choice_selected",
                        "targetId": "ja-target-respond-hi",
                        "lessonId": "ja-card-first-hi-dialogue-practice",
                        "stepId": "broad_meaning_guess",
                        "choiceId": "respond_to_greeting",
                        "isCorrect": True,
                    },
                )
                attempt_response = client.post(
                    "/api/validation/sessions/test-session/attempts",
                    data={
                        "metadata": (
                            '{"attemptId":"attempt-1","lessonId":"ja-card-first-hi-dialogue-practice",'
                            '"stepId":"repeat_with_mic","targetId":"ja-target-respond-hi",'
                            '"expectedText":"こんにちは！","expectedTransliteration":"Konnichiwa!",'
                            '"targetAudioUrl":"/audio/generated/ja/first-hi-response/line-1.mp3"}'
                        )
                    },
                    files={"file": ("attempt.webm", b"audio-bytes", "audio/webm")},
                )
                duplicate_response = client.post(
                    "/api/validation/sessions/test-session/attempts",
                    data={
                        "metadata": (
                            '{"attemptId":"attempt-1","lessonId":"ja-card-first-hi-dialogue-practice",'
                            '"stepId":"repeat_with_mic","targetId":"ja-target-respond-hi"}'
                        )
                    },
                    files={"file": ("attempt.webm", b"duplicate-audio", "audio/webm")},
                )
                audio_response = client.get("/api/validation/sessions/test-session/attempts/attempt-1/audio")
                scorecard_response = client.get("/api/validation/sessions/test-session/scorecard?score=true")
                admin_response = client.get("/api/validation/admin/summary")

        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(event_response.status_code, 200)
        self.assertEqual(attempt_response.status_code, 200)
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(audio_response.status_code, 200)
        self.assertEqual(audio_response.content, b"audio-bytes")
        self.assertEqual(attempt_response.json()["recordingPath"], duplicate_response.json()["recordingPath"])
        scorecard = scorecard_response.json()
        self.assertEqual(scorecard["eventCount"], 1)
        self.assertEqual(scorecard["attemptCount"], 1)
        self.assertEqual(scorecard["targets"][0]["targetId"], "ja-target-respond-hi")
        self.assertEqual(scorecard["targets"][0]["targetAudioUrl"], "/audio/generated/ja/first-hi-response/line-1.mp3")
        self.assertEqual(scorecard["targets"][0]["attempts"][0]["aiScore"]["status"], "scored")
        self.assertEqual(scorecard["targets"][0]["attempts"][0]["aiScore"]["result"]["communication"]["status"], "exact")
        admin_target_sessions = admin_response.json()["targets"][0]["sessions"]
        self.assertTrue(any(item["type"] == "choice" and item["choiceCorrect"] for item in admin_target_sessions))
        self.assertTrue(any(item["type"] == "recording" for item in admin_target_sessions))

    def test_validation_admin_summary_groups_attempts_by_language_and_scene_set(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.validation.validation_store", store):
                client = TestClient(app)
                client.post(
                    "/api/validation/sessions",
                    json={
                        "sessionId": "day-1",
                        "participantId": "friend-a",
                        "language": "ja",
                        "sceneSet": "mvp",
                        "lessonPage": "hello",
                    },
                )
                client.post(
                    "/api/validation/sessions/day-1/attempts",
                    data={
                        "metadata": (
                            '{"attemptId":"attempt-1","language":"ja","sceneSet":"mvp",'
                            '"lessonPage":"hello","lessonId":"ja-card-first-hi-dialogue-practice",'
                            '"stepId":"repeat_with_mic","targetId":"ja-target-respond-hi",'
                            '"expectedText":"こんにちは！","expectedTransliteration":"Konnichiwa!"}'
                        )
                    },
                    files={"file": ("attempt.webm", b"audio-bytes", "audio/webm")},
                )
                store.save_score(
                    "day-1",
                    "attempt-1",
                    {
                        "status": "scored",
                        "result": {
                            "communication": {
                                "status": "exact",
                                "close_enough": True,
                                "confidence": 0.96,
                            }
                        },
                    },
                )

                response = client.get("/api/validation/admin/summary")
                name_response = client.get("/api/validation/participant-name")
                delete_response = client.delete("/api/validation/sessions/day-1")
                deleted_summary_response = client.get("/api/validation/admin/summary")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["sessionCount"], 1)
        self.assertEqual(payload["attemptCount"], 1)
        self.assertEqual(payload["rememberedAttemptCount"], 1)
        self.assertEqual(payload["sessions"][0]["language"], "ja")
        self.assertEqual(payload["sessions"][0]["sceneSet"], "mvp")
        self.assertEqual(payload["targets"][0]["language"], "ja")
        self.assertEqual(payload["targets"][0]["sceneSet"], "mvp")
        self.assertEqual(payload["targets"][0]["targetId"], "ja-target-respond-hi")
        self.assertIs(payload["targets"][0]["sessions"][0]["scorePassed"], True)
        self.assertEqual(name_response.status_code, 200)
        self.assertNotEqual(name_response.json()["participantId"], "friend-a")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["status"], "deleted")
        self.assertEqual(deleted_summary_response.json()["sessionCount"], 0)

    def test_validation_admin_can_delete_selected_session_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.validation.validation_store", store):
                client = TestClient(app)
                client.post(
                    "/api/validation/sessions",
                    json={
                        "sessionId": "delete-me",
                        "participantId": "Bob",
                        "language": "ja",
                        "sceneSet": "mvp",
                    },
                )
                client.post(
                    "/api/validation/sessions/delete-me/attempts",
                    data={
                        "metadata": (
                            '{"attemptId":"attempt-1","language":"ja","sceneSet":"mvp",'
                            '"lessonId":"lesson","stepId":"repeat_with_mic","targetId":"target"}'
                        )
                    },
                    files={"file": ("attempt.webm", b"audio-bytes", "audio/webm")},
                )
                store.save_score(
                    "delete-me",
                    "attempt-1",
                    {
                        "status": "scored",
                        "result": {
                            "communication": {
                                "status": "exact",
                                "close_enough": True,
                                "confidence": 0.96,
                            }
                        },
                    },
                )

                delete_response = client.delete("/api/validation/sessions/delete-me/data?kind=recordings&kind=scores")
                summary_response = client.get("/api/validation/admin/summary")
                audio_response = client.get("/api/validation/sessions/delete-me/attempts/attempt-1/audio")

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["deleted"], ["recordings", "scores"])
        self.assertEqual(summary_response.json()["sessionCount"], 1)
        self.assertEqual(summary_response.json()["scoredAttemptCount"], 0)
        self.assertEqual(audio_response.status_code, 404)

    def test_validation_admin_can_delete_one_attempt_or_entire_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.validation.validation_store", store):
                client = TestClient(app)
                for session_id, participant_id in [("bob-day-1", "Bob"), ("maya-day-1", "Maya")]:
                    client.post(
                        "/api/validation/sessions",
                        json={
                            "sessionId": session_id,
                            "participantId": participant_id,
                            "language": "ja",
                            "sceneSet": "mvp",
                        },
                    )
                    client.post(
                        f"/api/validation/sessions/{session_id}/attempts",
                        data={
                            "metadata": (
                                f'{{"attemptId":"attempt-1","language":"ja","sceneSet":"mvp",'
                                f'"lessonId":"lesson","stepId":"repeat_with_mic","targetId":"target-{participant_id}"}}'
                            )
                        },
                        files={"file": ("attempt.webm", b"audio-bytes", "audio/webm")},
                    )

                delete_attempt_response = client.delete("/api/validation/sessions/bob-day-1/attempts/attempt-1")
                bob_audio_response = client.get("/api/validation/sessions/bob-day-1/attempts/attempt-1/audio")
                after_attempt_delete_response = client.get("/api/validation/admin/summary")
                delete_user_response = client.delete("/api/validation/users/Maya")
                after_user_delete_response = client.get("/api/validation/admin/summary")

        self.assertEqual(delete_attempt_response.status_code, 200)
        self.assertEqual(bob_audio_response.status_code, 404)
        self.assertEqual(after_attempt_delete_response.json()["sessionCount"], 2)
        self.assertEqual(after_attempt_delete_response.json()["attemptCount"], 1)
        self.assertEqual(delete_user_response.status_code, 200)
        self.assertEqual(delete_user_response.json()["deletedSessionCount"], 1)
        self.assertEqual(after_user_delete_response.json()["sessionCount"], 1)
        self.assertEqual(after_user_delete_response.json()["attemptCount"], 0)

    def test_validation_admin_can_score_one_skipped_attempt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.validation.validation_store", store), fake_conversation_coach():
                client = TestClient(app)
                client.post(
                    "/api/validation/sessions",
                    json={
                        "sessionId": "needs-score",
                        "participantId": "Bob",
                        "language": "ja",
                        "sceneSet": "mvp",
                    },
                )
                client.post(
                    "/api/validation/sessions/needs-score/attempts",
                    data={
                        "metadata": (
                            '{"attemptId":"attempt-1","language":"ja","sceneSet":"mvp",'
                            '"lessonId":"lesson","stepId":"repeat_with_mic","targetId":"target",'
                            '"expectedText":"こんにちは！","expectedTransliteration":"Konnichiwa!"}'
                        )
                    },
                    files={"file": ("attempt.webm", b"audio-bytes", "audio/webm")},
                )

                score_response = client.post("/api/validation/sessions/needs-score/attempts/attempt-1/score")
                summary_response = client.get("/api/validation/admin/summary")

        self.assertEqual(score_response.status_code, 200)
        self.assertEqual(score_response.json()["status"], "scored")
        self.assertEqual(summary_response.json()["scoredAttemptCount"], 1)
        self.assertEqual(summary_response.json()["targets"][0]["sessions"][0]["scoreStatus"], "exact")

    def test_validation_scorecard_ignores_malformed_jsonl_event_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.validation.validation_store", store):
                client = TestClient(app)
                client.post(
                    "/api/validation/sessions",
                    json={
                        "sessionId": "corrupt-events",
                        "participantId": "Bob",
                        "language": "ja",
                        "sceneSet": "mvp",
                    },
                )
                events_path = Path(temp_dir) / "sessions" / "corrupt-events" / "events.jsonl"
                events_path.write_text('{"type":"choice_selected","targetId":"target","isCorrect":true}\nnot-json\n')

                response = client.get("/api/validation/sessions/corrupt-events/scorecard")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["eventCount"], 1)

    def test_attempt_expected_phrase_prefers_backward_build_prompt_text(self):
        expected_text, expected_transliteration = attempt_expected_phrase(
            {
                "expectedText": "My name is Anna.",
                "expectedTransliteration": "My name is Anna.",
                "buildPromptText": "Anna.",
            }
        )

        self.assertEqual(expected_text, "Anna.")
        self.assertEqual(expected_transliteration, "Anna.")

    def test_backward_build_scoring_uses_build_prompt_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            CapturingConversationCoach.last_context = None
            with patch("app.routes.validation.validation_store", store):
                app.dependency_overrides[get_conversation_coach] = lambda: CapturingConversationCoach()
                try:
                    client = TestClient(app)
                    client.post(
                        "/api/validation/sessions",
                        json={
                            "sessionId": "backward-build",
                            "participantId": "Bob",
                            "language": "en",
                            "sceneSet": "mvp",
                        },
                    )
                    client.post(
                        "/api/validation/sessions/backward-build/attempts",
                        data={
                            "metadata": (
                                '{"attemptId":"build-attempt-1","language":"en","sceneSet":"mvp",'
                                '"lessonId":"en-card-introduce-self-dialogue-practice","stepId":"backward_build",'
                                '"targetId":"en-target-my-name-is","expectedText":"My name is Anna.",'
                                '"expectedTransliteration":"My name is Anna.",'
                                '"buildPromptText":"Anna.",'
                                '"targetAudioUrl":"/audio/generated/en/backward-build/en-target-my-name-is/build-3.mp3"}'
                            )
                        },
                        files={"file": ("attempt.webm", b"audio-bytes", "audio/webm")},
                    )
                    score_response = client.post(
                        "/api/validation/sessions/backward-build/attempts/build-attempt-1/score"
                    )
                finally:
                    app.dependency_overrides.pop(get_conversation_coach, None)

        self.assertEqual(score_response.status_code, 200)
        self.assertIsNotNone(CapturingConversationCoach.last_context)
        self.assertEqual(CapturingConversationCoach.last_context.target_text, "Anna.")
        self.assertEqual(CapturingConversationCoach.last_context.target_romanized, "Anna.")
        self.assertEqual(
            CapturingConversationCoach.last_context.target_audio,
            "/audio/generated/en/backward-build/en-target-my-name-is/build-3.mp3",
        )


if __name__ == "__main__":
    unittest.main()
