from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(None), db: AsyncSession = Depends(get_db)):
    return {"status": "ok", "resume_id": "r-1"}


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    return []


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    return {"status": "deleted", "resume_id": resume_id}
