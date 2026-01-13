from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers import problems, submissions


app = FastAPI(title="Mini Judge (MVP)")


# -----------------------------------------------------------------------------
# Static UI
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def ui_home():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=500, detail="UI file missing. Create app/static/index.html")
    return FileResponse(str(index_path))


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}


# -----------------------------------------------------------------------------
# API Routers
# -----------------------------------------------------------------------------
app.include_router(problems.router)
app.include_router(submissions.router)
