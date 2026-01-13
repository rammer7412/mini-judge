from fastapi import APIRouter

from app.schemas.problems import ProblemListResp, ProblemListItem, ProblemDetailResp
from app.services.problems_service import list_problem_ids, get_problem_info

router = APIRouter()

@router.get("/problems", response_model=ProblemListResp)
def get_problems():
    items = []
    for pid in list_problem_ids():
        info = get_problem_info(pid)
        items.append(
            ProblemListItem(
                id=pid,
                title=info["title"],
                time_limit_ms=info["time_limit_ms"],
                memory_limit_mb=info["memory_limit_mb"],
                default_language=info["default_language"],
            )
        )
    return ProblemListResp(problems=items)

@router.get("/problems/{problem_id}", response_model=ProblemDetailResp)
def get_problem(problem_id: str):
    info = get_problem_info(problem_id)
    return ProblemDetailResp(**info)
