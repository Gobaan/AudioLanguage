from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.runtime import STATIC_DIR

router = APIRouter()


@router.get("/gobi-home")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/learn")
def learner_app():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/debug/recording-countdown")
def recording_countdown_preview():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/debug/audio")
def audio_debug_player():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/gobi-admin")
def validation_admin():
    return FileResponse(str(STATIC_DIR / "index.html"))
