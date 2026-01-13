import json
from pathlib import Path
from typing import List, Dict, Any

from fastapi import HTTPException
from core.config import DATA_DIR, DEFAULT_SAMPLE_COUNT


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
    title = meta.get("title") or problem_id
    time_limit_ms = int(meta.get("time_limit_ms") or 1000)
    memory_limit_mb = int(meta.get("memory_limit_mb") or 256)

    languages = meta.get("languages")
    if not isinstance(languages, list) or not languages:
        languages = ["python3"]

    default_language = meta.get("default_language") or languages[0]

    sample_count = meta.get("sample_count")
    try:
        sample_count = int(sample_count) if sample_count is not None else DEFAULT_SAMPLE_COUNT
    except Exception:
        sample_count = DEFAULT_SAMPLE_COUNT

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
            break
    return samples


def get_problem_info(problem_id: str) -> Dict[str, Any]:
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
