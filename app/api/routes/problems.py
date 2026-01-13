from fastapi import APIRouter
from services.problems_service import (
    list_problem_ids,
    load_meta,
    load_statement,
    load_samples,
)

router = APIRouter()

@router.get("/problems")
def get_problems():
    problems = []
    for pid in list_problem_ids():
        # 폴더명이 pid여도 meta["id"]가 다를 수 있어서 meta 기반으로 내려줌
        meta = load_meta(pid)
        problems.append({
            "id": meta["id"],
            "title": meta["title"],
            "languages": meta["languages"],
            "default_language": meta["default_language"],
        })
    return {"problems": problems}

@router.get("/problems/{problem_id}")
def get_problem_detail(problem_id: str):
    meta = load_meta(problem_id)
    detail = dict(meta)
    detail["statement_md"] = load_statement(problem_id)
    detail["samples"] = load_samples(problem_id, int(meta["sample_count"]))
    return detail
