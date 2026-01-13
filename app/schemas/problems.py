from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ProblemListItem(BaseModel):
    id: str
    title: str
    time_limit_ms: int
    memory_limit_mb: int
    default_language: str

class ProblemListResp(BaseModel):
    problems: List[ProblemListItem]

class SampleCase(BaseModel):
    name: str
    input: str
    output: str

class ProblemDetailResp(BaseModel):
    id: str
    title: str
    time_limit_ms: int
    memory_limit_mb: int
    languages: List[str]
    default_language: str
    sample_count: int
    statement: str
    samples: List[SampleCase]
    # 원하면 meta 원본을 같이 노출할 수도 있음(현재는 비노출)
    meta: Optional[Dict[str, Any]] = None
