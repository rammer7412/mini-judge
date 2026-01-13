import os
import uuid
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

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
DEFAULT_SAMPLE_COUNT = int(os.getenv("DEFAULT_SAMPLE_COUNT", "3"))

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="Mini Judge (MVP)")

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
def submit(problem_id: str, req: SubmitReq):
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

    r.hset(f"sub:{sid}", mapping={"status": "QUEUED", "result": "", "detail": ""})
    r.rpush("queue:submissions", json.dumps(payload))
    return {"submission_id": sid}


@app.get("/submissions/{sid}")
def get_result(sid: str):
    key = f"sub:{sid}"
    if not r.exists(key):
        raise HTTPException(status_code=404, detail="submission not found")
    data = r.hgetall(key)
    return {"submission_id": sid, **data}
