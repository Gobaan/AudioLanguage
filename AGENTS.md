# AudioLanguage Project Instructions

AudioLanguage is a data-driven language-learning MVP. Keep the project organized around the current MVC-style boundary:

- `model`: lesson content, language data, audio/visual assets, and generated content metadata.
- `backend`: APIs, content loading, validation recording, scoring, and admin data access.
- `view`: React app orchestration, reusable components, static shell, and built assets.

Prefer backend-served JSON over hardcoded UI branches. The frontend should ask for a language, lesson set, scene type, or day parameter, then render the JSON contract it receives. When adding a language or scene, update model content and backend loading first; only change UI code if the contract needs a new interaction type.

For non-Latin beginner workflows, include and use romanized display/audio text where available. Native script can remain in source data, but the learner-facing MVP should not depend on beginners reading it before they have learned the sounds.

Keep lesson runtime JSON focused on what the app needs to render and play. Do not leak frame-generation-only fields such as mood, physical cues, or localized visual variants into the lesson payload unless the UI actually consumes them.

Validation data and recordings are local by default. Do not send learner audio or scorecard data to external services or shared servers unless the task explicitly asks for that.

## Agent Context Hygiene

This repository has large generated content and media manifests. Preserve token budget by finding the narrow file set before reading content.

- Use `python scripts/summarize_content_json.py` before opening broad `model/content/**/*.json` files.
- Use `python scripts/summarize_content_json.py --language ja` when a task is scoped to one language.
- Use `python scripts/summarize_content_json.py --largest 8` when looking for the noisiest files.
- Prefer targeted `rg` searches by target id, dialogue id, language, or route name.
- Do not dump generated manifests, media directories, validation recordings, build assets, or broad `rg "frame|audio|line"` output into chat unless the task specifically requires it.
- Read `AGENTS.md` files near the subsystem first, then inspect only the 1-3 files needed for the change.
- For content edits, inspect the specific language file and target/dialogue/card ids involved rather than every language.
- Treat `model/assets/**`, `model/validation/**`, `view/static/assets/**`, and temporary scratch folders as high-noise unless the task is directly about assets, validation data, or deployment bundles.
- Prefer short verification commands that assert behavior over broad full-suite runs unless the touched area requires the full suite.

Local `AGENTS.md` files override global skills for this repository. If a global skill conflicts with these instructions, follow the local project instructions.
