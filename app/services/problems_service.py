import json
import os
from typing import Any, Dict, List

from core.config import DATA_DIR

def _problem_dir(problem_id: str) -> str:
    return os.path.join(DATA_DIR, "problems", problem_id)

def _tests_dir(problem_id: str) -> str:
    return os.path.join(_problem_dir(problem_id), "tests")

def problem_exists(problem_id: str) -> bool:
    return os.path.isdir(_tests_dir(problem_id))

def list_problem_ids() -> List[str]:
    base = os.path.join(DATA_DIR, "problems")
    if not os.path.isdir(base):
        return []
    ids: List[str] = []
    for name in sorted(os.listdir(base)):
        if problem_exists(name):
            ids.append(name)
    return ids

def read_meta(problem_id: str) -> Dict[str, Any]:
    meta_path = os.path.join(_problem_dir(problem_id), "meta.json")
    if not os.path.isfile(meta_path):
        # meta.json 없으면 기본값
        return {
            "title": problem_id,
            "time_limit_ms": 1000,
            "memory_limit_mb": 256,
            "language": "python3",
            "sample_count": 1,
        }
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_statement_md(problem_id: str) -> str:
    st_path = os.path.join(_problem_dir(problem_id), "statement.md")
    if not os.path.isfile(st_path):
        return ""
    with open(st_path, "r", encoding="utf-8") as f:
        return f.read()

def read_samples(problem_id: str, sample_count: int) -> List[Dict[str, str]]:
    tdir = _tests_dir(problem_id)
    samples: List[Dict[str, str]] = []
    for i in range(1, sample_count + 1):
        in_path = os.path.join(tdir, f"{i}.in")
        out_path = os.path.join(tdir, f"{i}.out")
        if not (os.path.isfile(in_path) and os.path.isfile(out_path)):
            break
        with open(in_path, "r", encoding="utf-8") as f:
            in_txt = f.read()
        with open(out_path, "r", encoding="utf-8") as f:
            out_txt = f.read()
        samples.append({"in": in_txt, "out": out_txt})
    return samples
