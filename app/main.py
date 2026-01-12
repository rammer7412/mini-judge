import os
import uuid
import json
import time
from typing import List, Dict

import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="Mini Judge (MVP)")

# -----------------------------------------------------------------------------
# Static UI (student web)
# -----------------------------------------------------------------------------
# app/static/index.html 을 학생용 UI로 서빙한다.
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def ui_home():
    """학생용 웹 UI 진입점"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(
            status_code=500,
            detail="UI file missing. Create app/static/index.html",
        )
    return FileResponse(index_path)


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class SubmitReq(BaseModel):
    code: str


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def problem_dir(problem_id: str) -> str:
    return os.path.join(DATA_DIR, "problems", problem_id)


def tests_dir(problem_id: str) -> str:
    return os.path.join(problem_dir(problem_id), "tests")


def problem_exists(problem_id: str) -> bool:
    """tests 폴더가 존재하면 문제 존재로 판단"""
    return os.path.isdir(tests_dir(problem_id))


def list_problem_ids() -> List[str]:
    base = os.path.join(DATA_DIR, "problems")
    if not os.path.isdir(base):
        return []
    ids: List[str] = []
    for name in sorted(os.listdir(base)):
        if problem_exists(name):
            ids.append(name)
    return ids


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}


# -----------------------------------------------------------------------------
# Problems API
# -----------------------------------------------------------------------------
@app.get("/problems")
def get_problems():
    """학생 UI에서 문제 목록을 채우기 위한 API"""
    return {"problems": list_problem_ids()}


# -----------------------------------------------------------------------------
# Submissions API
# -----------------------------------------------------------------------------
@app.post("/problems/{problem_id}/submit")
def submit(problem_id: str, req: SubmitReq):
    """
    코드 제출:
    - /data/problems/{problem_id}/tests 가 없으면 404
    - Redis에 상태를 QUEUED로 기록
    - queue:submissions 리스트에 payload를 push
    """
    if not problem_exists(problem_id):
        raise HTTPException(
            status_code=404,
            detail=f"Problem '{problem_id}' not found (missing tests folder).",
        )

    sid = str(uuid.uuid4())
    payload: Dict[str, object] = {
        "id": sid,
        "problem_id": problem_id,
        "code": req.code,
        "ts": time.time(),
    }

    # 초기 상태 저장 (worker가 status/result/detail을 업데이트한다고 가정)
    r.hset(f"sub:{sid}", mapping={"status": "QUEUED", "result": "", "detail": ""})

    # 작업 큐에 넣기
    r.rpush("queue:submissions", json.dumps(payload))

    return {"submission_id": sid}


@app.get("/submissions/{sid}")
def get_result(sid: str):
    """
    결과 조회:
    - sub:{sid} 해시를 읽어 반환
    - worker가 status/result/detail을 업데이트하면 그대로 노출됨
    """
    key = f"sub:{sid}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="submission not found")

    data = r.hgetall(key)
    return {"submission_id": sid, **data}
