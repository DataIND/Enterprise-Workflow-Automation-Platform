from fastapi import HTTPException, status

from app.db.models.membership import Membership
from app.repositories.membership_repository import MembershipRepository
from app.utils.enums import UserRole

ROLE_PRIORITY = {
    UserRole.MEMBER: 1,
    UserRole.ADMIN: 2,
    UserRole.OWNER: 3,
}


def role_satisfies(role: str, minimum_role: UserRole) -> bool:
    try:
        current = ROLE_PRIORITY[UserRole(role)]
    except ValueError:
        return False

    return current >= ROLE_PRIORITY[minimum_role]


async def require_org_role(
    db,
    user_id: int,
    organization_id: int,
    minimum_role: UserRole = UserRole.MEMBER,
) -> Membership:
    membership = await MembershipRepository.get(db, user_id, organization_id)

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    if not role_satisfies(membership.role, minimum_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires {minimum_role.value} role or higher",
        )

    return membership
