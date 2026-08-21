from datetime import datetime

from pydantic import BaseModel

from app.utils.enums import UserRole


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
    role: UserRole = UserRole.MEMBER


class MembershipRoleUpdate(BaseModel):
    role: UserRole


class MembershipResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True
