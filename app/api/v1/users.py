from fastapi import APIRouter, Depends


from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db


from app.api.deps import get_current_user


from app.schemas.user import UserResponse, UserUpdate


from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def profile(
    db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)
):

    return await UserService.get_profile(db, user_id)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):

    return await UserService.update_profile(db, user_id, payload)


@router.delete("/me")
async def delete_account(
    db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)
):

    return await UserService.deactivate(db, user_id)


@router.get("/search", response_model=list[UserResponse])
async def search_users(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    return await UserService.search(db, keyword)
