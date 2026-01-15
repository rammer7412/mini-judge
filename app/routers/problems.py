from fastapi import APIRouter, HTTPException

from services.problems_service import get_problem_info, list_problem_ids

router = APIRouter()


@router.get("/problems")
def get_problems():
    """문제 목록: UI 드롭다운용 (가벼운 정보만)"""
    items = []
    for pid in list_problem_ids():
        try:
            info = get_problem_info(pid)
        except FileNotFoundError:
            continue
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


@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    """문제 상세(제목/설명/제한/샘플)"""
    try:
        return get_problem_info(problem_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")
