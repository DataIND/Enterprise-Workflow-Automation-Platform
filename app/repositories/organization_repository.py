from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.organization import Organization
from app.db.models.membership import Membership


class OrganizationRepository:

    @staticmethod
    async def create(db: AsyncSession, organization: Organization):
        db.add(organization)
        await db.commit()
        await db.refresh(organization)

        return organization

    @staticmethod
    async def get_user_organizations(db, user_id: int):

        result = await db.execute(
            select(Organization).join(Membership).where(Membership.user_id == user_id)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(db, organization_id):
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db, organization):
        await db.delete(organization)

        await db.commit()
