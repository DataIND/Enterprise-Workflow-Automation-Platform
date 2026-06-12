from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):

    user = await AuthService.register(
        db=db, email=request.email, password=request.password
    )

    return {"message": "User created", "user_id": user.id}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):

    token = await AuthService.login(db, request.email, request.password)

    if not token:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    return {"access_token": token, "token_type": "bearer"}
