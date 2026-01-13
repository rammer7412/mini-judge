from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]  # app/
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.is_dir():
    router.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@router.get("/")
def ui_home():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=500, detail="UI file missing. Create app/static/index.html")
    return FileResponse(str(index_path))
