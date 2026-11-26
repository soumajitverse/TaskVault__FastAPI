from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# 1. Base User Schema (shared fields)
class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    email: str = Field(
        ...,
        max_length=255,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="Valid email address",
    )


# 2. Registration Request Body (raw password required from client)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


# 3. Clean JSON Login Request Body
class UserLogin(BaseModel):
    email: str
    password: str


# 4. Response Schema (safe to send back - excludes sensitive password fields)
class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 5. JWT Token Schemas (OAuth2 format)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    role: str | None = None
