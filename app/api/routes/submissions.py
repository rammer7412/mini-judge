from fastapi import APIRouter

from app.core.redis_client import get_redis
from app.schemas.submissions import SubmitReq, SubmitResp
from app.services.submissions_service import enqueue_submission, fetch_submission_result
from app.services.problems_service import get_problem_info

router = APIRouter()

@router.post("/problems/{problem_id}/submit", response_model=SubmitResp)
def submit(problem_id: str, req: SubmitReq):
    r = get_redis()
    info = get_problem_info(problem_id)
    lang = req.language or info["default_language"]
    sid = enqueue_submission(r, problem_id=problem_id, code=req.code, language=lang)
    return SubmitResp(submission_id=sid)

@router.get("/submissions/{sid}")
def get_result(sid: str):
    r = get_redis()
    data = fetch_submission_result(r, sid)
    return {"submission_id": sid, **data}
