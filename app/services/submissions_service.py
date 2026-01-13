import json
import time
import uuid
from typing import Any, Dict

from fastapi import HTTPException
import redis

from app.services.problems_service import problem_exists, get_problem_info

QUEUE_KEY = "queue:submissions"

def enqueue_submission(r: redis.Redis, problem_id: str, code: str, language: str) -> str:
    if not problem_exists(problem_id):
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found (missing tests folder).")

    info = get_problem_info(problem_id)
    if language not in info["languages"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    sid = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "id": sid,
        "problem_id": problem_id,
        "code": code,
        "language": language,
        "ts": time.time(),
    }

    r.hset(f"sub:{sid}", mapping={"status": "QUEUED", "result": "", "detail": ""})
    r.rpush(QUEUE_KEY, json.dumps(payload))
    return sid

def fetch_submission_result(r: redis.Redis, sid: str) -> Dict[str, Any]:
    key = f"sub:{sid}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="submission not found")
    return r.hgetall(key)
