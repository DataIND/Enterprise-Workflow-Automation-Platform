from fastapi import HTTPException


from app.repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    async def get_profile(db, user_id: int):

        user = await UserRepository.get_by_id(db, user_id)

        if not user:

            raise HTTPException(status_code=404, detail="User not found")

        return user

    @staticmethod
    async def update_profile(db, user_id, payload):

        user = await UserService.get_profile(db, user_id)

        update_data = payload.dict(exclude_unset=True)

        for key, value in update_data.items():

            setattr(user, key, value)

        await db.commit()

        await db.refresh(user)

        return user

    @staticmethod
    async def deactivate(db, user_id):

        user = await UserService.get_profile(db, user_id)

        user.is_active = False

        await db.commit()

        return {"message": "User deactivated"}

    @staticmethod
    async def search(db, keyword):

        return await UserRepository.search_users(db, keyword)
