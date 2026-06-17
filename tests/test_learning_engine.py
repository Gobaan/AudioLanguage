import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from test_support import app
from app.content.learning_engine import build_learning_plan
from app.content.learning_engine.state_store import LearningStateStore
from app.validation import ValidationStore


class LearningEngineTests(unittest.TestCase):
    def test_import_contract_stays_public(self):
        from app.content.learning_engine import build_learning_plan as imported

        self.assertTrue(callable(imported))

    def test_endpoint_without_participant_keeps_legacy_shape(self):
        response = TestClient(app).get(
            "/api/learning-engine/lessons?language=ja&scene_set=mvp&order_seed=legacy"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plan_version"], 1)
        self.assertEqual(payload["session_id"], "ja:mvp:legacy")
        self.assertEqual(len(payload["lessons"]), 10)
        self.assertNotIn("participant_id", payload)

    def test_endpoint_with_participant_returns_personalized_three_scene_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            with patch("app.routes.content.validation_store", store):
                response = TestClient(app).get(
                    "/api/learning-engine/lessons?language=ja&scene_set=mvp"
                    "&order_seed=adaptive&participant_id=Bob"
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plan_version"], 2)
        self.assertEqual(payload["participant_id"], "Bob")
        self.assertEqual(len(payload["lessons"]), 3)
        self.assertTrue(all(lesson["planPurpose"] == "new" for lesson in payload["lessons"]))
        self.assertTrue(all(lesson["repairCategory"] == "new" for lesson in payload["lessons"]))
        self.assertTrue(all(lesson["targetId"] == lesson["target"]["id"] for lesson in payload["lessons"]))

    def test_validation_state_updates_drive_repair_categories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            create_session(store, "repairs", "Bob", "ja")
            store.append_event(
                "repairs",
                {
                    "type": "choice_selected",
                    "participantId": "Bob",
                    "language": "ja",
                    "sceneSet": "mvp",
                    "lessonId": "ja-card-first-hi-dialogue-practice",
                    "lessonPage": "hello",
                    "stepId": "broad_meaning_guess",
                    "targetId": "ja-target-respond-hi",
                    "isCorrect": False,
                },
            )
            save_and_score(
                store,
                "repairs",
                "attempt-introduce",
                "ja-card-introduce-self-dialogue-practice",
                "ja-target-my-name-is",
                passed=False,
            )
            save_and_score(
                store,
                "repairs",
                "attempt-repair-anchor",
                "ja-card-dont-understand-dialogue-practice",
                "ja-target-i-dont-understand",
                passed=True,
            )
            save_and_score(
                store,
                "repairs",
                "attempt-repair-transfer",
                "ja-card-repair-ticket-transfer-same_day_transfer",
                "ja-target-i-dont-understand",
                passed=False,
            )
            save_and_score(
                store,
                "repairs",
                "attempt-excuse-anchor",
                "ja-card-excuse-me-dialogue-practice",
                "ja-target-excuse-me-attention",
                passed=True,
            )
            save_and_score(
                store,
                "repairs",
                "attempt-excuse-delayed",
                "ja-card-excuse-me-station-review-delayed_review",
                "ja-target-excuse-me-attention",
                passed=False,
                scene_set="delayed",
            )

            plan = build_learning_plan(
                data_dir=Path("model/content"),
                project_dir=Path("."),
                language="ja",
                scene_set="mvp",
                order_seed="repairs",
                participant_id="Bob",
                state_store=store.learning_state,
            )

        self.assertEqual(len(plan["lessons"]), 3)
        purposes = [lesson["planPurpose"] for lesson in plan["lessons"]]
        target_ids = [lesson["targetId"] for lesson in plan["lessons"]]
        self.assertEqual(purposes, ["meaning_repair", "recall_repair", "transfer_repair"])
        self.assertEqual(
            target_ids,
            [
                "ja-target-respond-hi",
                "ja-target-my-name-is",
                "ja-target-i-dont-understand",
            ],
        )

    def test_unscored_attempt_is_neutral_and_transfer_practice_can_fill_slot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            create_session(store, "pending", "Bob", "ja")
            store.save_attempt(
                session_id="pending",
                attempt_id="pending-food",
                filename="attempt.webm",
                content_type="audio/webm",
                audio_bytes=b"audio",
                metadata={
                    "participantId": "Bob",
                    "language": "ja",
                    "sceneSet": "mvp",
                    "lessonId": "ja-card-order-food-dialogue-practice",
                    "lessonPage": "food-order",
                    "stepId": "backward_build",
                    "targetId": "ja-target-one-local-food-please",
                },
            )
            save_and_score(
                store,
                "pending",
                "attempt-hello",
                "ja-card-first-hi-dialogue-practice",
                "ja-target-respond-hi",
                passed=True,
            )

            plan = build_learning_plan(
                data_dir=Path("model/content"),
                project_dir=Path("."),
                language="ja",
                scene_set="mvp",
                order_seed="pending",
                participant_id="Bob",
                state_store=store.learning_state,
                planning_date="2026-06-02",
            )

        self.assertLessEqual(len(plan["lessons"]), 3)
        self.assertIn("transfer_practice", [lesson["planPurpose"] for lesson in plan["lessons"]])
        self.assertNotIn("recall_repair", [lesson["planPurpose"] for lesson in plan["lessons"]])

    def test_state_can_rebuild_from_validation_jsonl(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ValidationStore(Path(temp_dir))
            create_session(store, "rebuild", "Bob", "ja")
            save_and_score(
                store,
                "rebuild",
                "attempt-hello",
                "ja-card-first-hi-dialogue-practice",
                "ja-target-respond-hi",
                passed=True,
            )
            replacement = LearningStateStore(Path(temp_dir) / "rebuilt.sqlite")
            replacement.rebuild_from_validation_root(Path(temp_dir))

            states = replacement.target_states("Bob", "ja")

        self.assertTrue(states["ja-target-respond-hi"].anchor_passed)


def create_session(store: ValidationStore, session_id: str, participant_id: str, language: str) -> None:
    store.create_session(
        {
            "sessionId": session_id,
            "participantId": participant_id,
            "language": language,
            "sceneSet": "mvp",
            "lessonPage": "hello",
        }
    )


def save_and_score(
    store: ValidationStore,
    session_id: str,
    attempt_id: str,
    lesson_id: str,
    target_id: str,
    *,
    passed: bool,
    scene_set: str = "mvp",
    reviewed_at: str = "2026-06-01",
) -> None:
    store.save_attempt(
        session_id=session_id,
        attempt_id=attempt_id,
        filename="attempt.webm",
        content_type="audio/webm",
        audio_bytes=b"audio",
        metadata={
            "participantId": "Bob",
            "language": "ja",
            "sceneSet": scene_set,
            "lessonId": lesson_id,
            "lessonPage": "hello",
            "stepId": "scene_recall" if scene_set == "delayed" else "backward_build",
            "targetId": target_id,
            "receivedAt": reviewed_at,
        },
    )
    store.save_score(
        session_id,
        attempt_id,
        {
            "receivedAt": reviewed_at,
            "status": "scored",
            "result": {
                "communication": {
                    "status": "exact" if passed else "missed",
                    "close_enough": passed,
                }
            },
        },
    )


if __name__ == "__main__":
    unittest.main()
