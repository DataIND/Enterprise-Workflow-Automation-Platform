from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, organization_role
from app.db.session import get_db
from app.schemas.organization import (
    InviteUserRequest,
    MembershipResponse,
    MembershipRoleUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization_service import OrganizationService
from app.utils.enums import UserRole

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await OrganizationService.create(db, user_id, payload)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await OrganizationService.list(db, user_id)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.MEMBER)),
):
    return await OrganizationService.get(db, organization_id)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.ADMIN)),
):
    return await OrganizationService.update(db, organization_id, payload)


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.OWNER)),
):
    return await OrganizationService.delete(db, organization_id)


@router.get("/{organization_id}/members", response_model=list[MembershipResponse])
async def list_members(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.MEMBER)),
):
    return await OrganizationService.list_members(db, organization_id)


@router.post(
    "/{organization_id}/invite",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_user(
    organization_id: int,
    payload: InviteUserRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.ADMIN)),
):
    return await OrganizationService.invite_user(db, organization_id, payload)


@router.patch(
    "/{organization_id}/members/{member_user_id}", response_model=MembershipResponse
)
async def update_member_role(
    organization_id: int,
    member_user_id: int,
    payload: MembershipRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.OWNER)),
):
    return await OrganizationService.update_member_role(
        db, organization_id, member_user_id, payload
    )


@router.delete("/{organization_id}/members/{member_user_id}")
async def remove_member(
    organization_id: int,
    member_user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(organization_role(UserRole.ADMIN)),
):
    return await OrganizationService.remove_member(db, organization_id, member_user_id)
