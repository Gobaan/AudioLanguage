import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from content_assets import write_json
from lint_dialogues import lint_language


def write_language_fixture(
    base_dir: Path,
    *,
    language: str,
    script: str,
    dialogues: list[dict],
) -> None:
    language_dir = base_dir / "languages" / language
    write_json(
        language_dir / "targets.json",
        {
            "language": language,
            "display_name": language,
            "script": script,
            "targets": [],
        },
    )
    write_json(
        language_dir / "dialogues.json",
        {
            "language": language,
            "display_name": language,
            "script": script,
            "dialogues": dialogues,
        },
    )


class DialogueLinterTests(unittest.TestCase):
    def test_valid_dialogue_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "model" / "content"
            write_language_fixture(
                data_dir,
                language="ar",
                script="Arabic",
                dialogues=[
                    {
                        "id": "ar-test",
                        "target_id": "ar-target-hi",
                        "lines": [
                            {
                                "index": 0,
                                "line_type": "world_opener",
                                "text": "مرحبًا.",
                                "transliteration": "Marhaban.",
                            },
                            {
                                "index": 1,
                                "line_type": "learner_target",
                                "target_id": "ar-target-hi",
                                "text": "مرحبًا!",
                                "transliteration": "Marhaban!",
                            },
                            {
                                "index": 2,
                                "line_type": "world_response",
                                "text": "أهلًا.",
                                "transliteration": "Ahlan.",
                            },
                        ],
                    }
                ],
            )
            self.assertEqual(lint_language(data_dir, "ar", strict_beginner_shape=True), [])

    def test_flags_missing_transliteration_for_non_latin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "model" / "content"
            write_language_fixture(
                data_dir,
                language="ar",
                script="Arabic",
                dialogues=[
                    {
                        "id": "ar-test",
                        "target_id": "ar-target-hi",
                        "lines": [
                            {"index": 0, "line_type": "world_opener", "text": "مرحبًا"},
                            {
                                "index": 1,
                                "line_type": "learner_target",
                                "target_id": "ar-target-hi",
                                "text": "مرحبًا",
                            },
                            {"index": 2, "line_type": "world_response", "text": "أهلًا"},
                        ],
                    }
                ],
            )
            errors = lint_language(data_dir, "ar", strict_beginner_shape=True)
            self.assertTrue(any("missing transliteration" in error for error in errors))

    def test_flags_non_contiguous_indexes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "model" / "content"
            write_language_fixture(
                data_dir,
                language="en",
                script="English",
                dialogues=[
                    {
                        "id": "en-test",
                        "target_id": "en-target-hi",
                        "lines": [
                            {"index": 0, "line_type": "world_opener", "text": "Hi"},
                            {"index": 2, "line_type": "learner_target", "target_id": "en-target-hi", "text": "Hi"},
                            {"index": 3, "line_type": "world_response", "text": "Great"},
                        ],
                    }
                ],
            )
            errors = lint_language(data_dir, "en", strict_beginner_shape=True)
            self.assertTrue(any("line indexes must be contiguous" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
