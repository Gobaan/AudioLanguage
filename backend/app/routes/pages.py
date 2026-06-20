from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.runtime import STATIC_DIR

router = APIRouter()


@router.get("/gobi-home")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/service-worker.js")
def service_worker():
    return FileResponse(str(STATIC_DIR / "service-worker.js"), media_type="text/javascript")


@router.get("/learn")
def learner_app():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/debug")
@router.get("/debug/{debug_path:path}")
def debug_pages(debug_path: str = ""):
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/gobi-admin")
def validation_admin():
    return FileResponse(str(STATIC_DIR / "index.html"))
