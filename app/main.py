from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_TITLE)
    app.include_router(api_router)
    return app

app = create_app()
