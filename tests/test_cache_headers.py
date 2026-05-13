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


if __name__ == "__main__":
    unittest.main()
