from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):

    email: EmailStr

    password: str

    full_name: str | None = None


class UserUpdate(BaseModel):

    full_name: str | None = None


class UserResponse(BaseModel):

    id: int

    email: EmailStr

    full_name: str | None

    is_active: bool

    is_verified: bool

    created_at: datetime

    class Config:

        from_attributes = True
