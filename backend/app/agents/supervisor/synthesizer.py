import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.agents.supervisor import stream
from app.tools.llm import llm


async def synthesizer_node(state: SupervisorState) -> dict:
    results = state.get("all_results", {})
    turn_id = state.get("_turn_id", "")

    if not results or not any(v for v in results.values()):
        user_msg = state["messages"][-1].content if state["messages"] else "hello"
        prompt = (
            "你是AI求职助手，可以与用户进行自然友好的对话。\n"
            f"用户说: {user_msg}\n\n"
            "用中文自然回复，语气友好。如果用户只是打招呼或闲聊，就轻松回应；"
            "如果用户表达了求职需求但你没找到匹配的Agent，诚实说明并询问如何帮助。\n"
            "末尾附上一条求职相关的软性建议（不超过一句），由用户决定是否采纳。"
        )
    else:
        prompt = (
            "你是求职助手。基于以下任务结果，生成一段连贯的自然语言回复。\n"
            f"{json.dumps(results, ensure_ascii=False)}\n\n"
            "要求：\n"
            "1. 语言自然连贯，将所有结果编织成一个整体\n"
            "2. 末尾附上一条软性建议（不超过一句），由用户决定是否采纳\n"
            "3. 建议不强制，如'需要的话我也可以帮您...'"
        )

    chunks = []
    q = stream.get(turn_id)
    async for chunk in llm.astream(prompt):
        if chunk.content:
            chunks.append(chunk.content)
            if q:
                await q.put(chunk.content)

    return {"synthesized_response": "".join(chunks)}
