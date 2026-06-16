from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.runtime import STATIC_DIR

router = APIRouter()


@router.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/languages")
def language_selection():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/learn")
def learner_app():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/debug/recording-countdown")
def recording_countdown_preview():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/admin/validation")
def validation_admin():
    return FileResponse(str(STATIC_DIR / "index.html"))
