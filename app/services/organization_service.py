from fastapi import HTTPException
from app.db.models.organization import Organization
from app.db.models.membership import Membership
from app.repositories.organization_repository import OrganizationRepository


class OrganizationService:

    @staticmethod
    async def create(db, user_id: int, payload):
        organization = Organization(name=payload.name, owner_id=user_id)

        org = await OrganizationRepository.create(db, organization)

        membership = Membership(user_id=user_id, organization_id=org.id, role="OWNER")

        db.add(membership)
        await db.commit()

        return org

    @staticmethod
    async def list(db, user_id):
        return await OrganizationRepository.get_user_organizations(db, user_id)

    @staticmethod
    async def get(db, organization_id):

        org = await OrganizationRepository.get_by_id(db, organization_id)

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        return org

    @staticmethod
    async def update(db, organization_id, payload):
        org = await OrganizationService.get(db, organization_id)

        if payload.name:
            org.name = payload.name
        await db.commit()
        await db.refresh(org)

        return org

    @staticmethod
    async def invite_user(db, organization_id, payload):
        membership = Membership(
            user_id=payload.user_id, organization_id=organization_id, role=payload.role
        )

        db.add(membership)

        await db.commit()

        return {"message": "User invited"}
