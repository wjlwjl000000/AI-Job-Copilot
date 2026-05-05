from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
async def get_profile(db: AsyncSession = Depends(get_db)):
    return {}


@router.put("")
async def update_profile(data: dict, user_id: str = "u-default", db: AsyncSession = Depends(get_db)):
    return {"status": "updated", "data": data}
