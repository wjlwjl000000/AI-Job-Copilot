from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    return {"id": job_id, "title": "Sample Job"}


@router.post("")
async def create_job(data: dict, db: AsyncSession = Depends(get_db)):
    return {"status": "created", "id": "j-new"}
