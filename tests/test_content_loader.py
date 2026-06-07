import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from app.content.loader import load_content_graph
from app.content.data_graph import list_languages, load_language_session
from app.content.lessons import (
    backward_build_prompts,
    lessons_from_session,
    should_include_backward_build,
)
from content_assets import read_json, write_json
from generate_images_from_manifest import generate_language

CONTENT_DIR = PROJECT_DIR / "model" / "content"
ASSETS_DIR = PROJECT_DIR / "model" / "assets"


class ContentLoaderTests(unittest.TestCase):
    def test_loads_dialogues_with_category_and_assets(self):
        graph = load_content_graph(ASSETS_DIR / "audio_sources" / "dialogues.json")

        first = graph.dialogues[0]

        self.assertEqual(first.id, "ta-greeting-hello")
        self.assertEqual(first.category, "greeting")
        self.assertEqual(first.category_label, "Greetings")
        self.assertEqual(first.type, "anchor")
        self.assertIn("produce_from_visual", first.review_modes)
        self.assertEqual(first.lines[0].audio, "/audio/ta-greeting-hello-0.mp3")
        self.assertEqual(first.lines[0].visual, "/visuals/ta-greeting-hello/frame-0.png")
        self.assertFalse(first.lines[0].is_learner_target)
        self.assertTrue(first.lines[1].is_learner_target)

class StructuredDataGraphTests(unittest.TestCase):
    def test_loads_tamil_session_with_hydrated_references(self):
        session = load_language_session(
            data_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
            language="ta",
        )

        first = session["cards"][0]

        self.assertEqual(session["language"], "ta")
        self.assertEqual(first["dialogue"]["id"], "ta-greeting-hello")
        self.assertEqual(first["target"]["id"], "ta-target-hello-how-are-you")
        self.assertEqual(first["function"]["id"], "greet_and_ask_wellbeing")
        self.assertEqual(first["scene"]["id"], "study-room-friend")
        self.assertEqual(first["review_mode"]["id"], "ai_guided_response")
        self.assertTrue(first["dialogue"]["lines"][1]["is_learner_target"])
        self.assertNotIn("chunk_audio", first["dialogue"]["lines"][1])

    def test_applies_default_guided_dialogue_template_support(self):
        session = load_language_session(
            data_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
            language="en",
        )

        first = session["cards"][0]

        self.assertEqual(first["template_id"], "guided-dialogue-replay-v1")
        self.assertEqual(first["template"]["id"], "guided-dialogue-replay-v1")
        self.assertEqual(
            [step["type"] for step in first["template"]["playback_flow"]],
            ["play_line", "play_line", "record_attempt", "play_line"],
        )
        self.assertEqual(first["template"]["playback_flow"][2]["judgement"], "deferred")
        self.assertTrue(first["support"]["play_full_dialogue_first"])
        self.assertTrue(first["support"]["autoplay_full_dialogue"])
        self.assertTrue(first["support"]["replay_until_learner_turn"])
        self.assertFalse(first["support"]["show_examples_before_attempt"])

    def test_english_mvp_session_has_five_guided_scenarios_with_audio(self):
        session = load_language_session(
            data_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
            language="en",
        )

        self.assertEqual(len(session["cards"]), 5)
        for card in session["cards"]:
            self.assertEqual(card["template_id"], "guided-dialogue-replay-v1")
            self.assertEqual(card["mode"], "ai_guided_response")
            self.assertTrue(card["ai_scene_contract"]["target_function"]["definition"])
            self.assertTrue(card["ai_scene_contract"]["required_slots"])
            self.assertTrue(all(line.get("audio") for line in card["dialogue"]["lines"]))

    def test_short_targets_skip_backward_build(self):
        session = load_language_session(
            data_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
            language="en",
        )

        lesson = lessons_from_session(session)[0]
        step_ids = [step["id"] for step in lesson["steps"]]

        self.assertEqual(lesson["target"]["text"], "Hi!")
        self.assertNotIn("backward_build", step_ids)
        self.assertNotIn("audio_replay", step_ids)

    def test_first_session_excludes_meaning_cued_production_prompt(self):
        session = load_language_session(
            data_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
            language="en",
        )

        lesson = lessons_from_session(session)[0]

        self.assertNotIn("production_prompt", [step["id"] for step in lesson["steps"]])

    def test_backward_build_uses_phrase_units_not_meaning_tags(self):
        target = {
            "id": "en-target-test",
            "canonical": "Where is the bus stop?",
            "meaning_units": ["where", "place", "question"],
        }

        self.assertTrue(should_include_backward_build(target=target, target_phrase=target["canonical"]))
        self.assertEqual(
            [prompt["text"] for prompt in backward_build_prompts(target=target, target_phrase=target["canonical"], target_audio=None)],
            [
                "stop",
                "bus stop",
                "the bus stop",
                "is the bus stop",
                "Where is the bus stop?",
            ],
        )

    def test_backward_build_audio_only_uses_target_audio_for_full_prompt(self):
        target = {
            "id": "en-target-test",
            "canonical": "Where is the bus stop?",
        }

        prompts = backward_build_prompts(
            target=target,
            target_phrase=target["canonical"],
            target_audio="/audio/generated/en/example/line-1.mp3",
        )

        self.assertEqual([prompt["audioText"] for prompt in prompts], [prompt["text"] for prompt in prompts])
        self.assertEqual([prompt["audioUrl"] for prompt in prompts[:-1]], [None, None, None, None])
        self.assertEqual(prompts[-1]["audioUrl"], "/audio/generated/en/example/line-1.mp3")

    def test_japanese_first_session_uses_short_beginner_chunks(self):
        session = load_language_session(
            data_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
            language="ja",
        )

        learner_lines = [
            card["dialogue"]["lines"][1]["transliteration"]
            for card in session["cards"]
        ]

        self.assertEqual(len(session["cards"]), 15)
        self.assertEqual(
            learner_lines[:5],
            [
                "Konnichiwa!",
                "Anna desu.",
                "Wakarimasen.",
                "Sumimasen.",
                "Sandoicchi kudasai.",
            ],
        )
        self.assertEqual(
            learner_lines[5:],
            [
                "Konnichiwa!",
                "Anna desu.",
                "Wakarimasen.",
                "Sumimasen.",
                "Sandoicchi kudasai.",
                "Konnichiwa!",
                "Anna desu.",
                "Wakarimasen.",
                "Sumimasen.",
                "Sandoicchi kudasai.",
            ],
        )
        self.assertEqual(
            [card["stage"] for card in session["cards"]],
            [
                "guided_scene_production",
                "guided_scene_production",
                "guided_scene_production",
                "guided_scene_production",
                "guided_scene_production",
                "same_day_transfer",
                "same_day_transfer",
                "same_day_transfer",
                "same_day_transfer",
                "same_day_transfer",
                "delayed_review",
                "delayed_review",
                "delayed_review",
                "delayed_review",
                "delayed_review",
            ],
        )
        for card in session["cards"]:
            self.assertTrue(card["support"]["show_transliteration_after_failure"])
            for line in card["dialogue"]["lines"]:
                self.assertNotIn("???", line["text"])
                self.assertTrue(line["transliteration"])
                self.assertTrue(line["audio"])
                self.assertTrue((ASSETS_DIR / line["audio"].lstrip("/")).exists())
                self.assertTrue(
                    str(line["visual"]).startswith(("/visuals/final/", "/visuals/Drafts/"))
                )
                self.assertTrue((ASSETS_DIR / line["visual"].lstrip("/")).exists())

    def test_active_language_sessions_have_complete_dialogue_assets(self):
        languages = [language["id"] for language in list_languages(CONTENT_DIR)]

        for language in languages:
            with self.subTest(language=language):
                session = load_language_session(
                    data_dir=CONTENT_DIR,
                    project_dir=PROJECT_DIR,
                    language=language,
                )
                requires_transliteration = session.get("script") not in {None, "English", "Latin"}

                for card in session["cards"]:
                    with self.subTest(language=language, card=card["id"]):
                        self.assertTrue(card["dialogue"].get("lines"))
                        for line in card["dialogue"]["lines"]:
                            line_label = f"{card['id']} line {line.get('index')}"
                            text = str(line.get("text", ""))
                            transliteration = str(line.get("transliteration", ""))
                            audio = line.get("audio")
                            audio_text = line.get("audio_text")
                            visual = line.get("visual")

                            self.assertNotIn("???", text, line_label)
                            self.assertTrue(text.strip(), line_label)
                            if requires_transliteration:
                                self.assertTrue(transliteration.strip(), line_label)
                            self.assertTrue(audio or audio_text, line_label)
                            if audio:
                                self.assertTrue((ASSETS_DIR / str(audio).lstrip("/")).exists(), line_label)
                            self.assertTrue(visual, line_label)
                            self.assertTrue((ASSETS_DIR / str(visual).lstrip("/")).exists(), line_label)

    def test_lists_languages_from_data_graph(self):
        languages = list_languages(CONTENT_DIR)

        self.assertIn({"id": "ta", "display_name": "Tamil"}, languages)
        self.assertIn({"id": "yue", "display_name": "Cantonese"}, languages)


class VisualGenerationScriptTests(unittest.TestCase):
    def test_draft_generation_writes_drafts_without_updating_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            data_dir = project_dir / "model" / "content"
            manifest_path = data_dir / "languages" / "ja" / "visual_prompts.json"
            manifest = {
                "prompts": [
                    {
                        "id": "ja-test-frame-0",
                        "dialogue_id": "ja-test",
                        "line_index": 0,
                        "localized_prompt": "A friendly greeting scene.",
                        "image_path": "visuals/generated/ja/ja-test/frame-0.png",
                        "status": "needs_generation",
                    }
                ]
            }
            write_json(manifest_path, manifest)

            def fake_generate_image(**kwargs):
                out_path = kwargs["out_path"]
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(b"png")
                return []

            with patch("generate_images_from_manifest.generate_image", side_effect=fake_generate_image):
                created, skipped = generate_language(
                    data_dir=data_dir,
                    project_dir=project_dir,
                    language="ja",
                    model="test-model",
                    size="1024x1024",
                    quality="low",
                    reference_mode="never",
                    force=False,
                    limit=None,
                    dialogue_ids=None,
                    prompt_ids=None,
                    include_previous_frame=False,
                    explicit_reference_paths=[],
                    output_mode="draft",
                    draft_root=Path("visuals/Drafts"),
                )

            self.assertEqual((created, skipped), (1, 0))
            self.assertTrue(
                (project_dir / "model/assets/visuals/Drafts/ja-test/frame-0.png").exists()
            )
            self.assertFalse(
                (project_dir / "model/assets/visuals/generated/ja/ja-test/frame-0.png").exists()
            )
            self.assertEqual(read_json(manifest_path), manifest)


if __name__ == "__main__":
    unittest.main()
