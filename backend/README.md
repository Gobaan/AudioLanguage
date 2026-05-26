# Controller

The backend is the controller layer for the current app.

- `app/main.py`: FastAPI routes, request/response orchestration, and static mounts.
- `app/content/`: adapters that hydrate model data for the UI.
- `app/conversation/` and `app/speech/`: application services used by controller endpoints.

The backend should depend on the model and return view-ready payloads, but bulky content and media files should stay under `model/`.
