"""Generate PNG visual assets from a language visual prompt manifest."""

from __future__ import annotations

import argparse
import base64
import re
from contextlib import ExitStack
from pathlib import Path

from content_assets import list_language_dirs, path_exists, read_json, write_json
from load_secrets import load_secrets


DEFAULT_MODEL = "gpt-image-1-mini"
DEFAULT_QUALITY = "low"
DEFAULT_STYLE_REFERENCE = Path("visuals/style/examples/approved-comic-panel-sumimasen-cue.png")
REFERENCE_PATTERN = re.compile(r"visuals/style/(?:characters|examples)/[\w.-]+\.png")
CHARACTER_REFERENCE_PATTERN = re.compile(r"\b[\w.-]+-reference\.png\b")


def find_reference_paths(project_dir: Path, prompt: str) -> list[Path]:
    """Return existing visual reference images named in the prompt."""
    references: list[Path] = []
    seen: set[Path] = set()

    def add_reference(relative_path: Path) -> None:
        path = project_dir / relative_path
        if path.exists() and path not in seen:
            references.append(path)
            seen.add(path)

    add_reference(DEFAULT_STYLE_REFERENCE)
    for match in REFERENCE_PATTERN.findall(prompt):
        add_reference(Path(match))
    for match in CHARACTER_REFERENCE_PATTERN.findall(prompt):
        add_reference(Path("visuals/style/characters") / match)
    return references


def build_reference_prompt(prompt: str, reference_paths: list[Path], project_dir: Path) -> str:
    reference_names = ", ".join(str(path.relative_to(project_dir)).replace("\\", "/") for path in reference_paths)
    return (
        f"{prompt}\n\n"
        "Use the attached images as binding visual references, not loose inspiration. "
        f"Attached references: {reference_names}. "
        "If the prompt contains older wording such as 'simple flat webcomic', interpret it as polished clean anime/comic rendering matching the approved reference panel. "
        "Preserve the approved panel's line quality, color treatment, character scale, and composition discipline. "
        "Preserve recurring character identity and clothing from the character references. "
        "Reject rough sketchbook style, children's-book style, thick marker outlines, decorative sketch borders, photorealism, and generic character drift."
    )


def generate_image(
    *,
    prompt: str,
    out_path: Path,
    project_dir: Path,
    model: str,
    size: str,
    quality: str,
    reference_mode: str,
    extra_reference_paths: list[Path] | None = None,
) -> list[Path]:
    from openai import OpenAI

    client = OpenAI()
    reference_paths = find_reference_paths(project_dir, prompt)
    for path in extra_reference_paths or []:
        if path.exists() and path not in reference_paths:
            reference_paths.append(path)

    if reference_mode != "never" and reference_paths:
        with ExitStack() as stack:
            image_files = [stack.enter_context(path.open("rb")) for path in reference_paths]
            edit_args = {
                "model": model,
                "image": image_files,
                "prompt": build_reference_prompt(prompt, reference_paths, project_dir),
                "n": 1,
                "size": size,
                "quality": quality,
                "output_format": "png",
            }
            if model != "gpt-image-1-mini":
                edit_args["input_fidelity"] = "high"
            response = client.images.edit(
                **edit_args,
            )
    elif reference_mode == "always":
        raise RuntimeError("Reference mode is 'always', but no reference images were found.")
    else:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            output_format="png",
        )

    image_base64 = response.data[0].b64_json
    if not image_base64:
        raise RuntimeError("Image API returned no base64 PNG data")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(image_base64))
    return reference_paths


def generate_language(
    *,
    data_dir: Path,
    project_dir: Path,
    language: str,
    model: str,
    size: str,
    quality: str,
    reference_mode: str,
    force: bool,
    limit: int | None,
    dialogue_ids: set[str] | None,
    prompt_ids: set[str] | None,
    include_previous_frame: bool,
    explicit_reference_paths: list[Path],
) -> tuple[int, int]:
    manifest_path = data_dir / "languages" / language / "visual_prompts.json"
    manifest = read_json(manifest_path)
    created = 0
    skipped = 0
    previous_frames = {
        (item.get("dialogue_id"), item.get("line_index")): project_dir / item["image_path"]
        for item in manifest.get("prompts", [])
        if "image_path" in item
    }

    for item in manifest.get("prompts", []):
        if dialogue_ids and item.get("dialogue_id") not in dialogue_ids:
            continue
        if prompt_ids and item.get("id") not in prompt_ids:
            continue
        if limit is not None and created >= limit:
            break

        image_path = item["image_path"]
        if path_exists(project_dir, image_path) and not force:
            item["status"] = "generated"
            skipped += 1
            continue

        extra_reference_paths: list[Path] = []
        extra_reference_paths.extend(explicit_reference_paths)
        previous_key = (item.get("dialogue_id"), item.get("line_index", 0) - 1)
        previous_frame = previous_frames.get(previous_key)
        if include_previous_frame and previous_frame and previous_frame.exists():
            extra_reference_paths.append(previous_frame)

        reference_paths = generate_image(
            prompt=item["localized_prompt"],
            out_path=project_dir / image_path,
            project_dir=project_dir,
            model=model,
            size=size,
            quality=quality,
            reference_mode=reference_mode,
            extra_reference_paths=extra_reference_paths,
        )
        item["status"] = "generated"
        item["reference_images"] = [
            str(path.relative_to(project_dir)).replace("\\", "/") for path in reference_paths
        ]
        created += 1
        print(f"{language}: generated {image_path} with {len(reference_paths)} reference image(s)")

    write_json(manifest_path, manifest)
    return created, skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--project-dir", default=".", type=Path)
    parser.add_argument("--language", action="append", help="Language code to generate. Repeatable.")
    parser.add_argument("--dialogue-id", action="append", help="Only generate this dialogue id. Repeatable.")
    parser.add_argument("--prompt-id", action="append", help="Only generate this visual prompt id. Repeatable.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default=DEFAULT_QUALITY)
    parser.add_argument(
        "--reference-mode",
        choices=["auto", "always", "never"],
        default="auto",
        help="Use attached style/character image references when available.",
    )
    parser.add_argument(
        "--no-previous-frame",
        action="store_true",
        help="Do not attach the previous generated frame as a continuity reference.",
    )
    parser.add_argument(
        "--reference-image",
        action="append",
        default=[],
        type=Path,
        help="Attach an extra image reference, such as the current draft being revised. Repeatable.",
    )
    parser.add_argument("--limit", type=int, help="Maximum files to create per language.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_secrets()

    data_dir = args.data_dir.resolve()
    project_dir = args.project_dir.resolve()
    languages = args.language or [path.name for path in list_language_dirs(data_dir)]
    explicit_reference_paths = [
        path if path.is_absolute() else project_dir / path for path in args.reference_image
    ]

    for language in languages:
        created, skipped = generate_language(
            data_dir=data_dir,
            project_dir=project_dir,
            language=language,
            model=args.model,
            size=args.size,
            quality=args.quality,
            reference_mode=args.reference_mode,
            force=args.force,
            limit=args.limit,
            dialogue_ids=set(args.dialogue_id) if args.dialogue_id else None,
            prompt_ids=set(args.prompt_id) if args.prompt_id else None,
            include_previous_frame=not args.no_previous_frame,
            explicit_reference_paths=explicit_reference_paths,
        )
        print(f"{language}: created {created}, skipped {skipped}")


if __name__ == "__main__":
    main()
