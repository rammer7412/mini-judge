from typing import Optional, Dict, Any
from pydantic import BaseModel

class SubmitReq(BaseModel):
    code: str
    language: Optional[str] = None

class SubmitResp(BaseModel):
    submission_id: str

class SubmissionResultResp(BaseModel):
    submission_id: str
    status: Optional[str] = None
    result: Optional[str] = None
    detail: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
