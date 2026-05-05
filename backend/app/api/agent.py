import json
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from app.agents.supervisor.graph import graph

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    turn_id: str = None


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
                yield f"data: {json.dumps({'type': 'response', 'content': content, 'turn_id': turn_id}, ensure_ascii=False)}\n\n"
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
