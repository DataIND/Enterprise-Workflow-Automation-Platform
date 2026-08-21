from sqlalchemy import select

from app.db.models.membership import Membership


class MembershipRepository:

    @staticmethod
    async def create(db, membership: Membership):
        db.add(membership)
        await db.commit()
        await db.refresh(membership)

        return membership

    @staticmethod
    async def get(db, user_id: int, organization_id: int):
        result = await db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == organization_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_organization(db, organization_id: int):
        result = await db.execute(
            select(Membership).where(Membership.organization_id == organization_id)
        )

        return result.scalars().all()

    @staticmethod
    async def delete(db, membership: Membership):
        await db.delete(membership)
        await db.commit()
