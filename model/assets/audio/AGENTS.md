# Audio Asset Instructions

Use recorded/generated audio files when available. Browser speech or `audioText` playback is acceptable as an MVP fallback, but it should not replace real target audio when an asset exists.

Audio references in content should identify the exact dialogue line or prompt being played. Backward-build prompts should play the intended chunk, not the full dialogue unless the step explicitly asks for full-dialogue replay.

For non-Latin beginner languages, keep romanized `audioText` or equivalent pronunciation support available for speech synthesis and learner-facing fallback.

Voice generation should use a stable character-based cast per language, not a generic male/female split and not broad role-only guessing. Resolve each spoken line to the visual character through `scripts/character_cast.py`, then use that character's voice profile from `scripts/voice_registry.py`.

The recurring learner avatar is always the `learner` character unless a task explicitly changes the learner persona. Scene partners should keep the same `character_id`, `visual_reference`, and voice across anchor, transfer, and delayed scenes when the same visual character is used.

Every generated audio manifest row should include `character_id`, `visual_reference`, `voice_id`, and `voice_profile`. Two lines with identical text may still need different MP3 files if different characters speak them. Do not reuse an MP3 from another character just because the words match.

Do not use romanized learner-facing text as TTS input when a native-script `tts_text` field is available.
