"""Build per-language image and video prompt manifests from the content graph."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from content_assets import (
    list_language_dirs,
    load_curriculum,
    load_language_data,
    path_exists,
    relative_posix,
    write_json,
)


LINE_TYPE_INTENTIONS = {
    "world_opener": "The scene partner opens the exchange and creates the need for the learner response.",
    "learner_target": "The learner-character needs to express the target intention clearly.",
    "world_response": "The scene partner responds so the learner can infer whether the attempt worked.",
    "learner_close": "The learner-character closes the exchange politely.",
    "world_action": "A silent setup beat shows the situation and the learner-character's need.",
}


PARTNER_REFERENCE_BY_ROLE = {
    "barista": "vendor-reference.png",
    "cashier": "vendor-reference.png",
    "class_partner": "friend-reference.png",
    "classmate": "friend-reference.png",
    "conversation_partner": "friend-reference.png",
    "friend": "friend-reference.png",
    "host": "staff-reference.png",
    "local": "local-helper-reference.png",
    "neighbor": "friend-reference.png",
    "pharmacist": "pharmacist-reference.png",
    "receptionist": "staff-reference.png",
    "server": "vendor-reference.png",
    "shopkeeper": "vendor-reference.png",
    "staff": "staff-reference.png",
    "station_helper": "staff-reference.png",
    "vendor": "vendor-reference.png",
}


TURN_OVERLAY_BY_LINE_TYPE = {
    "world_opener": "Do not draw speech bubbles. The app will overlay the partner turn bubble.",
    "learner_target": "Do not draw speech bubbles. The app will overlay the learner turn bubble.",
    "world_response": "Do not draw speech bubbles. The app will overlay the partner response bubble.",
    "learner_close": "Do not draw speech bubbles. The app will overlay the learner closing bubble.",
}


def summarize_gestures(function: dict[str, Any], meaning_units: list[str]) -> str:
    grammar = function.get("gesture_grammar", {})
    cues: list[str] = []
    for unit in meaning_units:
        unit_cues = grammar.get(unit)
        if unit_cues:
            cues.append(f"{unit}: {', '.join(unit_cues)}")
    return "; ".join(cues)


def partner_reference_for(scene: dict[str, Any], line: dict[str, Any]) -> str:
    speaker_role = str(line.get("speaker_role", ""))
    if speaker_role == "learner":
        for character in scene.get("characters", []):
            role = str(character.get("role", ""))
            if role != "learner":
                return PARTNER_REFERENCE_BY_ROLE.get(role, "staff-reference.png")
        return "staff-reference.png"
    return PARTNER_REFERENCE_BY_ROLE.get(speaker_role, "staff-reference.png")


def target_meaning(targets_by_id: dict[str, Any], dialogue: dict[str, Any], line: dict[str, Any]) -> str:
    target_id = line.get("target_id") or dialogue.get("target_id")
    target = targets_by_id.get(target_id or "")
    if not target:
        return ""
    return target.get("display_meaning", "")


def line_intention(
    function: dict[str, Any],
    targets_by_id: dict[str, Any],
    dialogue: dict[str, Any],
    line: dict[str, Any],
) -> str:
    line_type = line.get("line_type", "")
    base = LINE_TYPE_INTENTIONS.get(line_type, "Show the conversational beat clearly.")
    if line_type == "learner_target":
        meaning = target_meaning(targets_by_id, dialogue, line)
        if meaning:
            return f"{base} Communicative function: {function.get('name', '')}. Intention: {meaning}."
    units = ", ".join(line.get("meaning_units", []))
    if units:
        return f"{base} Meaning cues: {units}."
    return base


def prompt_for(
    language: str,
    function: dict[str, Any],
    scene: dict[str, Any],
    targets_by_id: dict[str, Any],
    dialogue: dict[str, Any],
    line: dict[str, Any],
) -> tuple[str, str]:
    characters = "; ".join(
        f"{character.get('role')}: {character.get('description')}"
        for character in scene.get("characters", [])
    )
    props = ", ".join(scene.get("props", []))
    physical_cue = scene.get("physical_cues", {}).get(line.get("line_type", ""), "")
    gestures = summarize_gestures(function, line.get("meaning_units", []))
    intention = line_intention(function, targets_by_id, dialogue, line)
    localized_environment = scene.get("localized_variants", {}).get(language, scene.get("environment", ""))
    partner_reference = partner_reference_for(scene, line)
    turn_overlay_rule = TURN_OVERLAY_BY_LINE_TYPE.get(
        line.get("line_type", ""),
        "Do not draw speech bubbles. The app will overlay turn-taking UI.",
    )

    learner_turn_direction = ""
    if line.get("speaker_role") == "learner":
        learner_turn_direction = (
            "Learner action: the learner should direct gaze, face angle, and gesture toward the scene partner, "
            "not toward the viewer or camera, unless the scene specifically requires addressing the viewer."
        )

    dialogue_scene = len(scene.get("characters", [])) >= 2
    framing = (
        "Landscape 3:2 polished clean anime/comic panel matching visuals/style/examples/approved-comic-panel-sumimasen-cue.png."
        if dialogue_scene
        else "Square polished clean anime/comic panel matching visuals/style/examples/approved-comic-panel-sumimasen-cue.png."
    )
    framing_detail = (
        "Use landscape side-view staging for this two-person dialogue scene so both people, the environment, and their sightlines fit naturally."
        if dialogue_scene
        else "Use compact square staging for this simple visual beat."
    )

    shared_prompt = "\n\n".join(
        part
        for part in [
            framing,
            "Use crisp controlled linework, warm flat colors, light environmental detail, readable human faces, and mobile-safe composition.",
            "Use character references: visuals/style/characters/learner-reference.png for the recurring female learner avatar "
            f"and visuals/style/characters/{partner_reference} for the scene partner archetype.",
            f"Scene: {scene.get('environment', 'natural everyday setting')}.",
            scene.get("description", ""),
            f"Mood: {scene.get('mood', 'natural and conversational')}.",
            f"Characters: {characters}." if characters else "",
            f"Visible props: {props}." if props else "",
            f"Show this beat: {intention}",
            f"Body language: {physical_cue}." if physical_cue else "",
            f"Gesture cues: {gestures}." if gestures else "",
            learner_turn_direction,
            framing_detail,
            "Composition: natural candid comic-scene composition, not a character showcase. Characters should feel placed inside a real room with believable distance, furniture, doorway, counters, and sightlines. Avoid oversized foreground portraits. Avoid having characters face the camera unless the scene requires it. Camera at human eye level with medium-wide framing and enough room context to understand where both people are.",
            turn_overlay_rule,
            "Mobile-safe composition: keep active characters, faces, hands, speech bubbles, and meaning cues "
            "in the central 70% of the frame and above the lower 25% so app controls do not hide them.",
            "No subtitles, no translations, no target-language text, no source-language text, no readable dialogue text, no speech bubbles, no captions, no logos.",
            "The image must teach meaning through setting, faces, gaze, objects, gesture, and the social result.",
            "Reject rough sketchbook style, children's-book style, thick marker outlines, decorative sketch borders, photorealism, app screenshot layouts, close-up portraits, sticker poses, reaction shots, character reference sheets, staged two-character poses, and generic character drift.",
        ]
        if part
    )
    localized_prompt = "\n\n".join(
        [
            shared_prompt,
            f"Localize the environment as: {localized_environment}.",
            "Use culturally ordinary clothing, posture, and interpersonal distance for the scene context, but keep the communicative function language-neutral unless the scene explicitly requires a local cultural variant.",
            "Do not render the dialogue, phonetics, translations, captions, signs, or labels as written text.",
        ]
    )
    return shared_prompt, localized_prompt


def build_manifest(data_dir: Path, project_dir: Path, language: str) -> dict[str, Any]:
    functions_by_id, scenes_by_id = load_curriculum(data_dir)
    targets_payload, dialogues_payload = load_language_data(data_dir, language)
    targets_by_id = {item["id"]: item for item in targets_payload.get("targets", [])}
    prompts: list[dict[str, Any]] = []

    for dialogue in dialogues_payload.get("dialogues", []):
        function = functions_by_id.get(dialogue.get("function_id"), {})
        scene = scenes_by_id.get(dialogue.get("scene_id"), {})
        for line in dialogue.get("lines", []):
            shared_prompt, localized_prompt = prompt_for(
                language, function, scene, targets_by_id, dialogue, line
            )
            image_path = relative_posix(
                Path("visuals")
                / "generated"
                / language
                / dialogue["id"]
                / f"frame-{line['index']}.png"
            )
            image_prompt_path = relative_posix(
                Path("visuals")
                / "generated"
                / language
                / dialogue["id"]
                / "prompts"
                / f"frame-{line['index']}.txt"
            )
            video_prompt_path = relative_posix(
                Path("visuals")
                / "generated"
                / language
                / dialogue["id"]
                / "prompts"
                / f"beat-{line['index']}.txt"
            )
            prompts.append(
                {
                    "id": f"{dialogue['id']}-frame-{line['index']}",
                    "language": language,
                    "dialogue_id": dialogue["id"],
                    "dialogue_type": dialogue.get("type", ""),
                    "function_id": dialogue.get("function_id", ""),
                    "target_id": line.get("target_id") or dialogue.get("target_id", ""),
                    "scene_id": dialogue.get("scene_id", ""),
                    "line_index": line["index"],
                    "line_type": line.get("line_type", ""),
                    "speaker_role": line.get("speaker_role", ""),
                    "meaning_units": line.get("meaning_units", []),
                    "visual_intention": line_intention(function, targets_by_id, dialogue, line),
                    "shared_prompt": shared_prompt,
                    "localized_prompt": localized_prompt,
                    "image_prompt_path": image_prompt_path,
                    "video_prompt_path": video_prompt_path,
                    "image_path": image_path,
                    "status": "generated" if path_exists(project_dir, image_path) else "needs_generation",
                    "native_review_required": bool(
                        dialogues_payload.get("native_review_status") == "needs_native_review"
                    ),
                }
            )

    return {
        "language": language,
        "display_name": dialogues_payload.get("display_name", language),
        "script": dialogues_payload.get("script", ""),
        "source": [
            "data/curriculum/functions.json",
            "data/curriculum/scenes.json",
            f"data/languages/{language}/targets.json",
            f"data/languages/{language}/dialogues.json",
        ],
        "asset_type": "visual_prompts",
        "status_values": ["needs_generation", "generated", "reviewed"],
        "prompts": prompts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to build. Repeatable.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]

    for language in languages:
        manifest = build_manifest(data_dir, project_dir, language)
        output_path = data_dir / "languages" / language / "visual_prompts.json"
        write_json(output_path, manifest)
        generated = sum(1 for item in manifest["prompts"] if item["status"] == "generated")
        print(f"{language}: wrote {len(manifest['prompts'])} visual prompts ({generated} generated)")


if __name__ == "__main__":
    main()
