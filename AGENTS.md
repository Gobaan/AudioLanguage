# AudioLanguage Project Instructions

AudioLanguage is a data-driven language-learning MVP. Keep the project organized around the current MVC-style boundary:

- `model`: lesson content, language data, audio/visual assets, and generated content metadata.
- `backend`: APIs, content loading, validation recording, scoring, and admin data access.
- `view`: React app orchestration, reusable components, static shell, and built assets.

Prefer backend-served JSON over hardcoded UI branches. The frontend should ask for a language, lesson set, scene type, or day parameter, then render the JSON contract it receives. When adding a language or scene, update model content and backend loading first; only change UI code if the contract needs a new interaction type.

For non-Latin beginner workflows, include and use romanized display/audio text where available. Native script can remain in source data, but the learner-facing MVP should not depend on beginners reading it before they have learned the sounds.

Keep lesson runtime JSON focused on what the app needs to render and play. Do not leak frame-generation-only fields such as mood, physical cues, or localized visual variants into the lesson payload unless the UI actually consumes them.

Validation data and recordings are local by default. Do not send learner audio or scorecard data to external services or shared servers unless the task explicitly asks for that.

Local `AGENTS.md` files override global skills for this repository. If a global skill conflicts with these instructions, follow the local project instructions.
