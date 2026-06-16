from scripts.generate_backward_build_audio import learner_lines_by_target, spoken_phrase_for_target


def test_spoken_phrase_uses_learner_line_tts_text_before_romanized_target() -> None:
    target = {
        "id": "yue-target-respond-hi",
        "canonical": "Nei hou!",
        "transliteration": "Nei hou!",
    }
    learner_line = {
        "line_type": "learner_target",
        "target_id": "yue-target-respond-hi",
        "text": "Nei hou!",
        "audio_text": "Nei hou!",
        "tts_text": "你好！",
    }

    assert spoken_phrase_for_target(target, learner_line) == "你好！"


def test_explicit_backward_build_spoken_prompts_still_win() -> None:
    target = {
        "id": "yue-target-my-name-is",
        "canonical": "Ngo giu Anna.",
        "backward_build_spoken_prompts": ["Anna。", "叫 Anna。", "我叫 Anna。"],
    }
    learner_line = {
        "tts_text": "我叫 Anna。",
    }

    assert spoken_phrase_for_target(target, learner_line) == "我叫 Anna。"


def test_learner_lines_by_target_uses_first_learner_line() -> None:
    dialogues_payload = {
        "dialogues": [
            {
                "target_id": "target-a",
                "lines": [
                    {"index": 0, "line_type": "world_opener", "tts_text": "你好！"},
                    {"index": 1, "line_type": "learner_target", "tts_text": "你好！"},
                ],
            },
            {
                "target_id": "target-a",
                "lines": [
                    {"index": 1, "line_type": "learner_target", "tts_text": "早晨！"},
                ],
            },
        ]
    }

    assert learner_lines_by_target(dialogues_payload)["target-a"]["tts_text"] == "你好！"
