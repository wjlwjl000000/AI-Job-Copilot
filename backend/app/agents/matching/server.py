from fastapi import FastAPI
from app.a2a.server import create_a2a_router, mount_agent_card
from app.a2a.agent_card import create_agent_card
from app.a2a.types import JsonRpcResponse, TaskResult, TaskStatus, TaskArtifact

app = FastAPI(title="Matching Agent")

agent_card = create_agent_card(
    agent_id="urn:agent:copilot:matching",
    name="Matching Agent",
    description="当用户画像已构建完成，需要语义搜索匹配职位、评估简历与JD的多维度匹配分数、或针对已有JD优化简历内容时调用。需要已有的profile_id和JD内容（或JD搜索条件）。不要用于首次构建画像、单纯的技能描述、面试准备场景。",
    url="http://localhost:8002",
    skills=[
        {"id": "match-jobs", "name": "职位匹配搜索", "description": "基于用户画像向量在Chroma中语义搜索匹配的职位", "examples": ["帮我搜搜适合我的职位"]},
        {"id": "score-match", "name": "匹配度评估", "description": "多维度评估简历与JD的匹配度", "examples": ["我和这个岗位匹配吗"]},
        {"id": "optimize-resume", "name": "简历优化", "description": "针对特定JD生成优化版简历", "examples": ["帮我优化简历"]},
    ],
    input_fields=[
        {"name": "job_id", "type": "string", "required": False, "description": "目标职位的唯一标识符，从用户消息的 context 或对话中提取"},
        {"name": "jd_content", "type": "string", "required": False, "description": "JD 文本内容，用户直接输入的职位描述"},
        {"name": "resume_id", "type": "string", "required": False, "description": "要使用/优化的简历版本ID"},
    ],
)

mount_agent_card(app, agent_card.model_dump())


async def handle_task(request):
    from app.agents.matching.agent import matching_agent
    from langchain_core.messages import HumanMessage
    msg_parts = request.params["message"]["parts"]
    text = " ".join([p.get("text", "") for p in msg_parts if p["type"] == "text"])
    data = {}
    for p in msg_parts:
        if p["type"] == "application/json":
            data.update(p.get("content", {}))
    prompt = f"{text}\n任务数据: {data}" if data else text
    result = await matching_agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    ai_msgs = [m for m in result.get("messages", []) if getattr(m, "type", "") == "ai"]
    answer = ai_msgs[-1].content if ai_msgs else str(result)
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-matching",
            status=TaskStatus(state="completed"),
            artifacts=[TaskArtifact(content={"result": answer})],
        ),
    )


app.include_router(create_a2a_router(handler=handle_task))
