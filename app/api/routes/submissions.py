from fastapi import APIRouter, HTTPException
from schemas.submissions import SubmitReq
from services import problems_service, submissions_service

router = APIRouter()

@router.post("/problems/{problem_id}/submit")
def submit(problem_id: str, req: SubmitReq):
    if not problems_service.problem_exists(problem_id):
        raise HTTPException(status_code=404, detail="Problem not found (missing tests folder).")

    sid = submissions_service.create_submission(problem_id, req.code)
    return {"submission_id": sid}

@router.get("/submissions/{sid}")
def get_result(sid: str):
    data = submissions_service.get_submission(sid)
    if not data:
        raise HTTPException(status_code=404, detail="submission not found")
    return {"submission_id": sid, **data}
