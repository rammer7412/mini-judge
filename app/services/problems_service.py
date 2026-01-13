import os, json
from typing import List, Dict, Any
from fastapi import HTTPException

DATA_DIR = os.getenv("DATA_DIR", "/data")

def problem_base(problem_id: str) -> str:
    return os.path.join(DATA_DIR, "problems", problem_id)

def meta_path(problem_id: str) -> str:
    return os.path.join(problem_base(problem_id), "meta.json")

def statement_path(problem_id: str) -> str:
    return os.path.join(problem_base(problem_id), "statement.md")

def tests_dir(problem_id: str) -> str:
    return os.path.join(problem_base(problem_id), "tests")

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_meta(problem_id: str) -> Dict[str, Any]:
    mp = meta_path(problem_id)
    if not os.path.isfile(mp):
        raise HTTPException(404, f"meta.json missing for problem '{problem_id}'")

    meta = read_json(mp)

    required = ["id", "title", "time_limit_ms", "memory_limit_mb", "languages", "default_language", "sample_count"]
    for k in required:
        if k not in meta:
            raise HTTPException(500, f"meta.json missing field '{k}' for problem '{problem_id}'")
    return meta

def load_statement(problem_id: str) -> str:
    sp = statement_path(problem_id)
    if not os.path.isfile(sp):
        return ""
    return read_text(sp)

def load_samples(problem_id: str, sample_count: int) -> List[Dict[str, Any]]:
    tdir = tests_dir(problem_id)
    if not os.path.isdir(tdir):
        return []

    samples: List[Dict[str, Any]] = []
    for n in range(1, sample_count + 1):
        in_path = os.path.join(tdir, f"{n}.in")
        out_path = os.path.join(tdir, f"{n}.out")
        if not (os.path.isfile(in_path) and os.path.isfile(out_path)):
            break
        samples.append({
            "n": n,
            "in": read_text(in_path),
            "out": read_text(out_path),
        })
    return samples

def list_problem_ids() -> List[str]:
    base = os.path.join(DATA_DIR, "problems")
    if not os.path.isdir(base):
        return []
    return sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))])
