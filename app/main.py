import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.router import api_router

app = FastAPI(title="Mini Judge (MVP)")
app.include_router(api_router)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
