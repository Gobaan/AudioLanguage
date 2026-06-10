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
    """Keep phone testing honest while assets and scenes are changing quickly."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/visuals", StaticFiles(directory=str(VISUALS_DIR)), name="visuals")

app.include_router(pages.router)
app.include_router(content.router)
app.include_router(validation.router)
app.include_router(conversation.router)
