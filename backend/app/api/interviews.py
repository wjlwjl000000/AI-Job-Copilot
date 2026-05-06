from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.get("/{interview_id}")
async def get_interview(interview_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM interviews WHERE id=:id"), {"id": interview_id})
    row = result.fetchone()
    if row:
        return dict(row._mapping)
    return {"id": interview_id, "questions": []}


@router.put("/{interview_id}/questions/{question_id}")
async def submit_answer(interview_id: str, question_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """提交单个问题的回答，更新 questions 数组中对应 id 的 answer 字段"""
    result = await db.execute(text("SELECT questions FROM interviews WHERE id=:id"), {"id": interview_id})
    row = result.fetchone()
    if not row:
        return {"status": "error", "message": "Interview not found"}
    import json
    questions = row.questions if isinstance(row.questions, list) else json.loads(row.questions)
    for q in questions:
        if q.get("id") == question_id:
            q["answer"] = data.get("answer", "")
            break
    await db.execute(
        text("UPDATE interviews SET questions=:questions WHERE id=:id"),
        {"questions": json.dumps(questions), "id": interview_id},
    )
    await db.commit()
    return {"status": "updated", "question_id": question_id}
