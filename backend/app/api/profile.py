from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.profile import UserProfile

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _serialize(p: UserProfile) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "contact": p.contact,
        "basic": p.basic,
        "education": p.education,
        "skills": p.skills,
        "projects": p.projects,
        "organization": p.organization,
        "work_years": p.work_years,
        "target": p.target,
        "scores": p.scores,
        "summary": p.summary,
    }


@router.get("")
async def get_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()
    return _serialize(profile) if profile else {}


@router.put("")
async def update_profile(data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"status": "not_found"}
    for field in ["name", "contact", "basic", "education", "skills", "projects",
                   "organization", "work_years", "target", "scores", "summary"]:
        if field in data:
            setattr(profile, field, data[field])
    await db.commit()
    await db.refresh(profile)
    return _serialize(profile)


@router.delete("")
async def delete_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"status": "not_found"}
    await db.delete(profile)
    await db.commit()
    return {"status": "deleted"}
