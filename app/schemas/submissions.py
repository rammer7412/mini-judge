from pydantic import BaseModel

class SubmitReq(BaseModel):
    code: str
