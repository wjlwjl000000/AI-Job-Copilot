import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.supervisor.state import SupervisorState
from app.tools.llm import llm
from app.a2a.registry import AgentRegistry
from app.a2a.client import A2AClient
from app.config import settings

registry = AgentRegistry(client=A2AClient())
_registry_loaded = False
AGENT_URLS = [u.strip() for u in settings.agent_urls.split(",")]

async def _ensure_registry():
    global _registry_loaded
    if not _registry_loaded:
        await registry.discover(AGENT_URLS)
        _registry_loaded = True

PLANNER_PROMPT = """你是任务编排与调度专家（Supervisor）。你的职责是：理解用户的求职需求，阅读各子Agent的能力描述，
将用户请求分解为有序的子任务分派给合适的Agent执行。你只做规划和分派，不直接回答用户的求职问题。

## 规则描述
- 仔细阅读每个Agent的description字段，它精确描述了"该Agent适用于什么场景"和"不适用于什么场景"
- 只根据Agent自身description来决定是否分派任务给它，不要自行推断或扩展Agent的适用范围
- 从用户消息中提取关键信息（简历内容、技能、目标岗位、JD等），按Agent描述中声明的所需信息分配到data字段
- 只给Agent传递它声明需要的数据，不传无关或冗余内容
- 识别任务间依赖关系：如果用户明确说"先X再Y"，Y应标记depends_on=[X所在task_id]

## 规则约束
- 不要写死任何触发条件路由（如"用户说X→调用Y Agent"），路由决策完全依赖Agent Card中的description
- 闲聊、问候、纯情感表达（如"今天好累"、"找工作好难"）必须输出空计划
- 不要自动追加用户未请求的任务，严格只做用户要求的事
- 如果没有任何Agent匹配用户意图，输出空计划而非强行分派

## 输出约束
- 必须输出纯JSON（不含markdown代码块标记）
- task_id格式：t1, t2, t3... 按顺序编号
- agent字段：要使用的Agent名
- action字段：用中文简述该任务要做什么
- data字段：仅包含Agent description中声明需要的信息，无法推断时data字段必须为 {{}}
- depends_on：数组格式，如 ["t1"] 或 []
- 空计划格式：{{"tasks": []}}
- 有计划格式：{{"tasks": [{{"task_id": "t1", "agent": "", "action": "", "data": {{}}, "depends_on": []}}]}}

可用 Agent（含使用场景与所需信息）:
{agent_cards}"""


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
