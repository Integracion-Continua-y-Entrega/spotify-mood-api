from pydantic import BaseModel


class LoginPayload(BaseModel):
    code: str
    verifier: str