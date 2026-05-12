from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SECRETS_PATH = PROJECT_DIR / "config" / "secrets.local.json"
PLACEHOLDER_VALUES = {
    "",
    "replace-with-your-openai-project-api-key",
    "sk-...",
}


def load_secrets(path: Path = DEFAULT_SECRETS_PATH, *, override: bool = False) -> dict[str, str]:
    """Load local JSON config/secrets into environment variables.

    The real secrets file is intentionally git-ignored. Environment variables
    already set by the shell or deployment platform win unless override=True.
    """
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Secrets file must contain a JSON object: {path}")

    loaded: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"Secret keys must be non-empty strings: {path}")
        if value is None:
            continue

        string_value = str(value).strip()
        if string_value in PLACEHOLDER_VALUES:
            continue
        if not override and os.environ.get(key):
            continue

        os.environ[key] = string_value
        loaded[key] = string_value

    return loaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and preview local JSON config/secrets.")
    parser.add_argument("--path", default=DEFAULT_SECRETS_PATH, type=Path)
    parser.add_argument("--override", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    loaded = load_secrets(args.path, override=args.override)
    if not args.path.exists():
        print(f"No secrets file found at {args.path}")
        return

    print(f"Loaded {len(loaded)} config values from {args.path}")
    for key in sorted(loaded):
        print(f"- {key}")


if __name__ == "__main__":
    main()
