from sqlalchemy import select


from sqlalchemy.ext.asyncio import AsyncSession


from app.db.models.user import User


class UserRepository:

    @staticmethod
    async def create(db: AsyncSession, user: User):

        db.add(user)

        await db.commit()

        await db.refresh(user)

        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int):

        result = await db.execute(select(User).where(User.id == user_id))

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str):

        result = await db.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    @staticmethod
    async def search_users(db, keyword):

        result = await db.execute(select(User).where(User.email.contains(keyword)))

        return result.scalars().all()
