from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepoPaths:
    root: Path
    audio_sources_dir: Path
    audio_dir: Path
    prompts_audio_dir: Path
    dialogues_json: Path
    prompts_json: Path

    def mp3_path(self, *, scene_id: str, line_index: int) -> Path:
        return self.audio_dir / f"{scene_id}-{line_index}.mp3"

    def prompt_mp3_path(self, *, key: str) -> Path:
        return self.prompts_audio_dir / f"{key}.mp3"


def repo_paths() -> RepoPaths:
    root = Path(__file__).resolve().parents[1]
    audio_sources_dir = root / "audio_sources"
    audio_dir = root / "audio"
    prompts_audio_dir = audio_dir / "prompts"

    return RepoPaths(
        root=root,
        audio_sources_dir=audio_sources_dir,
        audio_dir=audio_dir,
        prompts_audio_dir=prompts_audio_dir,
        dialogues_json=audio_sources_dir / "dialogues.json",
        prompts_json=audio_sources_dir / "prompts.json",
    )
