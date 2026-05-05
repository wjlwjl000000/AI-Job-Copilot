import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm


class DummyRegistry:
    def get_all_summaries(self) -> list[dict]:
        return [
            {"name": "profile-agent", "description": "解析简历、构建画像", "skills": []},
            {"name": "matching-agent", "description": "职位匹配、评分、优化", "skills": []},
            {"name": "interview-agent", "description": "面试问题生成、回答评估", "skills": []},
        ]


registry = DummyRegistry()

PLANNER_PROMPT = """你是 Supervisor。根据用户意图生成执行计划，输出纯 JSON（不要markdown代码块）。

规则:
- 如果用户的消息是闲聊、问候、感谢或无明确求职需求 → 返回空计划 {{"tasks": []}}
- 只有当用户明确表达了求职相关需求时，才生成任务
- 识别任务依赖：如果用户说'先X再Y'，Y应标记 depends_on=[X所在的agent]
- 不要自动追加用户未请求的任务（软连接原则）
- 每个任务的 agent 必须是可用 Agent 列表中的名称

可用 Agent:
{agent_cards}

输出格式:
{{"tasks": [{{"agent": "...", "action": "...", "data": {{}}, "depends_on": []}}]}}"""


def planner_node(state: SupervisorState) -> dict:
    agent_cards = registry.get_all_summaries()
    prompt = PLANNER_PROMPT.format(agent_cards=json.dumps(agent_cards, ensure_ascii=False))
    user_msg = state["messages"][-1].content if state["messages"] else ""

    raw = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=user_msg)]).content
    # Parse JSON from LLM output (strip markdown fences if any)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("\n```", 1)[0]
    try:
        plan_data = json.loads(raw)
    except json.JSONDecodeError:
        plan_data = {"tasks": []}

    return {
        "plan": plan_data.get("tasks", []),
        "goal": user_msg,
        "loop_count": 0,
        "max_loops": 3,
        "all_results": {},
    }
