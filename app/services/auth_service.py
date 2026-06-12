from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

from app.core.security import hash_password, verify_password, create_access_token


class AuthService:

    @staticmethod
    async def register(db: AsyncSession, email: str, password: str):

        result = await db.execute(select(User).where(User.email == email))

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise Exception("Email already registered")

        user = User(email=email, password_hash=hash_password(password))

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def login(db, email, password):
        result = await db.execute(select(User).where(User.email == email))

        user = result.scalar_one_or_none()

        if not user:

            return None

        if not verify_password(password, user.password_hash):
            return None

        token = create_access_token({"sub": str(user.id)})

        return token
