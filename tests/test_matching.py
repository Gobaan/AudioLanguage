import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.speech.similarity import normalize_for_match, text_similarity


class MatchingTests(unittest.TestCase):
    def test_normalize_for_match_removes_case_and_punctuation(self):
        self.assertEqual(normalize_for_match("  Hello, WORLD!! "), "hello world")

    def test_text_similarity_matches_normalized_equivalent_text(self):
        self.assertEqual(text_similarity("Hello, world!", "hello world"), 1.0)

    def test_text_similarity_returns_zero_for_missing_input(self):
        self.assertEqual(text_similarity("", "hello"), 0.0)
        self.assertEqual(text_similarity("hello", ""), 0.0)


if __name__ == "__main__":
    unittest.main()
