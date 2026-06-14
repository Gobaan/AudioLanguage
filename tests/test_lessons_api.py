import unittest

from fastapi.testclient import TestClient

from test_support import app


class LessonsApiTests(unittest.TestCase):
    def test_language_selection_routes_and_new_languages_load(self):
        client = TestClient(app)

        languages_response = client.get("/languages")
        learn_response = client.get("/learn?language=yue&lesson=hello")
        api_languages_response = client.get("/api/languages")
        cantonese_response = client.get("/api/languages/yue/lessons?lesson=hello")
        tamil_response = client.get("/api/languages/ta/lessons?lesson=hello")

        self.assertEqual(languages_response.status_code, 200)
        self.assertEqual(learn_response.status_code, 200)
        self.assertEqual(api_languages_response.status_code, 200)
        languages = api_languages_response.json()
        yue = next(item for item in languages if item["id"] == "yue")
        ta = next(item for item in languages if item["id"] == "ta")
        ja = next(item for item in languages if item["id"] == "ja")
        en = next(item for item in languages if item["id"] == "en")

        self.assertEqual(yue["display_name"], "Cantonese")
        self.assertEqual(yue["description"], "Cantonese starter scenes for your friend.")
        self.assertEqual(yue["scene_sets"], ["mvp", "delayed"])
        self.assertEqual(ta["display_name"], "Tamil")
        self.assertEqual(ta["description"], "Tamil starter scenes for you.")
        self.assertEqual(ta["scene_sets"], ["mvp", "delayed"])
        self.assertEqual(ja["scene_sets"], ["mvp", "delayed"])
        self.assertEqual(en["scene_sets"], ["mvp", "delayed"])
        self.assertEqual(en["description"], "English reference scenes.")
        self.assertEqual(ja["sort_order"], 1)
        self.assertEqual(yue["sort_order"], 2)
        self.assertEqual([item["id"] for item in languages], ["ja", "yue", "zh", "ta", "en"])
        self.assertEqual(cantonese_response.status_code, 200)
        self.assertEqual(cantonese_response.json()["lessons"][0]["language"], "yue")
        self.assertEqual(tamil_response.status_code, 200)
        self.assertEqual(tamil_response.json()["lessons"][0]["language"], "ta")

    def test_lessons_endpoint_returns_frontend_renderable_lessons(self):
        response = TestClient(app).get("/api/languages/ja/lessons")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_lesson = payload["lessons"][0]
        step_types = [step["type"] for step in first_lesson["steps"]]
        meaning_step = next(step for step in first_lesson["steps"] if step["type"] == "broad_meaning_guess")

        self.assertEqual(payload["language"], "ja")
        tab_ids = [tab["id"] for tab in payload["lesson_tabs"]]
        tab_labels = [tab["label"] for tab in payload["lesson_tabs"]]
        self.assertEqual(
            tab_ids[:5],
            [
                "hello",
                "introduce",
                "repair",
                "excuse-me",
                "food-order",
            ],
        )
        self.assertEqual(
            set(tab_ids[5:]),
            {
                "hello-transfer",
                "introduce-transfer",
                "repair-transfer",
                "excuse-me-transfer",
                "food-order-transfer",
            },
        )
        self.assertEqual(tab_labels[:5], [f"Scene {index}" for index in range(1, 6)])
        self.assertEqual(set(tab_labels[5:]), {f"Scene {index}" for index in range(6, 11)})
        self.assertTrue(first_lesson["frames"][0]["imageUrl"].startswith("/visuals/"))
        self.assertNotIn("target_audio", step_types)
        self.assertIn("scene_setup", step_types)
        self.assertIn("backward_build", step_types)
        self.assertNotIn("repeat_with_mic", step_types)
        self.assertNotIn("scene_recall", step_types)
        self.assertNotIn("scorecard", step_types)
        self.assertNotIn("schedule_review", step_types)
        self.assertGreaterEqual(len(meaning_step["props"]["choices"]), 2)
        self.assertFalse(
            any(choice["label"].startswith("The learner says") for choice in meaning_step["props"]["choices"])
        )

    def test_lessons_endpoint_can_return_named_preview_lesson(self):
        response = TestClient(app).get("/api/languages/en/lessons?lesson=excuse-me")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        lessons = payload["lessons"]
        step_types = [step["type"] for step in lessons[0]["steps"]]

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["id"], "en-card-excuse-me-dialogue-practice")
        self.assertEqual(lessons[0]["target"]["text"], "Excuse me.")
        self.assertIn("backward_build", step_types)
        self.assertNotIn("repeat_with_mic", step_types)
        self.assertEqual(len(lessons[0]["steps"][-1]["props"]["prompts"]), 1)
        tab_ids = [tab["id"] for tab in payload["lesson_tabs"]]
        tab_labels = [tab["label"] for tab in payload["lesson_tabs"]]
        self.assertEqual(
            tab_ids[:5],
            ["hello", "introduce", "repair", "excuse-me", "food-order"],
        )
        self.assertEqual(
            set(tab_ids[5:]),
            {
                "hello-transfer",
                "introduce-transfer",
                "repair-transfer",
                "excuse-me-transfer",
                "food-order-transfer",
            },
        )
        self.assertEqual(tab_labels[:5], [f"Scene {index}" for index in range(1, 6)])
        self.assertEqual(set(tab_labels[5:]), {f"Scene {index}" for index in range(6, 11)})

    def test_lessons_endpoint_supports_all_mvp_lesson_aliases(self):
        aliases = {
            "hello": "en-card-first-hi-dialogue-practice",
            "introduce": "en-card-introduce-self-dialogue-practice",
            "repair": "en-card-dont-understand-dialogue-practice",
            "excuse-me": "en-card-excuse-me-dialogue-practice",
            "food-order": "en-card-order-food-dialogue-practice",
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
            "hello-transfer": "ja-card-greeting-neighbor-transfer-same_day_transfer",
            "introduce-transfer": "ja-card-introduce-class-transfer-same_day_transfer",
            "repair-transfer": "ja-card-repair-ticket-transfer-same_day_transfer",
            "excuse-me-transfer": "ja-card-excuse-me-cafe-transfer-same_day_transfer",
            "food-order-transfer": "ja-card-order-convenience-transfer-same_day_transfer",
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
        steps = response.json()["lessons"][0]["steps"]
        step_types = [step["type"] for step in steps]
        setup_step = next(step for step in steps if step["type"] == "scene_setup")
        meaning_step = next(step for step in steps if step["type"] == "broad_meaning_guess")
        recall_step = next(step for step in steps if step["type"] == "scene_recall")

        self.assertEqual(step_types, ["scene_setup", "broad_meaning_guess", "scene_recall"])
        self.assertEqual(setup_step["props"]["stopAtLineType"], "world_opener")
        self.assertEqual(meaning_step["frameId"], "line-0")
        self.assertEqual(meaning_step["props"]["question"], "What is the best response here?")
        self.assertEqual(meaning_step["props"]["difficulty"], "medium")
        self.assertFalse(meaning_step["props"]["revealDialogueAfterChoice"])
        self.assertTrue(meaning_step["props"]["revealDialogueOnIncorrectOnly"])
        self.assertEqual(recall_step["frameId"], "line-0")
        self.assertFalse(recall_step["audio"]["autoplay"])
        self.assertFalse(recall_step["audio"]["playBeforeMic"])
        self.assertIsNone(recall_step["audio"]["url"])
        self.assertTrue(recall_step["props"]["playModelLineAfterAttempt"])
        self.assertTrue(recall_step["props"]["playWorldResponseAfterAttempt"])
        self.assertTrue(recall_step["props"]["showDialogueRevealAfterAttempt"])
        self.assertTrue(recall_step["props"]["recordBeforeModelLine"])

    def test_delayed_review_lesson_tests_before_model_line(self):
        response = TestClient(app).get(
            "/api/languages/ja/lessons?scene_set=delayed&lesson=hello"
        )

        self.assertEqual(response.status_code, 200)
        steps = response.json()["lessons"][0]["steps"]
        setup_step = next(step for step in steps if step["type"] == "scene_setup")
        recall_step = next(step for step in steps if step["type"] == "scene_recall")

        self.assertEqual(setup_step["props"]["stopAtLineType"], "world_opener")
        self.assertEqual(recall_step["frameId"], "line-0")
        self.assertTrue(recall_step["props"]["recordBeforeModelLine"])
        self.assertTrue(recall_step["props"]["playModelLineAfterAttempt"])
        self.assertTrue(recall_step["props"]["playWorldResponseAfterAttempt"])
        self.assertFalse(recall_step["audio"]["playBeforeMic"])
        playback_flow = recall_step["props"]["playbackFlow"]
        record_index = next(
            index for index, item in enumerate(playback_flow) if item["type"] == "record_attempt"
        )
        post_record_lines = [
            item["line_type"]
            for item in playback_flow[record_index + 1 :]
            if item["type"] == "play_line"
        ]
        self.assertEqual(post_record_lines, ["learner_target", "world_response"])

    def test_delayed_scene_set_uses_delayed_review_aliases(self):
        response = TestClient(app).get("/api/languages/ja/lessons?scene_set=delayed&lesson=hello")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        lesson = payload["lessons"][0]
        meaning_step = next(step for step in lesson["steps"] if step["type"] == "broad_meaning_guess")

        self.assertEqual(payload["scene_set"], "delayed")
        self.assertEqual(
            set(tab["id"] for tab in payload["lesson_tabs"]),
            {"hello", "introduce", "repair", "excuse-me", "food-order"},
        )
        self.assertEqual(
            set(tab["label"] for tab in payload["lesson_tabs"]),
            {f"Scene {index}" for index in range(1, 6)},
        )
        self.assertEqual(lesson["id"], "ja-card-greeting-entry-review-delayed_review")
        self.assertEqual(lesson["stage"], "delayed_review")
        self.assertEqual(meaning_step["props"]["difficulty"], "hard")

    def test_lesson_order_seed_reproduces_randomized_groups(self):
        client = TestClient(app)
        first_response = client.get("/api/languages/ja/lessons?scene_set=delayed&order_seed=review-day-1")
        second_response = client.get("/api/languages/ja/lessons?scene_set=delayed&order_seed=review-day-1")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            [tab["id"] for tab in first_response.json()["lesson_tabs"]],
            [tab["id"] for tab in second_response.json()["lesson_tabs"]],
        )

    def test_fallback_choices_do_not_repeat_learner_says_prefix(self):
        response = TestClient(app).get(
            "/api/languages/ja/lessons?lesson=ja-card-greeting-neighbor-transfer-same_day_transfer"
        )

        self.assertEqual(response.status_code, 200)
        meaning_step = next(
            step for step in response.json()["lessons"][0]["steps"] if step["type"] == "broad_meaning_guess"
        )

        self.assertFalse(
            any(choice["label"].startswith("The learner says") for choice in meaning_step["props"]["choices"])
        )

    def test_lessons_endpoint_rejects_unknown_preview_lesson(self):
        response = TestClient(app).get("/api/languages/en/lessons?lesson=missing")

        self.assertEqual(response.status_code, 404)

    def test_distractors_endpoint_returns_shared_meaning_levels(self):
        response = TestClient(app).get("/api/languages/en/distractors")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_set = payload["meaning_distractors"][0]

        self.assertEqual(payload["language"], "en")
        self.assertIn("function_id", first_set)
        self.assertIn("easy", first_set["levels"])
        self.assertIn("medium", first_set["levels"])
        self.assertIn("hard", first_set["levels"])


if __name__ == "__main__":
    unittest.main()
