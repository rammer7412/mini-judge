import json
import time
import uuid
from typing import Dict

from core.redis_client import r

def create_submission(problem_id: str, code: str) -> str:
    sid = str(uuid.uuid4())
    payload: Dict[str, object] = {
        "id": sid,
        "problem_id": problem_id,
        "code": code,
        "ts": time.time(),
    }

    # 초기 상태
    r.hset(f"sub:{sid}", mapping={"status": "QUEUED", "result": "", "detail": ""})

    # 큐 push
    r.rpush("queue:submissions", json.dumps(payload))
    return sid

def get_submission(sid: str) -> Dict[str, str]:
    key = f"sub:{sid}"
    if not r.exists(key):
        return {}
    return r.hgetall(key)
