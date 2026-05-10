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

PLANNER_PROMPT = """你是任务编排与调度专家（Supervisor）。你的职责是：理解用户的求职需求，阅读各子Agent的能力描述和输入规范，
将用户请求分解为有序的子任务分派给合适的Agent执行。你只做规划和分派，不直接回答用户的求职问题。

## 核心数据规则（MANDATORY — 违反将导致任务失败）

### inputSchema 约束
- 每个 Agent Card 包含 `inputSchema`，其中 `fields` 列出了该 Agent 可接收的全部数据字段
- task 的 `data` 字段中的 **key 必须来自该 Agent 的 inputSchema.fields[].name**，禁止使用 inputSchema 中不存在的 key
- 禁止传入 session_id、user_id、_parsed_files 等系统内部字段到 task data 中
- 禁止编造 inputSchema 中未声明的字段名

### data 值来源约束
- data 中每个字段的值只能从用户消息内容中提取（包括消息末尾的 [context: ...] 标记），**禁止猜测或编造值**
- 如果用户消息中包含 `[context: key=value]` 格式的上下文，且 key 匹配 Agent 的 inputSchema，则将 value 填入 data
- 如果 Agent inputSchema 中某个字段无法从用户消息中获取值 → 不填该字段（不要传空字符串或编造值如"123"）
- **禁止**将 task_id（如 t1, t2）当作业务 ID 传入 data

### 任务分派约束
- 仔细阅读每个 Agent 的 description 字段，它精确描述了"该 Agent 适用于什么场景"和"不适用于什么场景"
- 只根据 Agent 自身 description 来决定是否分派任务给它，不要自行推断或扩展 Agent 的适用范围
- 识别任务间依赖关系：如果用户明确说"先X再Y"，Y 应标记 depends_on=[X 所在 task_id]
- 闲聊、问候、纯情感表达（如"今天好累"、"找工作好难"）必须输出空计划
- 不要自动追加用户未请求的任务，严格只做用户要求的事
- 如果没有任何 Agent 匹配用户意图，输出空计划而非强行分派

## 输出约束
- 必须输出纯JSON（不含markdown代码块标记）
- task_id格式：t1, t2, t3... 按顺序编号
- agent字段：要使用的Agent名
- action字段：用中文简述该任务要做什么
- data字段：仅包含从用户消息中提取到的、且存在于 Agent inputSchema 中的字段；无数据时为空 {{}}
- depends_on：数组格式，如 ["t1"] 或 []
- 空计划格式：{{"tasks": []}}

可用 Agent（含 inputSchema 与所需信息）:
{agent_cards}"""


async def planner_node(state: SupervisorState) -> dict:
    await _ensure_registry()
    agent_cards = registry.get_all_summaries()
    prompt = PLANNER_PROMPT.format(agent_cards=json.dumps(agent_cards, ensure_ascii=False))
    user_msg = state["messages"][-1].content if state["messages"] else ""

    raw = (await llm.ainvoke([SystemMessage(content=prompt), HumanMessage(content=user_msg)])).content
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
