import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm
from app.a2a.registry import AgentRegistry
from app.a2a.client import A2AClient

registry = AgentRegistry(client=A2AClient())
_registry_loaded = False
AGENT_URLS = [
    "http://profile-agent:8001",
    "http://matching-agent:8002",
    "http://interview-agent:8003",
    "http://support-agent:8004",
]

async def _ensure_registry():
    global _registry_loaded
    if not _registry_loaded:
        await registry.discover(AGENT_URLS)
        _registry_loaded = True

PLANNER_PROMPT = """你是 Supervisor。根据用户意图和 Agent 描述生成执行计划。输出纯 JSON（不要markdown代码块）。

规则:
- 仔细阅读每个 Agent 的 description，它说明了"什么时候用"和"不要用于什么场景"
- 根据触发条件匹配 Agent：用户给简历/技能/目标岗位→profile-agent, 已有画像要搜索/匹配JD→matching-agent, 要面试准备→interview-agent
- 从用户消息中提取关键信息，按各 Agent 描述分配到 data 字段
- 只给 Agent 它需要的信息，不传无关内容
- 闲聊/问候 → tasks: []
- 识别任务依赖：如果用户说'先X再Y'，Y应标记 depends_on=[X所在的agent]
- 不要自动追加用户未请求的任务（软连接原则）

可用 Agent（含使用场景与所需信息）:
{agent_cards}

输出格式:
{{"tasks": [{{"task_id": "t1", "agent": "...", "action": "...", "data": {{...}}, "depends_on": []}}]}}"""


def planner_node(state: SupervisorState) -> dict:
    global _registry_loaded
    if not _registry_loaded:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        loop.run_until_complete(_ensure_registry())
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

    tasks = plan_data.get("tasks", [])
    for i, t in enumerate(tasks):
        if "task_id" not in t:
            t["task_id"] = f"task_{i+1}"

    return {
        "plan": tasks,
        "goal": user_msg,
        "loop_count": 0,
        "max_loops": 3,
        "all_results": {},
    }
