from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.organization import OrganizationCreate
from app.db.models.organization import Organization

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("")
async def create_org(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):

    org = Organization(name=payload.name, owner_id=user_id)

    db.add(org)
    await db.commit()

    return org
