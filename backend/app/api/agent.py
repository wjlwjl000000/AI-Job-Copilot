import asyncio
import json
import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from app.agents.supervisor.graph import graph
from app.a2a.registry import AgentRegistry
from app.a2a.client import A2AClient

client = A2AClient()
registry = AgentRegistry(client=client)

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    turn_id: str | None = None


@router.post("/chat")
async def agent_chat(request: ChatRequest):
    turn_id = request.turn_id or str(uuid.uuid4())
    initial_state = {
        "user_id": "u-default",
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
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            if "__interrupt__" in event:
                yield f"data: {json.dumps(event['__interrupt__'], ensure_ascii=False)}\n\n"
            elif "synthesizer" in event:
                content = event["synthesizer"].get("synthesized_response", "")
                # Stream character-by-character for real-time display
                for i in range(0, len(content), 3):
                    chunk = content[i:i+3]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'turn_id': turn_id}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'type': 'done', 'turn_id': turn_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/resume")
async def resume_chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.turn_id}}

    async def event_stream():
        async for event in graph.astream(
            Command(resume={"answer": request.message}),
            config,
            stream_mode="updates",
        ):
            if "synthesizer" in event:
                content = event["synthesizer"].get("synthesized_response", "")
                yield f"data: {json.dumps({'type': 'response', 'content': content}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """Receive a resume file, parse it, return extracted text"""
    import tempfile
    # Save uploaded file to temp location
    suffix = os.path.splitext(file.filename or "resume.pdf")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        from app.tools.parser import parse_document
        result = await parse_document.ainvoke({"file_path": tmp_path})
        return {"status": "ok", "text": result.get("text", ""), "metadata": result.get("metadata", {}), "filename": file.filename}
    finally:
        os.unlink(tmp_path)


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
