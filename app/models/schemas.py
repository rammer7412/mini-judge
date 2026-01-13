from typing import Optional

from pydantic import BaseModel


class SubmitReq(BaseModel):
    code: str
    language: Optional[str] = None
