import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # /app
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    router.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@router.get("/")
def ui_home():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=500, detail="UI file missing. Create app/static/index.html")
    return FileResponse(index_path)
