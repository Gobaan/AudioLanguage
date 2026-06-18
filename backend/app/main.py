from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import content, conversation, pages, validation
from app.runtime import AUDIO_DIR, STATIC_DIR, VISUALS_DIR

app = FastAPI(title="Audio Language")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_browser_cache(request, call_next):
    """Avoid stale HTML/API while allowing asset caching to reduce request queueing."""
    response = await call_next(request)
    if response.status_code >= 400:
        cache_control = "no-store, no-cache, must-revalidate, max-age=0"
    else:
        cache_control = cache_control_for_path(request.url.path)
    response.headers["Cache-Control"] = cache_control
    if cache_control.startswith("no-store"):
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    else:
        if "Pragma" in response.headers:
            del response.headers["Pragma"]
        if "Expires" in response.headers:
            del response.headers["Expires"]
    return response


def cache_control_for_path(path: str) -> str:
    if path.startswith("/static/assets/"):
        # Vite build assets are content-hashed, so immutable caching is safe.
        return "public, max-age=31536000, immutable"
    if path.startswith("/audio/") or path.startswith("/visuals/"):
        # Reuse lesson media between steps while still refreshing reasonably quickly.
        return "public, max-age=3600"
    return "no-store, no-cache, must-revalidate, max-age=0"


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/visuals", StaticFiles(directory=str(VISUALS_DIR)), name="visuals")

app.include_router(pages.router)
app.include_router(content.router)
app.include_router(validation.router)
app.include_router(conversation.router)
