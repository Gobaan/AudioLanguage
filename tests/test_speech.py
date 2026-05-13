import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.speech.language import japanese_to_romaji, tamil_to_latin
from app.speech.transcription import unavailable_transcription


class TamilRomanizationTests(unittest.TestCase):
    def test_tamil_to_latin_handles_native_script(self):
        self.assertEqual(tamil_to_latin("\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd"), "vanakkam")


class JapaneseRomanizationTests(unittest.TestCase):
    def test_japanese_to_romaji_handles_mvp_phrases(self):
        self.assertEqual(japanese_to_romaji("こんにちは！"), "konnichiwa!")
        self.assertEqual(japanese_to_romaji("病院はどこですか？"), "byouin wa doko desu ka?")
        self.assertEqual(japanese_to_romaji("サンドイッチを一つお願いします。"), "sandoicchi o hitotsu onegaishimasu.")

    def test_japanese_to_romaji_preserves_english_feedback(self):
        feedback = "For a greeting response, say こんにちは or どうも."

        self.assertEqual(
            japanese_to_romaji(feedback),
            "For a greeting response, say konnichiwa or doumo.",
        )


class SpeechTranscriptionTests(unittest.TestCase):
    def test_unavailable_transcription_returns_safe_empty_result(self):
        result = unavailable_transcription("missing model")

        self.assertFalse(result["available"])
        self.assertEqual(result["romanized"], "")
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["feedback"], "missing model")


if __name__ == "__main__":
    unittest.main()
