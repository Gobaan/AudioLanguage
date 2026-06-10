# Audio Asset Instructions

Use recorded/generated audio files when available. Browser speech or `audioText` playback is acceptable as an MVP fallback, but it should not replace real target audio when an asset exists.

Audio references in content should identify the exact dialogue line or prompt being played. Backward-build prompts should play the intended chunk, not the full dialogue unless the step explicitly asks for full-dialogue replay.

For non-Latin beginner languages, keep romanized `audioText` or equivalent pronunciation support available for speech synthesis and learner-facing fallback.

Voice generation should use a stable role-based cast per language. The recurring learner avatar is female unless a task explicitly changes the learner persona. Scene partners should match the character role and visual gender when known; use masculine voices for male-coded partners and feminine voices for female-coded partners. Do not use romanized learner-facing text as TTS input when a native-script `tts_text` field is available.
