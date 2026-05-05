from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("")
async def create_application(data: dict, db: AsyncSession = Depends(get_db)):
    return {"status": "created", "id": "a-new"}


@router.get("")
async def list_applications(status: str = None, db: AsyncSession = Depends(get_db)):
    return []


@router.put("/{app_id}")
async def update_application(app_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    return {"status": "updated", "id": app_id}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return {"total": 0, "screening": 0, "interview": 0, "offer": 0, "rejected": 0}
