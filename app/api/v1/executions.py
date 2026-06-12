from fastapi import APIRouter, Depends


from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db


from app.repositories.execution_repository import ExecutionRepository

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("")
async def executions(db: AsyncSession = Depends(get_db)):

    return await ExecutionRepository.get_all(db)
