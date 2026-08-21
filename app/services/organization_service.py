from fastapi import HTTPException, status

from app.db.models.membership import Membership
from app.db.models.organization import Organization
from app.repositories.membership_repository import MembershipRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.utils.enums import UserRole


class OrganizationService:

    @staticmethod
    async def create(db, user_id: int, payload):
        organization = Organization(name=payload.name, owner_id=user_id)

        org = await OrganizationRepository.create(db, organization)

        membership = Membership(
            user_id=user_id,
            organization_id=org.id,
            role=UserRole.OWNER.value,
        )

        await MembershipRepository.create(db, membership)

        return org

    @staticmethod
    async def list(db, user_id: int):
        return await OrganizationRepository.get_user_organizations(db, user_id)

    @staticmethod
    async def get(db, organization_id: int):
        org = await OrganizationRepository.get_by_id(db, organization_id)

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        return org

    @staticmethod
    async def update(db, organization_id: int, payload):
        org = await OrganizationService.get(db, organization_id)

        if payload.name is not None:
            org.name = payload.name

        await db.commit()
        await db.refresh(org)

        return org

    @staticmethod
    async def delete(db, organization_id: int):
        org = await OrganizationService.get(db, organization_id)

        await OrganizationRepository.delete(db, org)

        return {"message": "Organization deleted"}

    @staticmethod
    async def list_members(db, organization_id: int):
        await OrganizationService.get(db, organization_id)

        return await MembershipRepository.get_by_organization(db, organization_id)

    @staticmethod
    async def invite_user(db, organization_id: int, payload):
        await OrganizationService.get(db, organization_id)

        if payload.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An organization can only have one owner",
            )

        user = await UserRepository.get_by_id(db, payload.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        existing = await MembershipRepository.get(db, payload.user_id, organization_id)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            )

        membership = Membership(
            user_id=payload.user_id,
            organization_id=organization_id,
            role=payload.role.value,
        )

        return await MembershipRepository.create(db, membership)

    @staticmethod
    async def _get_membership(db, organization_id: int, user_id: int) -> Membership:
        membership = await MembershipRepository.get(db, user_id, organization_id)

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found",
            )

        return membership

    @staticmethod
    async def update_member_role(db, organization_id: int, user_id: int, payload):
        membership = await OrganizationService._get_membership(
            db, organization_id, user_id
        )

        if membership.role == UserRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The owner role cannot be changed",
            )

        if payload.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An organization can only have one owner",
            )

        membership.role = payload.role.value

        await db.commit()
        await db.refresh(membership)

        return membership

    @staticmethod
    async def remove_member(db, organization_id: int, user_id: int):
        membership = await OrganizationService._get_membership(
            db, organization_id, user_id
        )

        if membership.role == UserRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The owner cannot be removed from the organization",
            )

        await MembershipRepository.delete(db, membership)

        return {"message": "Member removed"}
