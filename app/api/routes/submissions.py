from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import problems as problems_service
from services import submissions as submissions_service

router = APIRouter()

class SubmitReq(BaseModel):
    code: str
    language: Optional[str] = None

@router.post("/problems/{problem_id}/submit")
def submit(problem_id: str, req: SubmitReq):
    if not problems_service.problem_exists(problem_id):
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found (missing tests folder).")

    info = problems_service.get_problem_info(problem_id)
    lang = req.language or info["default_language"]

    if lang not in info["languages"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")

    sid = submissions_service.create_submission(problem_id, req.code, lang)
    return {"submission_id": sid}

@router.get("/submissions/{sid}")
def get_result(sid: str):
    data = submissions_service.get_submission(sid)
    if not data:
        raise HTTPException(status_code=404, detail="submission not found")
    return {"submission_id": sid, **data}
