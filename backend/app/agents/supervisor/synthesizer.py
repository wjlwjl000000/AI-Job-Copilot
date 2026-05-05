import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm


async def synthesizer_node(state: SupervisorState) -> dict:
    prompt = (
        "你是求职助手。基于以下任务结果，生成一段连贯的自然语言回复。\n"
        f"{json.dumps(state['all_results'], ensure_ascii=False)}\n\n"
        "要求：\n"
        "1. 语言自然连贯，将所有结果编织成一个整体\n"
        "2. 末尾附上一条软性建议（不超过一句），由用户决定是否采纳\n"
        "3. 建议不强制，如'需要的话我也可以帮您...'"
    )

    chunks = []
    async for chunk in llm.astream(prompt):
        if chunk.content:
            chunks.append(chunk.content)

    return {"synthesized_response": "".join(chunks)}
