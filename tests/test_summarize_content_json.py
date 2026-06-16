from __future__ import annotations

import json

from scripts.summarize_content_json import (
    JsonFileSummary,
    describe_json_shape,
    render_table,
    summarize_model_content_json,
)


def test_describe_json_shape_counts_top_level_collections() -> None:
    payload = {
        "dialogues": [{"id": "a"}, {"id": "b"}],
        "metadata": {"language": "ja"},
        "generated": True,
    }

    assert describe_json_shape(payload) == "dialogues[2], metadata{1}, generated:bool"


def test_summarize_model_content_json_skips_generated_ai_chunks(tmp_path) -> None:
    content_root = tmp_path / "content"
    language_dir = content_root / "languages" / "ja"
    chunk_dir = content_root / "ai_chunks"
    language_dir.mkdir(parents=True)
    chunk_dir.mkdir()
    (language_dir / "dialogues.json").write_text(
        json.dumps({"dialogues": [{"id": "first-hi"}]}),
        encoding="utf-8",
    )
    (chunk_dir / "ignored.json").write_text(json.dumps({"items": [1, 2, 3]}), encoding="utf-8")

    summaries = summarize_model_content_json(content_root)

    assert [summary.path for summary in summaries] == ["languages/ja/dialogues.json"]
    assert summaries[0].shape == "dialogues[1]"


def test_summarize_model_content_json_can_filter_to_one_language(tmp_path) -> None:
    content_root = tmp_path / "content"
    ja_dir = content_root / "languages" / "ja"
    ta_dir = content_root / "languages" / "ta"
    ja_dir.mkdir(parents=True)
    ta_dir.mkdir(parents=True)
    (ja_dir / "dialogues.json").write_text(json.dumps({"dialogues": []}), encoding="utf-8")
    (ta_dir / "dialogues.json").write_text(json.dumps({"dialogues": []}), encoding="utf-8")

    summaries = summarize_model_content_json(content_root, language="ja")

    assert [summary.path for summary in summaries] == ["languages/ja/dialogues.json"]


def test_summarize_model_content_json_can_show_largest_matches(tmp_path) -> None:
    content_root = tmp_path / "content"
    language_dir = content_root / "languages" / "ja"
    language_dir.mkdir(parents=True)
    (language_dir / "small.json").write_text(json.dumps({"items": []}), encoding="utf-8")
    (language_dir / "large.json").write_text(
        json.dumps({"items": [{"id": index} for index in range(20)]}),
        encoding="utf-8",
    )

    summaries = summarize_model_content_json(content_root, largest=1)

    assert [summary.path for summary in summaries] == ["languages/ja/large.json"]


def test_render_table_is_concise_and_contains_shape() -> None:
    table = render_table(
        [
            JsonFileSummary(
                path="languages/ja/dialogues.json",
                bytes=42,
                shape="dialogues[1]",
            )
        ]
    )

    assert "languages/ja/dialogues.json" in table
    assert "dialogues[1]" in table
