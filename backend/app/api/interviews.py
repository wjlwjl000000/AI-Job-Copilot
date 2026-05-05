from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.get("/{interview_id}")
async def get_interview(interview_id: str, db: AsyncSession = Depends(get_db)):
    return {"id": interview_id, "questions": []}
