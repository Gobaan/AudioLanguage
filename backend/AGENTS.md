# Backend Instructions

The backend is the adapter between model content and the lesson UI. Keep language-specific knowledge in JSON/content files under `model` and keep the backend responsible for loading, validating, normalizing, and serving that data.

Lesson APIs should return data the UI can render without hardcoded language branches. Add parameters for language, scene set, review/delay mode, and similar selection concerns instead of creating separate frontend builds.

When serving lessons:

- Hydrate public asset paths for frames and audio.
- Preserve lesson step order exactly as the content graph defines it.
- Use `audioText` or equivalent romanized text as the beginner-facing fallback for non-Latin languages.
- Keep transfer scenes and delayed review scenes separate from anchor lesson JSON.
- Exclude frame-generation metadata from runtime payloads unless the frontend consumes it.

Validation and admin behavior:

- Record participant, language, lesson/session, phrase, day, attempt, multiple-choice result, recording path, and scorecard state.
- Multiple retries for the same day/phrase should remain grouped as attempts, not become fake new days.
- Scorecards can rescore skipped or pending attempts.
- Admin deletion should support deleting a single recording/attempt and deleting an entire user.
- JSONL readers must tolerate empty or malformed lines where practical and keep one bad record from crashing the scorecard/admin page.

Do not send recordings to remote services during local testing. External evaluation or shared-server upload must be an explicit task.
