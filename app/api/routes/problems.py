from fastapi import APIRouter
from services import problems as problems_service

router = APIRouter()

@router.get("/problems")
def get_problems():
    items = []
    for pid in problems_service.list_problem_ids():
        info = problems_service.get_problem_info(pid)
        items.append({
            "id": pid,
            "title": info["title"],
            "time_limit_ms": info["time_limit_ms"],
            "memory_limit_mb": info["memory_limit_mb"],
            "languages": info["languages"],
            "default_language": info["default_language"],
            "sample_count": info["sample_count"],
        })
    return {"problems": items}

@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    return problems_service.get_problem_info(problem_id)
