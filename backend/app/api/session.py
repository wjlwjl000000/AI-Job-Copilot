import uuid
from fastapi import APIRouter, Header, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.session import Session
from app.models.chat_message import ChatMessage

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class UpdateSessionRequest(BaseModel):
    title: str | None = None


def _serialize_session(s: Session) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "turn_id": s.turn_id,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.get("")
async def list_sessions(
    x_client_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session)
        .where(Session.client_id == x_client_id)
        .order_by(desc(Session.updated_at))
    )
    sessions = result.scalars().all()
    return [_serialize_session(s) for s in sessions]


@router.post("")
async def create_session(
    x_client_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    session = Session(client_id=x_client_id, turn_id=str(uuid.uuid4()))
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _serialize_session(session)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    x_client_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.client_id == x_client_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"status": "not_found"}
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}


@router.patch("/{session_id}")
async def update_session(
    session_id: str,
    data: UpdateSessionRequest,
    x_client_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.client_id == x_client_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"status": "not_found"}
    if data.title is not None:
        session.title = data.title
    await db.commit()
    return {"status": "updated"}


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    x_client_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id, Session.client_id == x_client_id
        )
    )
    if not result.scalar_one_or_none():
        return []
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
