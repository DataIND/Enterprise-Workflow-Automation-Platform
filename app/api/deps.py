from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_org_role
from app.core.security import decode_token
from app.db.models.membership import Membership
from app.db.models.user import User
from app.db.session import get_db
from app.utils.enums import UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id_int))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user.id


def organization_role(minimum_role: UserRole):
    """Dependency for routes with an ``organization_id`` path parameter."""

    async def dependency(
        organization_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user),
    ) -> Membership:
        return await require_org_role(db, user_id, organization_id, minimum_role)

    return dependency
