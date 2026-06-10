import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from test_support import PROJECT_DIR, app


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


if __name__ == "__main__":
    unittest.main()
