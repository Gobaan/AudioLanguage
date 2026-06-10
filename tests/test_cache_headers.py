import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.conversation.models import CoachResponse, CommunicationJudgement
from app.validation import ValidationStore


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


class BrowserCacheHeaderTests(unittest.TestCase):
    def test_index_disables_browser_cache(self):
        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertEqual(response.headers["pragma"], "no-cache")
        self.assertEqual(response.headers["expires"], "0")

    def test_static_assets_disable_browser_cache(self):
        css_asset = next((PROJECT_DIR / "view" / "static" / "assets").glob("*.css"))
        response = TestClient(app).get(f"/static/assets/{css_asset.name}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers["cache-control"])

    def test_language_selection_routes_and_new_languages_load(self):
        client = TestClient(app)

        languages_response = client.get("/languages")
        learn_response = client.get("/learn?language=yue&lesson=hello")
        api_languages_response = client.get("/api/languages")
        cantonese_response = client.get("/api/languages/yue/lessons?lesson=hello")
        tamil_response = client.get("/api/languages/ta/lessons?lesson=hello")

        self.assertEqual(languages_response.status_code, 200)
        self.assertEqual(learn_response.status_code, 200)
        self.assertEqual(api_languages_response.status_code, 200)
        self.assertIn({"id": "yue", "display_name": "Cantonese"}, api_languages_response.json())
        self.assertIn({"id": "ta", "display_name": "Tamil"}, api_languages_response.json())
        self.assertEqual(cantonese_response.status_code, 200)
        self.assertEqual(cantonese_response.json()["lessons"][0]["language"], "yue")
        self.assertEqual(tamil_response.status_code, 200)
        self.assertEqual(tamil_response.json()["lessons"][0]["language"], "ta")

    def test_lessons_endpoint_returns_frontend_renderable_lessons(self):
        response = TestClient(app).get("/api/languages/ja/lessons")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_lesson = payload["lessons"][0]
        step_types = [step["type"] for step in first_lesson["steps"]]
        meaning_step = next(step for step in first_lesson["steps"] if step["type"] == "broad_meaning_guess")

        self.assertEqual(payload["language"], "ja")
        tab_ids = [tab["id"] for tab in payload["lesson_tabs"]]
        tab_labels = [tab["label"] for tab in payload["lesson_tabs"]]
        self.assertEqual(
            tab_ids[:5],
            [
                "hello",
                "introduce",
                "repair",
                "excuse-me",
                "food-order",
            ],
        )
        self.assertEqual(
            set(tab_ids[5:]),
            {
                "hello-transfer",
                "introduce-transfer",
                "repair-transfer",
                "excuse-me-transfer",
                "food-order-transfer",
            },
        )
        self.assertEqual(tab_labels[:5], [f"Scene {index}" for index in range(1, 6)])
        self.assertEqual(set(tab_labels[5:]), {f"Scene {index}" for index in range(6, 11)})
        self.assertEqual(first_lesson["player_component"], "TravellerLessonPlayer")
        self.assertTrue(first_lesson["frames"][0]["imageUrl"].startswith("/visuals/"))
        self.assertIn("scene_setup", step_types)
        self.assertIn("target_audio", step_types)
        self.assertIn("repeat_with_mic", step_types)
        self.assertNotIn("scene_recall", step_types)
        self.assertNotIn("scorecard", step_types)
        self.assertNotIn("schedule_review", step_types)
        self.assertGreaterEqual(len(meaning_step["props"]["choices"]), 2)
        self.assertFalse(
            any(choice["label"].startswith("The learner says") for choice in meaning_step["props"]["choices"])
        )

    def test_lessons_endpoint_can_return_named_preview_lesson(self):
        response = TestClient(app).get("/api/languages/en/lessons?lesson=hospital")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        lessons = payload["lessons"]
        step_types = [step["type"] for step in lessons[0]["steps"]]

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["id"], "en-card-hospital-directions-dialogue-practice")
        self.assertEqual(lessons[0]["target"]["text"], "Where is the hospital?")
        self.assertIn("backward_build", step_types)
        tab_ids = [tab["id"] for tab in payload["lesson_tabs"]]
        tab_labels = [tab["label"] for tab in payload["lesson_tabs"]]
        self.assertEqual(
            tab_ids[:5],
            ["hello", "introduce", "repair", "food-order", "hospital"],
        )
        self.assertEqual(
            set(tab_ids[5:]),
            {
                "hello-transfer",
                "introduce-transfer",
                "repair-transfer",
                "food-order-transfer",
            },
        )
        self.assertEqual(tab_labels[:5], [f"Scene {index}" for index in range(1, 6)])
        self.assertEqual(set(tab_labels[5:]), {f"Scene {index}" for index in range(6, 10)})

    def test_lessons_endpoint_supports_all_mvp_lesson_aliases(self):
        aliases = {
            "hello": "en-card-first-hi-dialogue-practice",
            "introduce": "en-card-introduce-self-dialogue-practice",
            "repair": "en-card-dont-understand-dialogue-practice",
            "food-order": "en-card-order-food-dialogue-practice",
            "hospital": "en-card-hospital-directions-dialogue-practice",
        }

        for alias, lesson_id in aliases.items():
            with self.subTest(alias=alias):
                response = TestClient(app).get(f"/api/languages/en/lessons?lesson={alias}")

                self.assertEqual(response.status_code, 200)
                lessons = response.json()["lessons"]
                self.assertEqual(len(lessons), 1)
                self.assertEqual(lessons[0]["id"], lesson_id)

    def test_lessons_endpoint_supports_japanese_lesson_aliases(self):
        aliases = {
            "hello": "ja-card-first-hi-dialogue-practice",
            "introduce": "ja-card-introduce-self-dialogue-practice",
            "repair": "ja-card-dont-understand-dialogue-practice",
            "excuse-me": "ja-card-excuse-me-dialogue-practice",
            "food-order": "ja-card-order-food-dialogue-practice",
            "hello-transfer": "ja-card-greeting-neighbor-transfer-same_day_transfer",
            "introduce-transfer": "ja-card-introduce-class-transfer-same_day_transfer",
            "repair-transfer": "ja-card-repair-ticket-transfer-same_day_transfer",
            "excuse-me-transfer": "ja-card-excuse-me-cafe-transfer-same_day_transfer",
            "food-order-transfer": "ja-card-order-convenience-transfer-same_day_transfer",
        }

        for alias, lesson_id in aliases.items():
            with self.subTest(alias=alias):
                response = TestClient(app).get(f"/api/languages/ja/lessons?lesson={alias}")

                self.assertEqual(response.status_code, 200)
                lessons = response.json()["lessons"]
                self.assertEqual(len(lessons), 1)
                self.assertEqual(lessons[0]["id"], lesson_id)

    def test_transfer_lesson_uses_scene_recall_without_target_replay(self):
        response = TestClient(app).get(
            "/api/languages/ja/lessons?lesson=ja-card-greeting-neighbor-transfer-same_day_transfer"
        )

        self.assertEqual(response.status_code, 200)
        steps = response.json()["lessons"][0]["steps"]
        step_types = [step["type"] for step in steps]
        meaning_step = next(step for step in steps if step["type"] == "broad_meaning_guess")

        self.assertEqual(step_types, ["scene_setup", "broad_meaning_guess", "scene_recall"])
        self.assertEqual(meaning_step["frameId"], "line-0")
        self.assertEqual(meaning_step["props"]["question"], "What is the best response here?")
        self.assertEqual(meaning_step["props"]["difficulty"], "medium")

    def test_delayed_scene_set_uses_delayed_review_aliases(self):
        response = TestClient(app).get("/api/languages/ja/lessons?scene_set=delayed&lesson=hello")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        lesson = payload["lessons"][0]
        meaning_step = next(step for step in lesson["steps"] if step["type"] == "broad_meaning_guess")

        self.assertEqual(payload["scene_set"], "delayed")
        self.assertEqual(
            set(tab["id"] for tab in payload["lesson_tabs"]),
            {"hello", "introduce", "repair", "excuse-me", "food-order"},
        )
        self.assertEqual(
            set(tab["label"] for tab in payload["lesson_tabs"]),
            {f"Scene {index}" for index in range(1, 6)},
        )
        self.assertEqual(lesson["id"], "ja-card-greeting-entry-review-delayed_review")
        self.assertEqual(lesson["stage"], "delayed_review")
        self.assertEqual(meaning_step["props"]["difficulty"], "hard")

    def test_lesson_order_seed_reproduces_randomized_groups(self):
        client = TestClient(app)
        first_response = client.get("/api/languages/ja/lessons?scene_set=delayed&order_seed=review-day-1")
        second_response = client.get("/api/languages/ja/lessons?scene_set=delayed&order_seed=review-day-1")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            [tab["id"] for tab in first_response.json()["lesson_tabs"]],
            [tab["id"] for tab in second_response.json()["lesson_tabs"]],
        )

    def test_fallback_choices_do_not_repeat_learner_says_prefix(self):
        response = TestClient(app).get(
            "/api/languages/ja/lessons?lesson=ja-card-greeting-neighbor-transfer-same_day_transfer"
        )

        self.assertEqual(response.status_code, 200)
        meaning_step = next(
            step for step in response.json()["lessons"][0]["steps"] if step["type"] == "broad_meaning_guess"
        )

        self.assertFalse(
            any(choice["label"].startswith("The learner says") for choice in meaning_step["props"]["choices"])
        )

    def test_lessons_endpoint_rejects_unknown_preview_lesson(self):
        response = TestClient(app).get("/api/languages/en/lessons?lesson=missing")

        self.assertEqual(response.status_code, 404)

    def test_distractors_endpoint_returns_shared_meaning_levels(self):
        response = TestClient(app).get("/api/languages/en/distractors")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_set = payload["meaning_distractors"][0]

        self.assertEqual(payload["language"], "en")
        self.assertIn("function_id", first_set)
        self.assertIn("easy", first_set["levels"])
        self.assertIn("medium", first_set["levels"])
        self.assertIn("hard", first_set["levels"])

    def test_validation_session_saves_events_and_attempts_locally(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.main.validation_store", store), patch("app.main.conversation_coach", FakeConversationCoach()):
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
            with patch("app.main.validation_store", store):
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
            with patch("app.main.validation_store", store):
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
            with patch("app.main.validation_store", store):
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
            with patch("app.main.validation_store", store), patch("app.main.conversation_coach", FakeConversationCoach()):
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
            with patch("app.main.validation_store", store):
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


if __name__ == "__main__":
    unittest.main()
