import json
import time
import uuid
from typing import Dict, Any, Optional

from core.redis_client import r


def create_submission(problem_id: str, code: str, language: str) -> str:
    sid = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "id": sid,
        "problem_id": problem_id,
        "code": code,
        "language": language,
        "ts": time.time(),
    }

    r.hset(f"sub:{sid}", mapping={"status": "QUEUED", "result": "", "detail": ""})
    r.rpush("queue:submissions", json.dumps(payload))
    return sid


def get_submission(sid: str) -> Optional[Dict[str, str]]:
    key = f"sub:{sid}"
    if not r.exists(key):
        return None
    return r.hgetall(key)
