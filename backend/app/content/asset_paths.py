from __future__ import annotations

from pathlib import Path
from typing import Any

from project_config.paths import repo_file_for_relative_path

from app.content.graph_core import public_path


def find_visual_beat(
    visual_beats: list[dict[str, Any]],
    dialogue_id: str,
    line_index: int,
) -> dict[str, Any] | None:
    for beat in visual_beats:
        if beat.get("dialogue_id") == dialogue_id and int(beat.get("line_index", -1)) == line_index:
            return beat
    return None


def existing_asset_path(project_dir: Path, path: str | None) -> str | None:
    if path and repo_file_for_relative_path(project_dir, path).exists():
        return path
    return None


def final_frame_asset_path(project_dir: Path, path: str | None, line_index: int) -> str | None:
    if path and path.startswith("visuals/final/"):
        expected_path = str(Path(path).with_name(f"frame-{line_index + 1}.png")).replace("\\", "/")
        if repo_file_for_relative_path(project_dir, expected_path).exists():
            return expected_path

    return existing_asset_path(project_dir, path)


def first_existing_asset_path(project_dir: Path, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if repo_file_for_relative_path(project_dir, candidate).exists():
            return candidate
    return None


def asset_folder_slug(value: str) -> str:
    parts = value.split("-", 1)
    if len(parts) == 2 and parts[0] in {"en", "es", "fr", "ja", "ta", "yue", "zh", "ar"}:
        return parts[1]
    return value


def resolve_line_assets(
    *,
    line: dict[str, Any],
    dialogue_id: str,
    asset_slug: str,
    visual_beats: list[dict[str, Any]],
    audio_assets: dict[tuple[str, int], str],
    project_dir: Path,
) -> tuple[str | None, str | None]:
    line_index = int(line.get("index", 0))
    beat = find_visual_beat(visual_beats, dialogue_id, line_index)
    beat_assets = beat.get("asset_paths", {}) if beat else {}
    audio_path = line.get("audio_path") or beat_assets.get("audio")
    image_path = final_frame_asset_path(project_dir, beat_assets.get("image"), line_index)

    if not audio_path:
        manifest_audio = audio_assets.get((dialogue_id, line_index))
        if manifest_audio and repo_file_for_relative_path(project_dir, manifest_audio).exists():
            audio_path = manifest_audio

    if not audio_path:
        derived_audio = f"audio/{dialogue_id}-{line_index}.mp3"
        audio_path = derived_audio if repo_file_for_relative_path(project_dir, derived_audio).exists() else None

    if not image_path:
        frame_number = line_index + 1
        image_path = first_existing_asset_path(
            project_dir,
            [
                f"visuals/final/{asset_folder_slug(dialogue_id)}/frame-{frame_number}.png",
                f"visuals/Drafts/{asset_folder_slug(dialogue_id)}/frame-{frame_number}.png",
                f"visuals/final/{asset_folder_slug(asset_slug)}/frame-{frame_number}.png",
                f"visuals/Drafts/{asset_folder_slug(asset_slug)}/frame-{frame_number}.png",
                f"visuals/{asset_slug}/frame-{frame_number}.png",
                f"visuals/final/{asset_folder_slug(dialogue_id)}/frame-{line_index}.png",
                f"visuals/Drafts/{asset_folder_slug(dialogue_id)}/frame-{line_index}.png",
                f"visuals/final/{asset_folder_slug(asset_slug)}/frame-{line_index}.png",
                f"visuals/Drafts/{asset_folder_slug(asset_slug)}/frame-{line_index}.png",
                f"visuals/{asset_slug}/frame-{line_index}.png",
            ],
        )

    return public_path(audio_path), public_path(image_path)
