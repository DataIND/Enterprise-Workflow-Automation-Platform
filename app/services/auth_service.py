from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User


class AuthService:
    @staticmethod
    def _issue_tokens(user_id: int) -> dict:
        subject = {"sub": str(user_id)}
        return {
            "access_token": create_access_token(subject),
            "refresh_token": create_refresh_token(subject),
            "token_type": "bearer",
        }

    @staticmethod
    async def register(db: AsyncSession, email: str, password: str):
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(email=email, password_hash=hash_password(password))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> dict | None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return AuthService._issue_tokens(user.id)

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> dict | None:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        result = await db.execute(select(User).where(User.id == user_id_int))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        return AuthService._issue_tokens(user.id)
