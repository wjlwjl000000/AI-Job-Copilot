import os
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.resume import Resume

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


def _serialize(r: Resume) -> dict:
    raw = (r.content or {}).get("raw_text", "")
    return {
        "id": r.id,
        "title": r.title,
        "base_version": r.base_version,
        "file_path": r.file_path,
        "preview": raw[:200],
        "char_count": len(raw),
    }


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).order_by(Resume.id))
    return [_serialize(r) for r in result.scalars().all()]


@router.get("/{resume_id}")
async def get_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    r = result.scalar_one_or_none()
    if not r:
        return {"status": "not_found"}
    raw = (r.content or {}).get("raw_text", "")
    return {**_serialize(r), "raw_text": raw}


@router.get("/{resume_id}/file")
async def get_resume_file(resume_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    r = result.scalar_one_or_none()
    if not r or not r.file_path or not os.path.isfile(r.file_path):
        return {"status": "not_found"}
    return FileResponse(r.file_path, filename=r.title, media_type="application/pdf")


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    r = result.scalar_one_or_none()
    if not r:
        return {"status": "not_found"}
    if r.file_path and os.path.isfile(r.file_path):
        os.unlink(r.file_path)
    await db.execute(delete(Resume).where(Resume.id == resume_id))
    await db.commit()
    return {"status": "deleted"}
