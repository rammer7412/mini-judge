from typing import Optional

from pydantic import BaseModel, Field


class SubmitReq(BaseModel):
    code: str
    language: Optional[str] = None
    # 로그인 없이 이름을 받아 제출 기록에 포함 (필수)
    user_name: str = Field(..., min_length=1, max_length=32)
