# View

The view layer owns browser-rendered files.

- `app/`: React app source, lesson orchestration, and page-level state.
- `components/`: reusable React/TSX lesson components.
- `api/`: frontend API client helpers.
- `static/`: built/browser-served files served by FastAPI at `/static/...`.

Component text should be passed in through props so the same view can support multiple UI and learning languages.

Keep rendering concerns here. Content, audio, and visual source assets belong in `model/`.

Run the app source with Vite from this folder:

```powershell
npm install
npm run dev
```

Build output is written to `static/`:

```powershell
npm run build
```
