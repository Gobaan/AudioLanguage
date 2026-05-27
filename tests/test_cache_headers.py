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
        response = TestClient(app).get("/static/styles.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers["cache-control"])

    def test_lessons_endpoint_returns_frontend_renderable_lessons(self):
        response = TestClient(app).get("/api/languages/ja/lessons")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_lesson = payload["lessons"][0]
        step_types = [step["type"] for step in first_lesson["steps"]]

        self.assertEqual(payload["language"], "ja")
        self.assertEqual(first_lesson["player_component"], "TravellerLessonPlayer")
        self.assertTrue(first_lesson["frames"][0]["imageUrl"].startswith("/visuals/"))
        self.assertIn("scene_setup", step_types)
        self.assertIn("target_audio", step_types)
        self.assertIn("repeat_with_mic", step_types)
        self.assertIn("schedule_review", step_types)


if __name__ == "__main__":
    unittest.main()
