import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from content_assets import write_json
from speech_bubble_placement import (
    NormalizedBox,
    place_bubble,
    speech_bubble_for_line,
    update_language,
)


class SpeechBubblePlacementTests(unittest.TestCase):
    def test_learner_line_gets_mic_bubble_from_detected_left_character(self):
        bubble, candidates = speech_bubble_for_line(
            {"speaker_role": "learner", "line_type": "learner_target"},
            [
                NormalizedBox(x=0.2, y=0.28, width=0.18, height=0.45, confidence=0.9),
                NormalizedBox(x=0.62, y=0.28, width=0.18, height=0.45, confidence=0.9),
            ],
        )

        self.assertEqual(bubble["kind"], "mic")
        self.assertEqual(bubble["source"], "detected")
        self.assertLess(bubble["anchorX"], 0.5)
        self.assertEqual(bubble["tipPosition"], "left")
        self.assertEqual(bubble["tipTilt"], "left")
        self.assertEqual(bubble["rotationDegrees"], -12.0)
        self.assertGreater(len(candidates), 0)

    def test_world_line_gets_speaker_bubble_from_detected_right_character(self):
        bubble, _ = speech_bubble_for_line(
            {"speaker_role": "server", "line_type": "world_response"},
            [
                NormalizedBox(x=0.2, y=0.28, width=0.18, height=0.45, confidence=0.9),
                NormalizedBox(x=0.62, y=0.28, width=0.18, height=0.45, confidence=0.9),
            ],
        )

        self.assertEqual(bubble["kind"], "speaker")
        self.assertEqual(bubble["source"], "detected")
        self.assertGreater(bubble["anchorX"], 0.5)
        self.assertEqual(bubble["tipPosition"], "right")
        self.assertEqual(bubble["tipTilt"], "right")
        self.assertEqual(bubble["rotationDegrees"], 12.0)

    def test_fallback_placement_stays_inside_mobile_safe_area(self):
        bubble, candidates = speech_bubble_for_line(
            {"speaker_role": "learner", "line_type": "learner_target"},
            [],
        )

        self.assertEqual(bubble["kind"], "mic")
        self.assertEqual(bubble["source"], "fallback")
        self.assertEqual(candidates, [])
        self.assertGreaterEqual(bubble["anchorX"], 0.08)
        self.assertLessEqual(bubble["anchorX"], 0.92)
        self.assertGreaterEqual(bubble["anchorY"], 0.08)
        self.assertLessEqual(bubble["anchorY"], 0.72)

    def test_placement_avoids_face_overlap_when_above_slot_is_crowded(self):
        speaker = NormalizedBox(x=0.4, y=0.2, width=0.2, height=0.45, confidence=0.9)
        blocker = NormalizedBox(x=0.45, y=0.08, width=0.1, height=0.1, confidence=0.9)

        bubble = place_bubble(speaker, [speaker, blocker])

        self.assertNotEqual((round(bubble.anchor_x, 2), round(bubble.anchor_y, 2)), (0.5, 0.12))

    def test_update_language_writes_speech_bubble_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            data_dir = project_dir / "model" / "content"
            language_dir = data_dir / "languages" / "ja"
            write_json(
                language_dir / "dialogues.json",
                {
                    "dialogues": [
                        {
                            "id": "ja-test",
                            "lines": [
                                {"index": 0, "speaker_role": "friend", "line_type": "world_opener"},
                                {"index": 1, "speaker_role": "learner", "line_type": "learner_target"},
                            ],
                        }
                    ]
                },
            )
            write_json(
                language_dir / "visual_beats.json",
                {
                    "visual_beats": [
                        {"dialogue_id": "ja-test", "line_index": 0, "asset_paths": {}},
                        {"dialogue_id": "ja-test", "line_index": 1, "asset_paths": {}},
                    ]
                },
            )

            updated = update_language(data_dir=data_dir, project_dir=project_dir, language="ja", force=False)

            payload = __import__("content_assets").read_json(language_dir / "visual_beats.json")
            self.assertEqual(updated, 2)
            self.assertEqual(payload["visual_beats"][0]["speech_bubble"]["kind"], "speaker")
            self.assertEqual(payload["visual_beats"][1]["speech_bubble"]["kind"], "mic")
            self.assertEqual(payload["visual_beats"][0]["speech_bubble"]["tipPosition"], "right")
            self.assertEqual(payload["visual_beats"][1]["speech_bubble"]["tipPosition"], "left")
            self.assertEqual(payload["visual_beats"][0]["speech_bubble"]["rotationDegrees"], 12.0)
            self.assertEqual(payload["visual_beats"][1]["speech_bubble"]["rotationDegrees"], -12.0)


if __name__ == "__main__":
    unittest.main()
