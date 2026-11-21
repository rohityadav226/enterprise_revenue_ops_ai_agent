from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$"
    )

    password: str = Field(
        min_length=12,
        max_length=128
    )

class LoginRequest(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    username: str
    full_name: str
    role: str
    region: str | None
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]