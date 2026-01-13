from fastapi import FastAPI

from api.router import api_router

app = FastAPI(title="Mini Judge (MVP)")
app.include_router(api_router)
