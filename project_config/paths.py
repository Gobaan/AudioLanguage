from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepoPaths:
    root: Path
    model_dir: Path
    content_dir: Path
    assets_dir: Path
    config_dir: Path
    view_dir: Path
    static_dir: Path
    audio_sources_dir: Path
    audio_dir: Path
    prompts_audio_dir: Path
    visuals_dir: Path
    storyboards_dir: Path
    secrets_example_json: Path
    secrets_local_json: Path
    dialogues_json: Path
    prompts_json: Path

    def mp3_path(self, *, scene_id: str, line_index: int) -> Path:
        return self.audio_dir / f"{scene_id}-{line_index}.mp3"

    def prompt_mp3_path(self, *, key: str) -> Path:
        return self.prompts_audio_dir / f"{key}.mp3"


def repo_paths() -> RepoPaths:
    root = Path(__file__).resolve().parents[1]
    model_dir = root / "model"
    content_dir = model_dir / "content"
    assets_dir = model_dir / "assets"
    config_dir = root / "project_config" / "config"
    view_dir = root / "view"
    static_dir = view_dir / "static"
    audio_sources_dir = assets_dir / "audio_sources"
    audio_dir = assets_dir / "audio"
    prompts_audio_dir = audio_dir / "prompts"
    visuals_dir = assets_dir / "visuals"
    storyboards_dir = assets_dir / "storyboards"

    return RepoPaths(
        root=root,
        model_dir=model_dir,
        content_dir=content_dir,
        assets_dir=assets_dir,
        config_dir=config_dir,
        view_dir=view_dir,
        static_dir=static_dir,
        audio_sources_dir=audio_sources_dir,
        audio_dir=audio_dir,
        prompts_audio_dir=prompts_audio_dir,
        visuals_dir=visuals_dir,
        storyboards_dir=storyboards_dir,
        secrets_example_json=config_dir / "secrets.example.json",
        secrets_local_json=config_dir / "secrets.local.json",
        dialogues_json=audio_sources_dir / "dialogues.json",
        prompts_json=audio_sources_dir / "prompts.json",
    )


def repo_file_for_relative_path(project_dir: Path, relative_path: str | Path) -> Path:
    """Resolve public asset-style paths into the MVC folder layout."""
    path = Path(relative_path)
    if path.is_absolute():
        return path

    parts = path.parts
    if not parts:
        return project_dir / path

    remainder = Path(*parts[1:]) if len(parts) > 1 else Path()
    if parts[0] == "audio":
        return project_dir / "model" / "assets" / "audio" / remainder
    if parts[0] == "visuals":
        return project_dir / "model" / "assets" / "visuals" / remainder
    if parts[0] == "audio_sources":
        return project_dir / "model" / "assets" / "audio_sources" / remainder
    if parts[0] == "data":
        return project_dir / "model" / "content" / remainder
    if parts[0] == "storyboards":
        return project_dir / "model" / "assets" / "storyboards" / remainder
    if parts[0] == "static":
        return project_dir / "view" / "static" / remainder
    return project_dir / path
