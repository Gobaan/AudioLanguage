"""Generate active-speaker speech bubble placement metadata for visual beats."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from content_assets import DEFAULT_DATA_DIR, list_language_dirs, read_json, write_json
from project_config.paths import repo_file_for_relative_path


@dataclass(frozen=True)
class NormalizedBox:
    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def upper_y(self) -> float:
        return self.y + self.height * 0.18

    def as_payload(self) -> dict[str, float]:
        return {
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "width": round(self.width, 3),
            "height": round(self.height, 3),
            "confidence": round(self.confidence, 3),
        }


@dataclass(frozen=True)
class BubbleCandidate:
    anchor_x: float
    anchor_y: float
    side: str
    score: float
    tip_position: str = "center"
    tip_tilt: str = "none"
    rotation_degrees: float = 0.0


BUBBLE_SAFE_MIN_X = 0.08
BUBBLE_SAFE_MAX_X = 0.92
BUBBLE_SAFE_MIN_Y = 0.08
BUBBLE_SAFE_MAX_Y = 0.72


def bubble_kind_for_line(line: dict[str, Any]) -> str:
    if line.get("speaker_role") == "learner" or line.get("line_type") == "learner_target":
        return "mic"
    return "speaker"


def fallback_speaker_box(kind: str) -> NormalizedBox:
    if kind == "mic":
        return NormalizedBox(x=0.25, y=0.24, width=0.2, height=0.48, confidence=0.35)
    return NormalizedBox(x=0.55, y=0.24, width=0.2, height=0.48, confidence=0.35)


def select_speaker_box(kind: str, boxes: list[NormalizedBox]) -> tuple[NormalizedBox, str]:
    if not boxes:
        return fallback_speaker_box(kind), "fallback"

    expected_x = fallback_speaker_box(kind).center_x
    selected = max(
        boxes,
        key=lambda box: box.confidence - abs(box.center_x - expected_x) * 0.75,
    )
    return selected, "detected"


def place_bubble(speaker_box: NormalizedBox, all_boxes: list[NormalizedBox]) -> BubbleCandidate:
    cx = speaker_box.center_x
    top = speaker_box.upper_y
    is_left_speaker = cx < 0.5
    inward_x = min(cx + 0.1, 0.48) if is_left_speaker else max(cx - 0.1, 0.52)
    inward_tip_position = "left" if is_left_speaker else "right"
    inward_tip_tilt = "left" if is_left_speaker else "right"
    inward_rotation_degrees = -12.0 if is_left_speaker else 12.0
    candidates = [
        BubbleCandidate(
            inward_x,
            top - 0.12,
            "bottom",
            4.6,
            inward_tip_position,
            inward_tip_tilt,
            inward_rotation_degrees,
        ),
        BubbleCandidate(cx, top - 0.12, "bottom", 4.0, "center", "none"),
        BubbleCandidate(speaker_box.x + speaker_box.width * 0.18, top - 0.08, "bottom-right", 3.4, "right", "right", 12.0),
        BubbleCandidate(speaker_box.x + speaker_box.width * 0.82, top - 0.08, "bottom-left", 3.4, "left", "left", -12.0),
        BubbleCandidate(speaker_box.x - 0.08, top + 0.04, "right", 2.6, "right", "right", 12.0),
        BubbleCandidate(speaker_box.x + speaker_box.width + 0.08, top + 0.04, "left", 2.6, "left", "left", -12.0),
    ]
    return max((score_candidate(candidate, all_boxes) for candidate in candidates), key=lambda item: item.score)


def score_candidate(candidate: BubbleCandidate, boxes: list[NormalizedBox]) -> BubbleCandidate:
    score = candidate.score
    if not (BUBBLE_SAFE_MIN_X <= candidate.anchor_x <= BUBBLE_SAFE_MAX_X):
        score -= 3.0
    if not (BUBBLE_SAFE_MIN_Y <= candidate.anchor_y <= BUBBLE_SAFE_MAX_Y):
        score -= 3.0
    if 0.18 <= candidate.anchor_x <= 0.82:
        score += 0.7
    if candidate.anchor_y <= 0.28:
        score += 0.5
    if candidate.anchor_y > 0.75:
        score -= 4.0
    for box in boxes:
        if overlaps_box(candidate.anchor_x, candidate.anchor_y, box):
            score -= 1.7
    return BubbleCandidate(
        anchor_x=clamp(candidate.anchor_x, BUBBLE_SAFE_MIN_X, BUBBLE_SAFE_MAX_X),
        anchor_y=clamp(candidate.anchor_y, BUBBLE_SAFE_MIN_Y, BUBBLE_SAFE_MAX_Y),
        side=candidate.side,
        score=score,
        tip_position=candidate.tip_position,
        tip_tilt=candidate.tip_tilt,
        rotation_degrees=candidate.rotation_degrees,
    )


def overlaps_box(anchor_x: float, anchor_y: float, box: NormalizedBox) -> bool:
    bubble_half_size = 0.07
    bubble_left = anchor_x - bubble_half_size
    bubble_right = anchor_x + bubble_half_size
    bubble_top = anchor_y - bubble_half_size
    bubble_bottom = anchor_y + bubble_half_size
    box_left = box.x
    box_right = box.x + box.width
    box_top = box.y
    box_bottom = box.y + box.height
    return not (
        bubble_right < box_left
        or bubble_left > box_right
        or bubble_bottom < box_top
        or bubble_top > box_bottom
    )


def speech_bubble_for_line(
    line: dict[str, Any],
    detected_boxes: list[NormalizedBox],
) -> tuple[dict[str, Any], list[dict[str, float]]]:
    kind = bubble_kind_for_line(line)
    speaker_box, source = select_speaker_box(kind, detected_boxes)
    boxes_for_scoring = detected_boxes or [speaker_box]
    placement = place_bubble(speaker_box, boxes_for_scoring)
    return (
        {
            "kind": kind,
            "anchorX": round(placement.anchor_x, 3),
            "anchorY": round(placement.anchor_y, 3),
            "side": placement.side,
            "tipPosition": placement.tip_position,
            "tipTilt": placement.tip_tilt,
            "rotationDegrees": round(placement.rotation_degrees, 1),
            "source": source,
        },
        [box.as_payload() for box in detected_boxes],
    )


def detect_character_boxes(image_path: Path) -> list[NormalizedBox]:
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError:
        return []

    image = cv2.imread(str(image_path))
    if image is None:
        return []

    image_height, image_width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    face_detector = cv2.CascadeClassifier(str(cascade_path))
    if face_detector.empty():
        return []

    boxes = []
    for x, y, width, height in face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4):
        boxes.append(
            NormalizedBox(
                x=float(x) / image_width,
                y=float(y) / image_height,
                width=float(width) / image_width,
                height=float(height) / image_height,
                confidence=0.8,
            )
        )
    return boxes


def update_language(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    force: bool,
) -> int:
    language_dir = data_dir / "languages" / language
    visual_path = language_dir / "visual_beats.json"
    dialogues_path = language_dir / "dialogues.json"
    visual_payload = read_json(visual_path)
    dialogues_payload = read_json(dialogues_path)
    lines_by_key = {
        (dialogue["id"], int(line["index"])): line
        for dialogue in dialogues_payload.get("dialogues", [])
        for line in dialogue.get("lines", [])
    }

    updated = 0
    for beat in visual_payload.get("visual_beats", []):
        if beat.get("speech_bubble") and not force:
            continue
        line = lines_by_key.get((beat.get("dialogue_id"), int(beat.get("line_index", -1))))
        if line is None:
            continue
        image_path = beat.get("asset_paths", {}).get("image")
        detected_boxes = detect_character_boxes(repo_file_for_relative_path(project_dir, image_path)) if image_path else []
        speech_bubble, candidate_payload = speech_bubble_for_line(line, detected_boxes)
        beat["speech_bubble"] = speech_bubble
        beat["character_candidates"] = candidate_payload
        updated += 1

    if updated:
        write_json(visual_path, visual_payload)
    return updated


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to update. Repeatable.")
    parser.add_argument("--force", action="store_true", help="Replace existing speech bubble metadata.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]

    total = 0
    for language in languages:
        updated = update_language(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
            force=args.force,
        )
        total += updated
        print(f"{language}: updated {updated} visual beats")
    print(f"Updated {total} speech bubble placements.")


if __name__ == "__main__":
    main()
