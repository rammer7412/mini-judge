from fastapi import APIRouter, HTTPException, Query

from models.schemas import SubmitReq
from services.problems_service import get_problem_info, problem_exists
from services.submissions_service import (
    create_submission,
    get_submission_raw,
    normalize_submission_view,
    wait_for_final_result,
)

router = APIRouter()


@router.post("/problems/{problem_id}/submit")
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

    try:
        info = get_problem_info(problem_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    lang = req.language or info["default_language"]
    if lang not in info["languages"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")

    # username (no auth) - 필수
    user_name = (req.user_name or "").strip()
    if not user_name:
        raise HTTPException(status_code=400, detail="user_name is required")
    if len(user_name) > 32:
        raise HTTPException(status_code=400, detail="user_name too long (max 32)")

    sid = create_submission(problem_id=problem_id, code=req.code, language=lang, user_name=user_name)

    if not wait:
        return {"submission_id": sid}

    return await wait_for_final_result(sid=sid, timeout_s=float(timeout_s))


@router.get("/submissions/{sid}")
def get_result(sid: str):
    key = f"sub:{sid}"
    # r.exists는 deps에서 관리하지만, 여기서는 raw 조회로 판별
    data = get_submission_raw(sid)
    if not data:
        raise HTTPException(status_code=404, detail="submission not found")
    return normalize_submission_view(sid, data)
