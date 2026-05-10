from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.job import Job
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.id.desc()))
    return [{"id": r.id, "source": r.source, "jd_content": r.jd_content,
             "company": r.company, "salary_range": r.salary_range,
             "city": r.city, "status": r.status} for r in result.scalars().all()]


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    r = result.scalar_one_or_none()
    if not r:
        return {"status": "not_found"}
    return {"id": r.id, "source": r.source, "jd_content": r.jd_content,
            "company": r.company, "salary_range": r.salary_range,
            "city": r.city, "status": r.status, "requirements": r.requirements}


@router.post("")
async def create_job(data: dict, db: AsyncSession = Depends(get_db)):
    job = Job(
        id=str(uuid.uuid4()),
        source=data.get("source", "manual"),
        jd_content=data.get("jd_content", ""),
        company=data.get("company", ""),
        salary_range=data.get("salary_range", ""),
        city=data.get("city", ""),
        requirements=data.get("requirements", []),
        status="open",
    )
    db.add(job)
    await db.commit()
    return {"status": "created", "id": job.id}
