"""Generate ~256KB JPEG variants for lesson visual frames."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


TARGET_BYTES = 256 * 1024
FRAME_PATTERN = "frame-*.png"
OUTPUT_SUFFIX = "-256kb.jpg"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default="model/assets/visuals",
        help="Root folder to scan for frame PNG files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be generated without writing files.",
    )
    return parser.parse_args()


def find_best_variant(image: Image.Image, target_bytes: int) -> tuple[Image.Image, int, int]:
    best: tuple[int, Image.Image, int] | None = None
    scales = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    for scale in scales:
        if scale == 1.0:
            candidate = image
        else:
            width = max(1, int(image.width * scale))
            height = max(1, int(image.height * scale))
            candidate = image.resize((width, height), Image.Resampling.LANCZOS)

        for quality in range(5, 96):
            tmp_path = Path("tmp/.visual-256kb-temp.jpg")
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            candidate.save(tmp_path, format="JPEG", quality=quality, optimize=True, progressive=True)
            size = tmp_path.stat().st_size
            tmp_path.unlink(missing_ok=True)
            if size <= target_bytes:
                if best is None or size > best[0]:
                    best = (size, candidate.copy(), quality)
            else:
                break

        if best is not None:
            break

    if best is None:
        fallback = image.resize(
            (max(1, image.width // 2), max(1, image.height // 2)),
            Image.Resampling.LANCZOS,
        )
        return fallback, 20, -1

    size, best_image, best_quality = best
    return best_image, best_quality, size


def output_path_for(frame_path: Path) -> Path:
    return frame_path.with_name(f"{frame_path.stem}{OUTPUT_SUFFIX}")


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    frame_paths = sorted(path for path in root.rglob(FRAME_PATTERN) if OUTPUT_SUFFIX not in path.name)
    if not frame_paths:
        print(f"No frame PNG files found under {root}")
        return

    generated = 0
    for frame_path in frame_paths:
        out_path = output_path_for(frame_path)
        with Image.open(frame_path) as source:
            rgb = source.convert("RGB")
            variant, quality, expected_size = find_best_variant(rgb, TARGET_BYTES)
            if args.dry_run:
                print(
                    f"[dry-run] {out_path.as_posix()} quality={quality} "
                    f"size<={TARGET_BYTES} expected={expected_size}"
                )
                continue

            out_path.parent.mkdir(parents=True, exist_ok=True)
            variant.save(out_path, format="JPEG", quality=quality, optimize=True, progressive=True)
            print(
                f"generated={out_path.as_posix()} "
                f"bytes={out_path.stat().st_size} quality={quality} "
                f"resolution={variant.width}x{variant.height}"
            )
            generated += 1

    if not args.dry_run:
        print(f"generated_count={generated}")


if __name__ == "__main__":
    main()
