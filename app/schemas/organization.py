from datetime import datetime
from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str


class OrganizationUpdate(BaseModel):
    name: str | None = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InviteUserRequest(BaseModel):
    user_id: int
    role: str
