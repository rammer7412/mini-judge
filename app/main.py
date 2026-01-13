from fastapi import FastAPI

from routes.ui import router as ui_router
from routes.health import router as health_router
from routes.problems import router as problems_router
from routes.submissions import router as submissions_router

app = FastAPI(title="Mini Judge (MVP)")

app.include_router(ui_router)
app.include_router(health_router)
app.include_router(problems_router)
app.include_router(submissions_router)
