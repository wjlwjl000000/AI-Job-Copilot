import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session
from app.models.application import Application
from app.models.job import Job
from app.models.session import Session
from app.models.chat_message import ChatMessage

router = APIRouter(prefix="/api/applications", tags=["applications"])


async def _trigger_supervisor(app_id: str, old_status: str, new_status: str, user_id: str):
    """后台异步触发 Supervisor，为投递状态变更生成主动通知消息。"""
    try:
        from langchain_core.messages import HumanMessage
        from app.agents.supervisor.graph import graph
        from app.agents.supervisor.planner import _ensure_registry

        await _ensure_registry()

        # 查 Job 获取公司/职位名
        job_info = ""
        async with async_session() as db:
            result = await db.execute(select(Job).join(
                Application, Application.job_id == Job.id
            ).where(Application.id == app_id))
            job = result.scalar_one_or_none()
            if job:
                job_info = f"{job.company or '未知公司'} - {job.jd_content[:80] if job.jd_content else '未知职位'}"

        status_prompts = {
            "rejected": (
                f"投递被拒：{job_info}。请搜索新的匹配职位并给予鼓励。"
            ),
            "interview": (
                f"获得面试机会：{job_info}。请生成针对该岗位的面试准备问题。"
            ),
            "offer": (
                f"已获Offer：{job_info}。请恭喜用户并提供入职准备建议。"
            ),
            "screening": (
                f"进入初筛：{job_info}。请提醒用户关注该岗位的技能要求，做好准备。"
            ),
        }
        msg = status_prompts.get(
            new_status,
            f"投递状态更新：{job_info} — 状态从「{old_status}」变更为「{new_status}」。",
        )

        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        initial_state = {
            "user_id": user_id,
            "session_id": "",
            "messages": [HumanMessage(content=msg)],
            "goal": "",
            "plan": [],
            "all_results": {},
            "loop_count": 0,
            "max_loops": 3,
            "should_continue": False,
            "synthesized_response": "",
        }

        final_state = await graph.ainvoke(initial_state, config)
        response = final_state.get("synthesized_response", "")
        if not response:
            return

        # 写入最近活跃的 session（不限 client_id，确保前端可查询到）
        async with async_session() as db:
            result = await db.execute(
                select(Session).order_by(Session.updated_at.desc()).limit(1)
            )
            session = result.scalar_one_or_none()
            if not session:
                session = Session(
                    id=str(uuid.uuid4()), client_id=user_id,
                    title="投递追踪", turn_id=str(uuid.uuid4()),
                )
                db.add(session)
                await db.flush()

            agent_msg = ChatMessage(session_id=session.id, role="agent", content=response)
            db.add(agent_msg)
            await db.commit()
    except Exception:
        pass  # 后台任务静默失败，不影响 API 响应


@router.post("")
async def create_application(data: dict, db: AsyncSession = Depends(get_db)):
    now = datetime.now().isoformat()
    app = Application(
        id=str(uuid.uuid4()),
        user_id=data.get("user_id", "u-default"),
        resume_id=data.get("resume_id"),
        job_id=data.get("job_id"),
        status=data.get("status", "planned"),
        notes=data.get("notes", ""),
        timeline=[{"status": data.get("status", "planned"), "time": now, "note": ""}],
    )
    db.add(app)
    await db.commit()
    return {"status": "created", "id": app.id}


@router.get("")
async def list_applications(status: str = None, db: AsyncSession = Depends(get_db)):
    stmt = select(
        Application.id, Application.user_id, Application.resume_id,
        Application.job_id, Application.status, Application.timeline,
        Application.notes,
        Job.company, Job.jd_content,
    ).outerjoin(Job, Application.job_id == Job.id)
    if status:
        stmt = stmt.where(Application.status == status)
    stmt = stmt.order_by(Application.id.desc())
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": r.id, "user_id": r.user_id, "resume_id": r.resume_id,
            "job_id": r.job_id, "status": r.status, "timeline": r.timeline,
            "notes": r.notes,
            "company": r.company, "jd_content": r.jd_content,
        }
        for r in rows
    ]


@router.put("/{app_id}")
async def update_application(app_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        return {"status": "error", "message": "application not found"}

    old_status = app.status
    new_status = data.get("status")
    if new_status and new_status != old_status:
        now = datetime.now().isoformat()
        timeline = list(app.timeline or [])
        timeline.append({"status": new_status, "time": now, "note": data.get("notes", "")})
        app.status = new_status
        app.timeline = timeline

    if "notes" in data and not new_status:
        app.notes = data["notes"]

    await db.commit()

    if new_status and new_status != old_status:
        asyncio.create_task(_trigger_supervisor(app_id, old_status, new_status, app.user_id))

    return {"status": "updated", "id": app_id}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application.status, func.count(Application.id))
        .group_by(Application.status)
    )
    counts = dict(result.all())
    total = sum(counts.values())
    return {
        "total": total,
        "planned": counts.get("planned", 0),
        "applied": counts.get("applied", 0),
        "screening": counts.get("screening", 0),
        "interview": counts.get("interview", 0),
        "offer": counts.get("offer", 0),
        "rejected": counts.get("rejected", 0),
    }
