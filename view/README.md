# View

The view layer owns browser-rendered files.

- `static/`: HTML, CSS, and JavaScript served by FastAPI at `/static/...`.
- `components/`: React/TSX component scaffolds for the next view implementation.

Component text should be passed in through props so the same view can support multiple UI and learning languages.

Keep rendering concerns here. Content, audio, and visual source assets belong in `model/`.
