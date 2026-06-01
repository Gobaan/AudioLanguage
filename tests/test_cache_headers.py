import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app


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

    def test_lessons_endpoint_returns_frontend_renderable_lessons(self):
        response = TestClient(app).get("/api/languages/ja/lessons")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_lesson = payload["lessons"][0]
        step_types = [step["type"] for step in first_lesson["steps"]]
        meaning_step = next(step for step in first_lesson["steps"] if step["type"] == "broad_meaning_guess")

        self.assertEqual(payload["language"], "ja")
        self.assertEqual(
            [tab["id"] for tab in payload["lesson_tabs"]],
            ["hello", "introduce", "repair", "excuse-me", "food-order"],
        )
        self.assertEqual(first_lesson["player_component"], "TravellerLessonPlayer")
        self.assertTrue(first_lesson["frames"][0]["imageUrl"].startswith("/visuals/"))
        self.assertIn("scene_setup", step_types)
        self.assertIn("target_audio", step_types)
        self.assertIn("repeat_with_mic", step_types)
        self.assertNotIn("scene_recall", step_types)
        self.assertNotIn("scorecard", step_types)
        self.assertNotIn("schedule_review", step_types)
        self.assertGreaterEqual(len(meaning_step["props"]["choices"]), 2)

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
        self.assertEqual(
            [tab["id"] for tab in payload["lesson_tabs"]],
            ["hello", "introduce", "repair", "food-order", "hospital"],
        )

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
        step_types = [step["type"] for step in response.json()["lessons"][0]["steps"]]

        self.assertEqual(step_types, ["scene_setup", "broad_meaning_guess", "scene_recall"])

    def test_lessons_endpoint_rejects_unknown_preview_lesson(self):
        response = TestClient(app).get("/api/languages/en/lessons?lesson=missing")

        self.assertEqual(response.status_code, 404)

    def test_distractors_endpoint_returns_dialogue_levels(self):
        response = TestClient(app).get("/api/languages/en/distractors")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_set = payload["dialogue_distractors"][0]

        self.assertEqual(payload["language"], "en")
        self.assertIn("dialogue_id", first_set)
        self.assertIn("easy", first_set["levels"])
        self.assertIn("medium", first_set["levels"])
        self.assertIn("hard", first_set["levels"])


if __name__ == "__main__":
    unittest.main()
