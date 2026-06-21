# AudioLanguage (Claude Code)

Follow `AGENTS.md` for architecture and content boundaries. This file adds token hygiene for Claude Code (which does not read `.cursorignore`).

## Do not read or search

- `view/static/assets/**` — verify frontend builds via `view/static/index.html` only
- `model/assets/**`, `model/validation/**`
- `config/client_secret_*.json`, `analysis.txt`

## Before opening content JSON

Run `python scripts/summarize_content_json.py` (optionally `--language <code>`) instead of reading broad `model/content/**/*.json`.

## Commits and checks

- Secret-scan source files only; exclude paths above
- Use focused tests (`pytest` with `-k` or one file) when possible
