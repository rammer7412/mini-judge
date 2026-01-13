from fastapi import APIRouter, HTTPException
from services import problems_service

router = APIRouter()

@router.get("/problems")
def get_problems():
    return {"problems": problems_service.list_problem_ids()}

@router.get("/problems/{problem_id}")
def get_problem_detail(problem_id: str):
    if not problems_service.problem_exists(problem_id):
        raise HTTPException(status_code=404, detail="problem not found")

    meta = problems_service.read_meta(problem_id)
    statement_md = problems_service.read_statement_md(problem_id)

    sample_count = int(meta.get("sample_count", 1))
    samples = problems_service.read_samples(problem_id, sample_count)

    return {
        "id": problem_id,
        "meta": meta,
        "statement_md": statement_md,
        "samples": samples,
    }
