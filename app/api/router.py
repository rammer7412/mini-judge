from fastapi import APIRouter

from routes.health import router as health_router
from routes.ui import router as ui_router
from routes.problems import router as problems_router
from routes.submissions import router as submissions_router

api_router = APIRouter()
api_router.include_router(ui_router)
api_router.include_router(health_router)
api_router.include_router(problems_router)
api_router.include_router(submissions_router)
