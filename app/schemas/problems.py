from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class ProblemSummary(BaseModel):
    id: str

class ProblemDetail(BaseModel):
    id: str
    meta: Dict[str, Any]
    statement_md: str
    samples: List[Dict[str, str]]  # [{"in": "...", "out": "..."}]
