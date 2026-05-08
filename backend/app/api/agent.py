import asyncio
import json
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Header, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from app.agents.supervisor.graph import graph
from app.a2a.registry import AgentRegistry
from app.a2a.client import A2AClient
from app.database import get_db
from app.models.session import Session
from app.models.chat_message import ChatMessage
from app.tools.parser import set_session_id

client = A2AClient()
registry = AgentRegistry(client=client)

router = APIRouter(prefix="/api/agent", tags=["agent"])

# 按 session_id 隔离的已解析文件缓存: {session_id: {file_id: {filename, text, char_count}}}
_parsed_files: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    turn_id: str | None = None


@router.post("/chat")
async def agent_chat(
    request: ChatRequest,
    x_client_id: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    session_id = request.session_id
    turn_id = None

    if session_id:
        set_session_id(session_id)

    if session_id and x_client_id:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id, Session.client_id == x_client_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            turn_id = session.turn_id
            session.updated_at = datetime.now()
            user_msg = ChatMessage(
                session_id=session_id, role="user", content=request.message
            )
            db.add(user_msg)
            await db.commit()

    if not turn_id:
        turn_id = request.turn_id or str(uuid.uuid4())

    initial_state = {
        "user_id": "u-default",
        "session_id": session_id or "",
        "messages": [HumanMessage(content=request.message)],
        "goal": "",
        "plan": [],
        "all_results": {},
        "loop_count": 0,
        "max_loops": 3,
        "should_continue": False,
        "synthesized_response": "",
    }
    config = {"configurable": {"thread_id": turn_id}}

    async def event_stream():
        response_content = ""
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            if "__interrupt__" in event:
                yield f"data: {json.dumps(event['__interrupt__'], ensure_ascii=False)}\n\n"
            elif "synthesizer" in event:
                content = event["synthesizer"].get("synthesized_response", "")
                response_content = content
                yield f"data: {json.dumps({'type': 'response', 'content': content, 'turn_id': turn_id}, ensure_ascii=False)}\n\n"

        if session_id and response_content:
            agent_msg = ChatMessage(
                session_id=session_id, role="agent", content=response_content
            )
            db.add(agent_msg)
            await db.commit()

        yield f"data: {json.dumps({'type': 'done', 'turn_id': turn_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/resume")
async def resume_chat(
    request: ChatRequest,
    x_client_id: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    session_id = request.session_id
    turn_id = None

    if session_id:
        set_session_id(session_id)

    if session_id and x_client_id:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id, Session.client_id == x_client_id
            )
        )
        session = result.scalar_one_or_none()
        if session:
            turn_id = session.turn_id
            session.updated_at = datetime.now()
            user_msg = ChatMessage(
                session_id=session_id, role="user", content=request.message
            )
            db.add(user_msg)
            await db.commit()

    if not turn_id:
        turn_id = request.turn_id or str(uuid.uuid4())

    config = {"configurable": {"thread_id": turn_id}}

    async def event_stream():
        response_content = ""
        async for event in graph.astream(
            Command(resume={"answer": request.message}),
            config,
            stream_mode="updates",
        ):
            if "synthesizer" in event:
                content = event["synthesizer"].get("synthesized_response", "")
                response_content = content
                yield f"data: {json.dumps({'type': 'response', 'content': content}, ensure_ascii=False)}\n\n"

        if session_id and response_content:
            agent_msg = ChatMessage(
                session_id=session_id, role="agent", content=response_content
            )
            db.add(agent_msg)
            await db.commit()

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/parse-file")
async def parse_file(file: UploadFile = File(...), session_id: str = Form(None)):
    """接收文件，用 MinerULoader 解析，按 session_id 存入后端列表"""
    import tempfile
    file_id = str(uuid.uuid4())
    suffix = os.path.splitext(file.filename or "resume.pdf")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    text = None
    try:
        from langchain_mineru import MinerULoader
        loader = MinerULoader(source=tmp_path, language='ch', mode='flash', timeout=30)
        docs = loader.load()
        text = "\n".join(d.page_content for d in docs)
    except Exception:
        pass

    if not text:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(tmp_path)
            text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception:
            pass

    if not text:
        os.unlink(tmp_path)
        return {"status": "error", "message": "简历解析失败，请检查文件格式"}

    os.unlink(tmp_path)
    entry = {"filename": file.filename, "text": text, "char_count": len(text)}
    if session_id:
        _parsed_files.setdefault(session_id, {})[file_id] = entry
    return {"status": "ok", "file_id": file_id, "filename": file.filename, "char_count": len(text)}


@router.delete("/parse-file/{file_id}")
async def delete_parsed_file(file_id: str, session_id: str = None):
    """删除后端存储的已解析文件"""
    if session_id and session_id in _parsed_files:
        _parsed_files[session_id].pop(file_id, None)
        if not _parsed_files[session_id]:
            del _parsed_files[session_id]
        return {"status": "deleted"}
    return {"status": "not_found"}


@router.get("/parse-file/{file_id}")
async def get_parsed_file(file_id: str, session_id: str = None):
    """获取已解析文件的内容"""
    if session_id and session_id in _parsed_files:
        f = _parsed_files[session_id].get(file_id)
        if f:
            return {"file_id": file_id, "filename": f["filename"], "text": f["text"], "char_count": f["char_count"]}
    return {"status": "not_found"}


class RegisterRequest(BaseModel):
    agent_url: str


@router.post("/registry")
async def register_agent(req: RegisterRequest):
    try:
        card = await registry.register(req.agent_url)
        return {"status": "registered", "name": card["name"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/registry")
async def list_registry():
    return registry.list_all()


@router.delete("/registry/{agent_name}")
async def unregister_agent(agent_name: str):
    if registry.is_system_agent(agent_name):
        return {"status": "error", "message": "系统Agent不可删除"}
    registry.unregister(agent_name)
    return {"status": "deleted"}
