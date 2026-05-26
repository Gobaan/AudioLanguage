# Model

The model layer owns language-learning content and media assets.

- `content/`: structured curriculum and language JSON used to hydrate sessions.
- `assets/audio/`: generated and curated MP3 files served publicly as `/audio/...`.
- `assets/audio_sources/`: legacy dialogue and prompt source JSON for audio generation.
- `assets/visuals/`: generated, draft, final, and style-reference image assets served publicly as `/visuals/...`.
- `assets/storyboards/`: storyboard source material for visual production.

Manifest paths intentionally keep public URL-style prefixes such as `audio/...` and `visuals/...`.
Runtime code resolves those paths through `audiolanguage.paths`.
