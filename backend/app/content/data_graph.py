"""Backward-compatible exports for the content data graph."""

from app.content.graph_core import DataGraphError, index_by_id, public_path, read_json, required
from app.content.manifests import load_audio_assets, load_curriculum_distractors, load_distractors
from app.content.session_hydration import hydrate_line, hydrate_practice_card, list_languages, load_language_session

__all__ = [
    "DataGraphError",
    "hydrate_line",
    "hydrate_practice_card",
    "index_by_id",
    "list_languages",
    "load_audio_assets",
    "load_curriculum_distractors",
    "load_distractors",
    "load_language_session",
    "public_path",
    "read_json",
    "required",
]
