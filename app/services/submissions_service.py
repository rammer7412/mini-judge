import asyncio
import json
import time
import uuid
from typing import Any, Dict

from deps import FINAL_STATUSES, r


def normalize_submission_view(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Redis submission hash를 UI가 보기 좋은 형태로 정규화한다.

    worker.py legacy:
      status=DONE, result=<VERDICT>
    또한 status 자체가 AC/WA 등 verdict 코드로 저장되는 경우도 지원한다.
    """

    raw_status = (data.get("status") or "").upper()
    result = (data.get("result") or "").strip()
    detail = data.get("detail") or ""

    verdict_map = {
        "AC": "ACCEPTED",
        "WA": "WRONG_ANSWER",
        "TLE": "TIME_LIMIT_EXCEEDED",
        "MLE": "MEMORY_LIMIT_EXCEEDED",
        "RE": "RUNTIME_ERROR",
        "CE": "COMPILATION_ERROR",
        "IE": "INTERNAL_ERROR",
    }

    def canon(x: str) -> str:
        x = (x or "").upper()
        return verdict_map.get(x, x)

    if raw_status == "DONE":
        status = canon(result) if result else "INTERNAL_ERROR"
    else:
        status = canon(raw_status) if raw_status else "QUEUED"

    return {
        "submission_id": sid,
        "status": status,
        "result": result,
        "detail": detail,
        "raw_status": raw_status,
        "user_name": (data.get("user_name") or "").strip(),
    }


def create_submission(problem_id: str, code: str, language: str, user_name: str = "") -> str:
    sid = str(uuid.uuid4())
    ts = time.time()
    payload: Dict[str, Any] = {
        "id": sid,
        "problem_id": problem_id,
        "code": code,
        "language": language,
        "user_name": user_name,
        "ts": ts,
    }
    key = f"sub:{sid}"
    r.hset(
        key,
        mapping={
            "status": "QUEUED",
            "result": "",
            "detail": "",
            "user_name": user_name,
            "submitted_at": str(ts),
        },
    )
    r.rpush("queue:submissions", json.dumps(payload))
    return sid


def get_submission_raw(sid: str) -> Dict[str, Any]:
    return r.hgetall(f"sub:{sid}") or {}


async def wait_for_final_result(sid: str, timeout_s: float) -> Dict[str, Any]:
    """최종 상태가 될 때까지 대기하고 정규화된 결과를 반환한다."""
    key = f"sub:{sid}"
    deadline = time.time() + float(timeout_s)
    while True:
        data = r.hgetall(key) or {}
        raw_status = (data.get("status") or "").upper()

        if raw_status in FINAL_STATUSES:
            return normalize_submission_view(sid, data)

        if time.time() >= deadline:
            out = normalize_submission_view(sid, data)
            out["detail"] = (out.get("detail") or "") + "\n(timeout waiting for result)"
            return out

        await asyncio.sleep(0.2)
