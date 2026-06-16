# Script Instructions

Scripts are maintenance tools, not runtime behavior. Keep them narrow and explicit.

For token-heavy content investigation:

- Start with `python scripts/summarize_content_json.py`.
- Add `--language {code}` for one-language tasks.
- Add `--largest N` or `--min-bytes N` when searching for noisy generated files.
- Prefer existing audit scripts over opening large JSON manifests directly.

When adding a script:

- Make the filename describe the action and scope.
- Keep default behavior read-only unless the filename and arguments clearly say it writes.
- Add a focused test for parsing, filtering, or safety behavior.
- Do not make scripts silently rewrite runtime JSON unless the user explicitly asked for a migration or generation step.
