import os
import uuid
import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR = os.getenv("DATA_DIR", "/data")
DEFAULT_SAMPLE_COUNT = int(os.getenv("DEFAULT_SAMPLE_COUNT", "3"))

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="Mini Judge (MVP)")


# -----------------------------------------------------------------------------
# Submission status
# -----------------------------------------------------------------------------
FINAL_STATUSES = {
    "ACCEPTED",
    "WRONG_ANSWER",
    "TIME_LIMIT_EXCEEDED",
    "MEMORY_LIMIT_EXCEEDED",
    "RUNTIME_ERROR",
    "COMPILATION_ERROR",
    "INTERNAL_ERROR",
    # worker legacy terminal status
    "DONE",
}

# -----------------------------------------------------------------------------
# Static UI
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def ui_home():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=500, detail="UI file missing. Create app/static/index.html")
    return FileResponse(str(index_path))


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class SubmitReq(BaseModel):
    code: str
    language: Optional[str] = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def problems_root() -> Path:
    return Path(DATA_DIR) / "problems"


def problem_path(problem_id: str) -> Path:
    return problems_root() / problem_id


def tests_dir(problem_id: str) -> Path:
    return problem_path(problem_id) / "tests"


def problem_exists(problem_id: str) -> bool:
    return tests_dir(problem_id).is_dir()


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def safe_read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def list_problem_ids() -> List[str]:
    root = problems_root()
    if not root.is_dir():
        return []
    out: List[str] = []
    for p in sorted(root.iterdir(), key=lambda x: x.name):
        if p.is_dir() and (p / "tests").is_dir():
            out.append(p.name)
    return out


def normalize_meta(problem_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    meta.json을 표준 형태로 맞춘다 (없으면 기본값)
    """
    title = meta.get("title") or problem_id
    time_limit_ms = int(meta.get("time_limit_ms") or 1000)
    memory_limit_mb = int(meta.get("memory_limit_mb") or 256)

    languages = meta.get("languages")
    if not isinstance(languages, list) or not languages:
        languages = ["python3"]

    default_language = meta.get("default_language") or languages[0]

    # 샘플 개수(meta.json 우선)
    sample_count = meta.get("sample_count")
    try:
        sample_count = int(sample_count) if sample_count is not None else DEFAULT_SAMPLE_COUNT
    except Exception:
        sample_count = DEFAULT_SAMPLE_COUNT

    # 너무 큰 값 방지(실수로 999 같은 거 넣는 경우)
    if sample_count < 0:
        sample_count = 0
    if sample_count > 20:
        sample_count = 20

    return {
        "id": meta.get("id") or problem_id,
        "title": title,
        "time_limit_ms": time_limit_ms,
        "memory_limit_mb": memory_limit_mb,
        "languages": languages,
        "default_language": default_language,
        "sample_count": sample_count,
    }


def load_samples_from_tests(problem_id: str, sample_count: int) -> List[Dict[str, str]]:
    """
    tests 폴더의 1.in/1.out, 2.in/2.out ... 을 sample_count 개까지 읽는다.
    """
    tdir = tests_dir(problem_id)
    if not tdir.is_dir() or sample_count <= 0:
        return []

    samples: List[Dict[str, str]] = []
    for i in range(1, sample_count + 1):
        inp = tdir / f"{i}.in"
        out = tdir / f"{i}.out"
        if inp.is_file() and out.is_file():
            samples.append(
                {
                    "name": str(i),
                    "input": safe_read_text(inp).rstrip("\n"),
                    "output": safe_read_text(out).rstrip("\n"),
                }
            )
        else:
            # 중간 번호가 없으면 거기서 멈춤
            break
    return samples


def get_problem_info(problem_id: str) -> Dict[str, Any]:
    """
    문제 상세:
    - meta.json: 제목/제한/언어/샘플개수
    - statement.md 또는 statement.txt: 문제 설명
    - samples: tests의 1..N 샘플 표시
    """
    pdir = problem_path(problem_id)
    if not (pdir / "tests").is_dir():
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    meta_raw = safe_read_json(pdir / "meta.json")
    meta = normalize_meta(problem_id, meta_raw)

    statement = safe_read_text(pdir / "statement.md")
    if not statement:
        statement = safe_read_text(pdir / "statement.txt")
    if not statement:
        statement = "(no statement) Create data/problems/<id>/statement.md"

    samples = load_samples_from_tests(problem_id, meta["sample_count"])

    return {
        "id": problem_id,
        "title": meta["title"],
        "time_limit_ms": meta["time_limit_ms"],
        "memory_limit_mb": meta["memory_limit_mb"],
        "languages": meta["languages"],
        "default_language": meta["default_language"],
        "sample_count": meta["sample_count"],
        "statement": statement,
        "samples": samples,
    }




def normalize_submission_view(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redis에 저장된 submission hash를 UI/클라이언트가 쓰기 좋은 형태로 정규화.

    worker.py가 status=DONE, result=<VERDICT> 형태로 저장하는 구버전도 지원한다.

    반환 포맷은 항상:
      {submission_id, status, result, detail, raw_status}

    - status: UI가 표시할 "정규화된 상태"(ACCEPTED/WRONG_ANSWER/...)
    - result: worker가 준 원본 verdict 코드(AC/WA/TLE/RE 등) 또는 메시지
    """
    raw_status = (data.get("status") or "").upper()
    result = (data.get("result") or "").strip()
    detail = data.get("detail") or ""

    # worker verdict code -> UI status
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

    # worker legacy: status=DONE, result=VERDICT
    if raw_status == "DONE":
        status = canon(result) if result else "INTERNAL_ERROR"
    else:
        # 어떤 구현에서는 status 자체가 AC/WA 처럼 올 수도 있고,
        # 혹은 ACCEPTED 같은 정규 상태가 올 수도 있음
        status = canon(raw_status) if raw_status else "QUEUED"

    return {
        "submission_id": sid,
        "status": status,
        "result": result,
        "detail": detail,
        "raw_status": raw_status,
    }

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
    """
    문제 목록: UI 드롭다운용 (가벼운 정보만)
    """
    items = []
    for pid in list_problem_ids():
        info = get_problem_info(pid)
        items.append(
            {
                "id": pid,
                "title": info["title"],
                "time_limit_ms": info["time_limit_ms"],
                "memory_limit_mb": info["memory_limit_mb"],
                "default_language": info["default_language"],
            }
        )
    return {"problems": items}


@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    """
    문제 상세(제목/설명/제한/샘플)
    """
    return get_problem_info(problem_id)


# -----------------------------------------------------------------------------
# Submissions API
# -----------------------------------------------------------------------------
@app.post("/problems/{problem_id}/submit")
async def submit(
    problem_id: str,
    req: SubmitReq,
    wait: bool = Query(True, description="true이면 채점 완료까지 기다린 뒤 결과를 반환"),
    timeout_s: float = Query(20.0, ge=0.0, description="wait 모드 최대 대기 시간(초)"),
):
    """
    - wait=false: submission_id만 즉시 반환 (기존 방식)
    - wait=true : 채점 완료까지 서버에서 대기 후 최종 결과 반환 (프론트 폴링 불필요)
    """
    if not problem_exists(problem_id):
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found (missing tests folder).")

    info = get_problem_info(problem_id)
    lang = req.language or info["default_language"]

    if lang not in info["languages"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")

    sid = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "id": sid,
        "problem_id": problem_id,
        "code": req.code,
        "language": lang,
        "ts": time.time(),
    }

    key = f"sub:{sid}"
    r.hset(key, mapping={"status": "QUEUED", "result": "", "detail": ""})
    r.rpush("queue:submissions", json.dumps(payload))

    if not wait:
        return {"submission_id": sid}

    # wait=true: DONE/최종판정까지 대기
    deadline = time.time() + float(timeout_s)
    while True:
        data = r.hgetall(key) or {}
        raw_status = (data.get("status") or "").upper()

        # worker가 바로 최종판정(status=ACCEPTED 등)으로 저장하는 경우도 대응
        if raw_status in FINAL_STATUSES:
            return normalize_submission_view(sid, data)

        if time.time() >= deadline:
            # 타임아웃: 현재 상태를 그대로 반환(프론트는 필요하면 /submissions/{sid}로 추가 확인 가능)
            out = normalize_submission_view(sid, data)
            out["detail"] = (out.get("detail") or "") + "\n(timeout waiting for result)"
            return out

        await asyncio.sleep(0.2)



@app.get("/submissions/{sid}")
def get_result(sid: str):
    key = f"sub:{sid}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="submission not found")
    data = r.hgetall(key)
    return normalize_submission_view(sid, data)

    key = f"sub:{sid}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="submission not found")
    data = r.hgetall(key)
    return {"submission_id": sid, **data}
