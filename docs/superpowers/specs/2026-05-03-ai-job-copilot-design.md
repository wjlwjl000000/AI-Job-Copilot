# AI Job Copilot — 设计文档

## 概述

AI 求职助手（AI Job Copilot）是一个面向中国求职市场的 Web 应用，覆盖投递全流程，并通过 RAG 提供个性化情感支持。

**目标用户：** 中国求职者（初期为个人工具，后续可 SaaS 化）
**市场：** 中国（BOSS 直聘、拉勾、智联招聘等）
**AI 接入：** 云端大模型 API（DeepSeek/通义千问，可切换）

---

## 技术栈

| 层 | 选型 | 说明 |
|---|------|------|
| 前端 | Vue.js 3 + Vite + Element Plus + Pinia | SPA，国内生态成熟 |
| 后端框架 | FastAPI (Python) | 异步优先，各 Agent 独立 HTTP 服务 |
| Agent 间通信 | Google A2A 协议 (JSON-RPC 2.0) | Agent Card 注册发现 + `tasks/sendMessage` |
| Supervisor 编排 | LangGraph StateGraph | Plan-and-Execute 模式（增量式） |
| Sub-Agent 决策 | LangChain `create_agent()` | 内置 ReAct 模式 |
| SKILL 系统 | .md 文件 + 渐进式信息披露 | 业务资源集合，Agent 按需加载 |
| 流式输出 | LLM `stream()` + `graph.astream()` + FastAPI SSE | 自然语言增量推送 |
| AI 模型 | `ChatOpenAI(model="glm-4-flash")`（智谱AI） | DeepSeek/通义千问可切换 |
| 上下文管理 | 自定义中间件：滑动窗口 + 摘要 | 按消息数量控制窗口 |
| Tool 重试 | LangChain 内置 `ToolRetryMiddleware` | 失败自动重试 |
| 业务数据库 | PostgreSQL | 用户、简历、职位、投递等业务数据 |
| 向量存储 | Chroma，`add_documents()` 一行写入 | 应用启动时连接，JD/经历/画像向量 |
| 部署 | Docker Compose | 每个 Agent 独立容器 |

---

## 多 Agent 架构

### 设计原则

- 按**上下文依赖程度**划分专职 Agent，信息独立，仅通过 A2A 协议传递结构化结果
- **Supervisor**：Plan-and-Execute 模式，仅规划用户当前明确请求的任务
- **Sub-Agent**：ReAct 模式（Think → Act → Observe 循环），确保单任务完成度
- **软连接**：系统各能力之间无强制流程链路，Synthesizer 在回复末尾附上软性建议，由用户决定下一步
- **通信拓扑**：Supervisor ↔ Profile/Matching/Interview（不含 Support）；Sub-Agent 可通过 `call_support_agent` Tool 调用 Support；Supervisor **不可**直接调用 Support；Sub-Agent 之间禁止通信
- **TOOL 绑定在 Agent 上**：`tools=[...]` 是 `create_agent()` 的参数
- **系统 Agent 不可删除**：内置 Agent 为系统骨架，用户可通过前端注册自定义 Agent

### Agent 清单

```
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                          │
│  模式: Plan-and-Execute (LangGraph StateGraph)               │
│  职责: 意图识别 → 生成 Plan → A2A 并行分发(不含Support) →汇总│
│  TOOL: 无（通过 A2A 客户端调用 Sub-Agent，不走 Tool 机制）     │
│  Registry: Profile / Matching / Interview（不含 Support）     │
└──────┬────────────────────────────┬─────────────────────────┘
       │ A2A                       │ A2A
       ▼                           ▼
┌────────────┐             ┌──────────────────┐
│  Profile   │             │   Interview      │
│  Agent     │             │   Agent          │
│ 模式: ReAct│             │ 模式: ReAct       │
│            │             │                  │
│ SKILL:     │             │ SKILL:           │
│ build-     │             │ generate-        │
│  profile   │             │  interview-qs    │
│            │             │ evaluate-        │
│            │             │  answer          │
│ TOOL:      │             │                  │
│ parse_     │             │ TOOL:            │
│  document  │             │ db_read/write    │
│ db_write   │             │ call_support_    │
│ read_      │             │  agent           │
│  profile   │             │ load_skill       │
│ save_      │             │ react            │
│  resume    │             │ read_qa_queue    │
│ confirm_   │             │                  │
│  overwrite │             │                  │
│ chroma_    │             │                  │
│  insert    │             │                  │
│ call_      │             │                  │
│  support   │             │                  │
│ load_skill │             │                  │
│ react      │             │                  │
│            │             │                  │
│ call_      │             │ call_            │
│  support  ─┼──┐          │  support  ───┐   │
│            │  │          │              │   │
│ 无上游依赖  │  │          │ 依赖 Matching│   │
└──┬─────────┘  │          └──────┬───────┘   │
   │            │                 │           │
   ▼            │                 │           │
┌────────────┐  │                 │           │
│  Matching  │  │                 │           │
│  Agent     │  │                 │           │
│ 模式: ReAct│  │                 │           │
│            │  │                 │           │
│ SKILL:     │  │                 │           │
│ match-jobs │  │                 │           │
│ score-     │  │                 │           │
│  match     │  │                 │           │
│ optimize-  │  │                 │           │
│  resume    │  │                 │           │
│            │  │                 │           │
│ TOOL:      │  │                 │           │
│ db_read/   │  │                 │           │
│  write     │  │                 │           │
│ chroma_    │  │                 │           │
│  query     │  │                 │           │
│ web_search │  │                 │           │
│ call_      │  │                 │           │
│  support  ─┼──┘                 │           │
│ load_skill │                    │           │
│ react      │                    │           │
│            │                    │           │
│ 依赖       │                    │           │
│ Profile    │                    │           │
└────────────┘                    │           │
   │                              │           │
   └──────────────────────────────┴───────────┘
                     │
                     ▼
       ┌────────────────────────────┐
       │       Support Agent        │
       │      模式: ReAct            │
       │      SKILL: comfort-user,  │
       │       daily-checkin        │
       │      TOOL: chroma_query,   │
       │       db_read, load_skill, │
       │       react                │
       │                            │
       │  ← 仅被 Profile/Matching/  │
       │     Interview 通过 A2A 调用 │
       │  ← Supervisor 不可直接调用  │
       │  结果嵌入调用者的返回值     │
       └────────────────────────────┘
```

---

## A2A 协议设计（JSON-RPC 2.0 标准）

### Agent Card

每个 Sub-Agent 暴露标准 A2A Agent Card 端点：

```
GET /.well-known/agent-card.json → {
  "a2a_version": "1.0",
  "id": "urn:agent:copilot:matching",
  "name": "Matching Agent",
  "description": "负责职位匹配、匹配度评分和简历优化。当用户需要搜索匹配职位、评估与JD的匹配程度、或优化简历时调用。",
  "url": "http://matching-agent:8001",
  "version": "1.0.0",
  "capabilities": { "streaming": true, "pushNotifications": false },
  "skills": [
    {
      "id": "match-jobs",
      "name": "职位匹配搜索",
      "description": "基于用户画像向量在Chroma中语义搜索匹配的职位",
      "examples": ["帮我搜搜适合我的职位", "有什么岗位推荐"]
    },
    {
      "id": "score-match",
      "name": "简历职位匹配度评估",
      "description": "多维度评估简历与JD的匹配度，输出评分和差距分析",
      "examples": ["我和这个岗位匹配吗", "评估下匹配度"]
    },
    {
      "id": "optimize-resume",
      "name": "简历优化",
      "description": "针对特定JD生成优化版简历，匹配度低于0.6时自动触发",
      "examples": ["帮我优化简历", "针对这个岗位改一下简历"]
    }
  ],
  "defaultInputModes": ["text", "application/json"],
  "defaultOutputModes": ["text", "application/json"]
}
```

**Agent Card 的双重作用：**
1. Supervisor 通过 Card `skills[].description` 判断"何时调用该 Agent"
2. Sub-Agent 内部的 SKILL.md 保留，用于 ReAct 循环中的渐进式信息加载

**注册机制：**
- Supervisor 启动时广播 → 各 Agent 返回 Card → 写入 Registry
- 前端注册界面：用户输入 Agent URL → Supervisor 拉取 `/.well-known/agent-card.json` → 验证 → 持久化
- 系统内置 Agent 不可删除，用户注册的 Agent 可管理

### 通信协议（JSON-RPC 2.0 + Task 状态机）

```
# 请求 (Supervisor → Sub-Agent)
POST {agent_url}/
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tasks/sendMessage",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {"type": "text", "text": "评估简历与岗位匹配度"},
        {"type": "application/json", "content": {"profile_id": "p_42", "job_id": "j_xxx"}}
      ]
    }
  }
}

# 响应 (Sub-Agent → Supervisor)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "task-abc123",
    "status": {"state": "completed"},         # 见下方状态机
    "artifacts": [
      {"type": "application/json", "content": {"overall": 0.45, ...}}
    ]
  }
}
```

**Task 状态机：**
```
submitted → working → completed
                ↓          ↓
           input-required  failed
                           canceled
```
- `completed` / `failed` / `canceled` → 终端状态
- `input-required` → 需要用户确认或补充信息（HITL 中断）
- Support Agent 永远返回 `completed`，不会返回 `input-required`

**SSE 流式事件：**
- `messageDelta` — 增量文本块（Synthesizer 逐字输出）
- `taskStatusUpdate` — Task 状态变更
- `taskArtifactUpdate` — 产出物增量

### 中断处理（A2A `input-required` → LangGraph `interrupt()`）

**Sub-Agent 内部 — 统一循环：**

Profile Agent 的 `handle_task` 不区分首次/resume——统一为「构建输入 → ainvoke → 检查中断」循环：

```
handle_task(request):
  session = _task_sessions.pop(task_id, None)  # 判断首次 or resume
  if session → Command(resume=...) else → 初始消息
  result = ainvoke(input, config)
  if __interrupt__ → 存 session → return input-required  ← 等待下次调用
  else → return completed
```

N 个中断 = N 次 A2A 往返，每次调用走同一路径，无需预设中断次数。

**Executor 层面 — while 循环处理串行中断：**

```python
if result.result.status.state == "input-required":
    task_result = result
    while True:
        msg = task_result.result.status.message
        user_answer = interrupt({"type": "user_question", "question": msg, ...})
        task_result = await a2a_client.send_message(
            agent_url=..., message={"text": user_answer["answer"]},
            task_id=task_result.result.id,
        )
        if task_result.result.status.state == "input-required":
            continue   # 二次中断 → 再次循环（用户看到一个接一个的气泡）
        # completed → 收集 artifact → break
```

N 个中断 = N 次 `while` 循环迭代，每次 `interrupt()` 暂停 Supervisor 图。用户点一次按钮解一个中断，解完后 Agent 如果还有下一个中断，executor 自动再次 `interrupt()`，前端出现新气泡。Agent 返回 `completed` 后循环结束。

并行中断（多个 Agent 同时返回 input-required）由 `asyncio.as_completed` 顺序串行化处理，先到先中断。

---

## Supervisor Agent：Plan-and-Execute

Supervisor 内部使用 LangGraph StateGraph 实现 Plan-and-Execute 模式。Supervisor 不直接调用 TOOL，而是通过 A2A 客户端分发任务。

### 状态定义

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class SupervisorState(TypedDict):
    user_id: str
    session_id: str
    messages: Annotated[list, add_messages]
    goal: str                           # 用户原始目标
    plan: list[dict]                    # [{task_id, agent, action, data, depends_on}]
    all_results: dict                   # {task_id: result}
    synthesized_response: str
    loop_count: int                     # 当前循环次数
    max_loops: int                      # 最大循环次数 (默认3)
    should_continue: bool               # Replanner → Executor 路由标志
    paused_tasks: list[dict]            # 已中断任务 [{tid, task_id_on_agent, msg, agent}]
                                        # LangGraph interrupt() 触发重放时，executor 跳过
                                        # HTTP 调用但保持 interrupt() 可达
```

### 图结构

```
用户消息
  │
  ▼
[Planner]          ● 分析意图 → 生成初始 Plan
  │                ● 基于 Agent Card Registry
  │
  ▼
┌─[Executor]─────┐ ● 并行 A2A 执行 Plan 中所有任务
│   asyncio      │ ● asyncio.as_completed() 逐个收结果
│   .as_completed│ ● input-required → interrupt() 立即挂起
│   () loop      │    等待用户回复 → 恢复 → 继续收结果
│                │ ● 全部完成 → 返回 results
└────────────────┘
  │
  ▼
[Replanner]        ● 基于 results + goal，LLM 决策
  │                ● rewite → 返回修订 Plan → Executor
  │                ● done   → Synthesizer
  │
  ├──(rewrite)──→ Executor
  │
  └──(done)──→ [Synthesizer] → SSE 流式输出
```

### 关键节点

```python
# ---- Planner ----
def planner_node(state: SupervisorState):
    """基于用户消息 + Agent Card Registry，生成初始执行计划"""
    agent_cards = registry.get_all_summaries()
    # Profile/Matching/Interview 的 description（不含 Support）
    
    plan = llm.with_structured_output(PlanSchema).invoke([
        SystemMessage(
            "你是 Supervisor。根据用户意图，从可用 Agent 中选择，生成执行计划。"
            f"\n可用 Agent:\n{json.dumps(agent_cards, ensure_ascii=False)}"
        ),
        *state["messages"],
    ])
    return {
        "plan": plan.tasks,
        "goal": state["messages"][-1].content,
        "loop_count": 0,
        "max_loops": 3,
        "all_results": {},
    }


# ---- _process_interrupt_loop (串行中断循环) ----
async def _process_interrupt_loop(task, tid, task_id_on_agent, msg, state):
    """中断循环：interrupt → 用户回复 → send_message → 直到 completed"""
    task_id = task_id_on_agent
    question = msg
    while True:
        user_answer = interrupt({
            "type": "user_question", "question": question, "task_id": task_id,
        })
        text_to_agent = user_answer.get("answer", "") if isinstance(user_answer, dict) else str(user_answer)
        try:
            task_result = await a2a_client.send_message(
                agent_url=_agent_url(task["agent"]),
                message={"role": "user", "parts": [{"type": "text", "text": text_to_agent}]},
                task_id=task_id,
            )
        except Exception:
            state["all_results"][tid] = [{"error": "agent_resume_failed"}]
            return
        if task_result.result and task_result.result.status.state == "input-required":
            task_id = task_result.result.id
            question = task_result.result.status.message or "请提供更多信息"
            continue   # 二次中断 → 继续循环
        if task_result.result and task_result.result.artifacts:
            state["all_results"][tid] = [a.content for a in task_result.result.artifacts]
        else:
            state["all_results"][tid] = []
        return


# ---- Executor (LangGraph interrupt 重放感知) ----
async def executor_node(state: SupervisorState):
    """
    并行 A2A + while 循环串行中断。
    关键：LangGraph interrupt() 触发 checkpoint 保存→图重放。
    paused_tasks 确保重放时跳过 HTTP 调用但保持 interrupt() 可达。
    """
    paused = state.get("paused_tasks", [])
    paused_ids = {p["tid"] for p in paused}

    # 新任务：排除已完成 + 已暂停
    new_tasks = [t for t in state["plan"]
                 if t.get("task_id", t["agent"]) not in state["all_results"]
                 and t.get("task_id", t["agent"]) not in paused_ids]

    session_id = state.get("session_id", "")
    running = [asyncio.create_task(_execute_task(t, session_id, a2a_client)) for t in new_tasks]

    # ── 新任务 ──
    for coro in asyncio.as_completed(running):
        task, result = await coro
        tid = task.get("task_id", task["agent"])
        if result is None:
            state["all_results"][tid] = [{"error": "agent_unavailable"}]
            continue
        if result.result and result.result.status.state == "input-required":
            state["paused_tasks"] = state.get("paused_tasks", []) + [{
                "tid": tid, "task_id_on_agent": result.result.id,
                "msg": result.result.status.message or "请提供更多信息",
                "agent": task["agent"],
            }]
            await _process_interrupt_loop(task, tid, result.result.id,
                                          result.result.status.message, state)
            state["paused_tasks"] = [p for p in state.get("paused_tasks", []) if p["tid"] != tid]
            task["data"] = {}
        elif result.result and result.result.status.state == "completed":
            state["all_results"][tid] = [a.content for a in result.result.artifacts] if result.result.artifacts else []
            task["data"] = {}

    # ── 暂停任务（重放路径）──
    for pt in paused:
        task = next((t for t in state["plan"] if t.get("task_id", t["agent"]) == pt["tid"]), {"agent": pt["agent"]})
        await _process_interrupt_loop(task, pt["tid"], pt["task_id_on_agent"], pt["msg"], state)
        state["paused_tasks"] = [p for p in state.get("paused_tasks", []) if p["tid"] != pt["tid"]]

    all_failed = all(...)
    result = {"all_results": state["all_results"]}
    if all_failed:
        result["should_continue"] = False
    return result


# ---- Replanner (循环出口 + ReWrite) ----
def replanner_node(state: SupervisorState):
    """
    基于 goal + all_results，LLM 决策：
    - done：任务完成，目标达成 → Synthesizer
    - rewrite：Plan 中还有未完成步骤 → 回 Executor
    """
    response = llm.with_structured_output(ReplanSchema).invoke([
        SystemMessage(
            "你是 Replanner。基于目标和已执行结果，决定是否继续。"
            "1. 所有步骤完成 → done"
            "2. 还有未执行步骤 → rewrite（修订 Plan）"
            "3. 不要自动追加用户未请求的任务（软连接原则）"
            f"第{state['loop_count']}轮，最多{state['max_loops']}轮。"
        ),
        HumanMessage(f"目标: {state['goal']}"),
        HumanMessage(f"原始 Plan: {state['plan']}"),
        HumanMessage(f"结果: {json.dumps(state['all_results'])}"),
    ])
    
    if response.action == "done":
        return {"should_continue": False}
    else:
        return {
            "should_continue": True,
            "plan": response.revised_plan,
            "loop_count": state["loop_count"] + 1,
        }


# ---- Synthesizer (流式自然语言输出 + 软性建议) ----
async def synthesizer_node(state: SupervisorState):
    """
    汇总 all_results → LLM stream() 逐 chunk 输出 + 末尾附软性建议。
    """
    prompt = (
        "你是求职助手。基于以下结果生成回复：\n"
        f"{json.dumps(state['all_results'])}\n\n"
        "要求：1. 语言连贯自然 2. 末尾附一条下一步建议（不超过一句）"
        "3. 建议是软性的，由用户决定是否采纳"
    )
    
    # 流式生成，逐 chunk yield
    chunks = []
    async for chunk in llm.astream(prompt):
        chunks.append(chunk.content)
        # 每个 chunk 通过 SSE 推送给前端
    
    return {"synthesized_response": "".join(chunks)}


# ---- 路由 ----
def after_executor(state: SupervisorState) -> str:
    """Executor 返回后 → Replanner（统一入口，不区分 priority）"""
    return "replanner"

def should_continue(state: SupervisorState) -> str:
    """Replanner 返回后 → 继续 or 结束"""
    if state["loop_count"] >= state["max_loops"]:
        return "synthesizer"  # 兜底
    if state["should_continue"]:
        return "executor"
    return "synthesizer"


# ---- 构建图 ----
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(SupervisorState)

builder.add_node("planner", planner_node)
builder.add_node("executor", executor_node)
builder.add_node("replanner", replanner_node)
builder.add_node("synthesizer", synthesizer_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "replanner")
builder.add_conditional_edges("replanner", should_continue, {
    "executor": "executor",
    "synthesizer": "synthesizer",
})
builder.add_edge("synthesizer", END)

graph = builder.compile(checkpointer=MemorySaver())
```

### Executor 内部中断流程

```
Executor 进入
  │
  ├─ 并行发出 A2A 调用 (Matching, Profile, Interview...)
  │
  ├─ asyncio.as_completed() 循环:
  │
  │   Profile 返回 state: "input-required" (2s)（如 save_resume HITL 中断）
  │   │
  │   ├─ user_answer = interrupt({...})
  │   │    → 图挂起，MemorySaver 保存状态
  │   │    → asyncio 协程存活（未取消）
  │   │    → SSE yield __interrupt__ 事件给前端
  │   │    → 等待用户输入...
  │   │
  │   │  用户回复 → graph.astream(Command(resume={"answer": "..."}), config)
  │   │    → 图从此处恢复
  │   │    → user_answer = {"answer": "..."}
  │   │    → A2A 发回原 Agent 继续（同一 task_id）
  │   │    → 继续 asyncio.as_completed() 循环
  │   │
  │   Agent 连接失败 → 记录 error，继续收其他结果
  │   │
  │   Matching 返回 state: "completed" (30s) → 直接写入 results
  │
  └─ 全部完成（或全部 error → should_continue=False）→ return results
```

**为什么不会阻塞：**
- `asyncio.as_completed()` 顺序是"谁先完成谁先处理"
- Profile 2秒返回 `input-required` → `interrupt()` 立即触发
- 未完成的 asyncio 协程不丢失
- `interrupt()` 的返回值就是用户回复，无需额外 state 字段
- Agent 不可用时记录 error 标记，不阻塞整体流程

### 流式输出

```python
@router.post("/api/agent/chat")
async def agent_chat(request: ChatRequest):
    initial_state = {
        "user_id": request.user_id,
        "messages": [HumanMessage(content=request.message)],
        "plan": [],
        "all_results": {},
        "loop_count": 0,
        "max_loops": 3,
    }
    
    config = {"configurable": {"thread_id": request.turn_id or str(uuid.uuid4())}}
    
    async def event_stream():
        interrupted = False
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            if event.get("__interrupt__"):
                interrupted = True
                # __interrupt__ 是 Interrupt 对象，提取 .value 后再序列化
                iv = event["__interrupt__"]
                if not isinstance(iv, (list, tuple)):
                    iv = [iv]
                payload = iv[0].value if hasattr(iv[0], "value") else iv[0]
                yield f"data: {json.dumps(payload)}\n\n"
            elif event.get("synthesizer"):
                content = event["synthesizer"]["synthesized_response"]
                yield f"data: {json.dumps({'type': 'response', 'content': content})}\n\n"
        
        # 中断后不发送 done，等待用户回复后在新请求中恢复
        if not interrupted:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")


# 用户回复时恢复
@router.post("/api/agent/chat/resume")
async def resume_chat(request: ResumeRequest):
    config = {"configurable": {"thread_id": request.turn_id}}
    async for event in graph.astream(
        Command(resume={"answer": request.message}),  # resume 值 = interrupt() 返回值
        config,
        stream_mode="updates"
    ):
        ...  # 同上
```

---

## Sub-Agent：ReAct 模式

每个 Sub-Agent 用 `create_agent()` 创建，自带 ReAct 模式。TOOL 通过 `tools=[...]` 绑定在 Agent 上。

**LLM 配置（所有 Agent 共享）：**
```python
from langchain_openai import ChatOpenAI

# 主 LLM：智谱AI (glm-4-flash)
llm = ChatOpenAI(
    model="glm-4-flash",
    api_key=settings.zhipuai_api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    streaming=True,
)

# 备选：ChatAnywhere (gpt-5-mini)，已配置可切换
# llm = ChatOpenAI(model="gpt-5-mini", api_key=..., base_url="https://api.chatanywhere.tech")
```

### Profile Agent

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware, HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

PROFILE_SYSTEM_PROMPT = """你是简历解析与求职画像构建专家。
可用 SKILL: build-profile

## SKILL First 规则
- 收到任务后第一步必须调用 load_skill(skill_name="build-profile") 加载完整工作流
- 严格按加载的工作流逐步执行，不跳过、不自行变更步骤顺序
- 工作流所有步骤执行完毕 → 以自然语言输出全面、具体的总结

## 约束
- 只做简历解析和画像构建。不做职位匹配、面试、情感支持。
- 全程中文，不编造。"""

profile_agent = create_agent(
    model=llm,
    system_prompt=PROFILE_SYSTEM_PROMPT,
    tools=[parse_document, read_profile, db_write, save_resume,
           confirm_overwrite, chroma_insert, call_support_agent,
           load_skill, react],
    middleware=[
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
        HumanInTheLoopMiddleware(interrupt_on={"save_resume": True,
                                                "confirm_overwrite": True}),
    ],
    checkpointer=InMemorySaver(),
)
```

### Matching Agent

```python
MATCHING_SYSTEM_PROMPT = """你是职位匹配与简历优化专家。可用技能: match-jobs, score-match, optimize-resume。

ReAct 规则：Think → Act → Observe 循环。每步 Act 调用工具。任务未完成 → react() 继续。

## 规则
- 匹配度 < 0.6 → 主动调 call_support_agent 获取经历分享
- 不要做首次画像构建（Profile Agent 职责）
- 优化简历时必须保留真实经历，不得虚构或夸大"""

matching_agent = create_agent(
    model=llm,
    system_prompt=MATCHING_SYSTEM_PROMPT,
    tools=[db_read, db_write, chroma_query, web_search,
           call_support_agent, load_skill, react],
    middleware=[
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

### Interview Agent / Support Agent

同模式，`create_agent()` + 各自的 `tools` + 占位符 system_prompt。

**Support Agent 特别注意：** 永远返回 `completed`，不生成 `input-required`。

### 关键说明

- **TOOL 绑定于 Agent**：`tools=[...]` 传给 `create_agent()`
- **ReAct 是内置的**：`create_agent()` 默认 ReAct，不手动写循环
- **SKILL 按需加载**：Agent 通过 `load_skill(skill_name)` Tool 在 ReAct 循环中自主加载 SKILL.md 完整工作流，无需中间件预填充
- **`SlidingWindowMiddleware`**：自定义，按消息数量控制窗口。窗口内保留原文，窗口外自动生成摘要
- **`ToolRetryMiddleware`**：LangChain 内置
- **`HumanInTheLoopMiddleware`**：LangChain 内置，Profile Agent 用于 `save_resume` / `confirm_overwrite` 的人机确认中断。**依赖 Python 3.11+**，因 `asyncio.create_task()` 在 3.11 起自动复制 `contextvars`
- **`call_support_agent`**：A2A 封装 Tool，Sub-Agent 间唯一通信例外

---

## SKILL 与 TOOL

### TOOL（原子操作层，绑定于 Agent）

| Tool | 功能 | 绑定于 |
|------|------|--------|
| `parse_document` | 解析已上传简历文件，返回 {table, data, errors} | Profile |
| `read_profile` | 查询 user_profiles 表 | Profile |
| `save_resume` | 保存原始简历文本到 resumes 表（触发 HITL 中断） | Profile |
| `confirm_overwrite` | 确认覆盖已有画像（触发 HITL 中断） | Profile |
| `db_read` | 读数据库 | Matching, Interview, Support |
| `db_write` | 写数据库（创建/更新） | Profile, Matching, Interview |
| `chroma_query` | 向量相似度检索 | Matching, Support |
| `chroma_insert` | 写入向量到 Chroma | Profile |
| `web_search` | 搜索外部职位信息（初期返回空列表） | Matching |
| `call_support_agent` | A2A 调用 Support Agent | Profile, Matching, Interview |
| `read_qa_queue` | 读面试问答队列 | Interview |
| `react` | ReAct 思考循环占位，当前无合适工具时继续推理 | 全部 Agent |
| `load_skill` | 按需加载 SKILL.md 完整工作流内容 | 全部 Agent |

### SKILL（业务资源层，.md 文件）

**格式：**

```markdown
---
name: skill-name
description: 非结构化描述，说明什么情况下、什么时候应该使用这个SKILL
---

# Skill 标题

## 目标
简要描述这个技能要完成什么

## 工作流程
1. 步骤一 → 调用的 Tool
2. 步骤二 → 调用的 Tool
...

## 输出格式
描述返回结果的格式和字段说明

## 关联
- 某些情况下建议或需要加载的其他 SKILL
```

**清单与归属：**

| SKILL 文件 | 归属 Agent | description（何时使用） |
|-----------|-----------|----------------------|
| `build-profile.md` | Profile | 当简历解析完成、用户补充信息、或画像需要更新时 |
| `match-jobs.md` | Matching | 当用户希望基于画像搜索和发现匹配的职位机会时 |
| `score-match.md` | Matching | 当用户想了解简历与某个岗位的匹配程度时 |
| `optimize-resume.md` | Matching | 当需要针对特定JD优化简历措辞、或匹配度低于0.6时 |
| `generate-interview-qs.md` | Interview | 当用户获得面试机会，需要针对性生成面试问题时 |
| `evaluate-answer.md` | Interview | 当用户完成模拟面试回答，需要评估质量和改进建议时 |
| `comfort-user.md` | Support | 当用户遭遇被拒、匹配度低、面试失败或需要鼓励和经历分享时 |
| `daily-checkin.md` | Support | 当用户进行每日签到、系统定时触发求职日报时 |

### 渐进式信息披露

```
Sub-Agent 启动
  → system prompt 中只列出本 Agent 的 SKILL name + description 摘要（每个几十 token）

Supervisor 发来任务
  → Agent 的 ReAct 循环中，LLM 根据 description 判断需要哪个 SKILL
  → 调用 load_skill(skill_name) Tool → 加载该 SKILL 完整 body → 注入上下文
  → Agent 按 SKILL 工作流程执行，调用 TOOL
  → 任务完成输出 Final Answer，下一轮对话自动卸载 SKILL body

  → 执行中 LLM 判定需要新 SKILL → load_skill → 继续 → 最终卸载
```

---

## 关键场景实现逻辑

### 场景一：新用户上传简历

```
0. 前端上传简历文件:
   POST /api/agent/parse-file (multipart/form-data)
   → MinerU 解析 PDF → 返回 file_id + char_count
   → 文本缓存到后端 session 级别 _parsed_files

1. 前端 POST /api/agent/chat (SSE)
   {message: "帮我构建求职画像", session_id: "xxx"}

2. Supervisor Planner:
   基于 Agent Card Registry 生成 Plan（不含 Support）:
     [
       {task_id: "t1", agent: "Profile Agent", action: "构建求职画像",
        data: {session_id: "xxx"}},
       {task_id: "t2", agent: "Matching Agent", action: "搜索匹配职位",
        data: {session_id: "xxx"}}
     ]

3. Supervisor Executor 并行 A2A:
   发出 Profile + Matching（Planner 通过 depends_on 标记 t2 依赖 t1）

4. Profile Agent (ReAct) 执行 build-profile SKILL:
   Thought: "需要构建画像" → load_skill("build-profile")
   Act: read_profile() → 空，无已有画像
   Act: parse_document() → LLM 将解析文本转为结构化 JSON
   Act: chroma_insert(collection="profiles", ...) → 向量化
   Act: db_write(table="user_profiles", data={...}) → 写入 PostgreSQL
   Act: save_resume(messages="...-xxx") → 触发 HITL 中断，前端弹窗询问
   → Agent 返回 input-required，Supervisor Executor interrupt()
   → 用户确认 → resume → save_resume 继续 → Final Answer
   → {status: completed, result: {profile_id, skill_tags, ...}}

5. Matching Agent (ReAct) 执行 match-jobs SKILL:
   Thought: "搜索匹配职位" → load_skill("match-jobs")
   Act: db_read("user_profiles") → 获取技能标签
   Act: web_search(query=..., source="boss") → 搜索外部职位（初期返回空列表）
   Act: react() → 无外部结果时用 chroma_query 本地匹配
   → {status: completed, result: {matches: [...]}}

   Matching 内部发现是首次使用:
   Act: call_support_agent(trigger="onboarding")
   # Support Agent (ReAct): comfort-user → chroma_query → react
   # → {story, encouragement} 嵌入 Matching result 中

6. Executor 全部完成 → Replanner:
   判断: 目标达成 → done

7. Synthesizer:
   汇总 Profile + Matching（内含 Support 内容）
   "简历已解析，技能包括 Python、FastAPI、Vue.js。
    匹配到3个职位...欢迎加入，我们一起努力！"
   → SSE 推送
```

### 场景二：用户请求匹配度评估（含 Replanner ReWrite）

```
1. 前端: {message: "我和这个岗位匹配度多少?", context: {job_id: "xxx"}}

2. Supervisor Planner:
   Plan: [{task_id: "t1", agent: "Matching Agent", action: "评估匹配度", data: {job_id: "xxx"}}]

3. Executor → Matching Agent (ReAct):
   Thought: "评估匹配度" → load_skill("score-match")
   Act: db_read(table="user_profiles") → 获取技能、经验、学历
   Act: db_read(table="jobs", filters={"id": "xxx"}) → 获取 JD
   Thought: 四维度对比评分（技能/经验/学历/薪资）→ overall=0.45，偏低
   
   Thought: "匹配度低，应生成优化版并获取鼓励"
   Act: load_skill("optimize-resume") → 按工作流优化
   Thought: 对照 JD 调整措辞，仅改写不编造
   Act: db_write(table="resumes", data={...base_version: false...})
   Act: call_support_agent(trigger="low_match", context={overall: 0.45})
   → {state: "completed", result: {overall: 0.45, gaps: [...], 
        optimized_resume_id: "...", support_content: {...}}}

4. Executor → Replanner:
   Replanner 分析: 初始 Plan 只有 score，但 Matching 返回了优化版简历。
   匹配度低(0.45)，优化版已生成，已有鼓励内容。目标达成 → done。

5. Synthesizer:
   "匹配度 45%，主要差距在 LangChain 经验...
    已生成优化版简历。这里有一个相似经历：3个月前..."
   → SSE 推送

# 注：如果 Replanner 发现需要追加任务（如匹配度低但未生成优化版），
#   会 rewrite Plan，路由回 Executor 继续执行
```

### 场景三：HITL 中断（Sub-Agent 需要用户确认）

```
时间线:
  0s: Executor 并行发出 Profile:build / Matching:match
  2s: Profile 返回 input-required

1. Executor asyncio.as_completed() 收到 Profile 返回:
   Profile Agent 的 HumanInTheLoopMiddleware 触发中断
   → {state: "input-required", message: "是否保存当前解析的简历文件-xxx"}

2. Executor 调用 interrupt():
   → LangGraph 图挂起（Matching 的 asyncio 协程仍在执行）
   → MemorySaver 保存状态
   → LangGraph astream yield __interrupt__ 事件
   → 后端提取 Interrupt.value → 通过 SSE 推送给前端
   → 图暂停，等待...

3. 前端收到 interrupt 事件 → 在消息列表中渲染系统气泡:
   "是否保存当前解析的简历文件-xxx"
   [同意] [拒绝]
   → 用户点击「同意」

4. 前端调用 resumeChat("是") → POST /api/agent/chat/resume {message: "是", session_id: "xxx"}

5. 后端 event_stream（新请求）:
   graph.astream(Command(resume={"answer": "是"}), config) → 图从 interrupt() 处恢复

6. Executor 恢复后:
   → A2A Profile（同一 task_id）: {text: "是"}
   → Profile Agent 的 HITL 中间件收到 resume={"decisions": [{"type": "approve"}]}
   → save_resume 继续执行 → 输出自然语言总结
   → {state: "completed", result: {profile_id, ...}}

7. 继续等待 Matching 完成（可能已返回，直接取结果）
   Executor 全部完成 → Replanner → done → Synthesizer → SSE 响应
```

### 场景四：投递被拒，自动触发

```
1. PUT /api/applications/{id} {status: "rejected"}
   → FastAPI 处理后自动向 Supervisor 发送事件

2. Supervisor Planner:
   识别: 被拒事件
   Plan（不含 Support）:
     [{task_id: "t1", agent: "Matching Agent", action: "搜索新职位", data: {}}]

3. Matching Agent (ReAct):
   Thought: "投递被拒，搜索新职位"
   Act: chroma_query(profile_embedding, "jobs") → 5个匹配
   
   Thought: "用户可能需要鼓励"
   Act: call_support_agent(trigger="rejected", job_id)
   # Support Agent (ReAct): comfort-user → chroma_query("被拒 同行业") → Thought 生成鼓励
   # → {story, encouragement}
   Observe: "鼓励内容已获取"
   
   → {priority: false, result: {matches: [...], support_content: {...}}}

4. Executor 完成 → Replanner: done → Synthesizer:
   "不要气馁！求职路上被拒是常事...这里有相似经历：...
    另外为您匹配到 5 个新职位，看看有没有合适的。"
   → SSE 推送
```

---

## 数据模型

### PostgreSQL（业务数据）

```
User (用户)
  email, password_hash, created_at

UserProfile (求职画像)
  id: uuid                # 唯一标识符
  name: str               # 用户姓名
  contact: jsonb          # {phone, email}
  basic: jsonb            # {age, gender, ethnicity, hometown, political}
  education: jsonb        # [{degree, school, major, period}]
  skills: jsonb           # [{name, level, evidence}]
  projects: jsonb         # [{name, role, description, content, tech_stack, achievements}]
  organization: jsonb     # [{name, duties, achievements}]
  work_years: int
  target: jsonb           # {cities, salary_range, industry, roles}
  scores: jsonb           # {competitiveness, market_match, completeness}
  summary: text           # 个人简介/自述

Resume (简历版本)
  user_id → User
  title: str             # 版本名称
  base_version: bool     # 是否基础版本
  target_role: str       # 目标岗位
  content: jsonb         # 结构化内容
  file_path: str         # 原始文件
  match_scores: jsonb    # 各 JD 的匹配评分历史

Job (职位)
  source: str            # boss/lagou/manual
  job_id: str            # 平台职位ID
  jd_content: text       # 职位描述原文
  requirements: jsonb    # [{skill, level, required}, ...]
  company: str
  salary_range: str
  city: str

Application (投递记录)
  user_id → User
  resume_id → Resume
  job_id → Job
  status: enum           # planned/applied/screening/interview/offer/rejected
  timeline: jsonb        # [{status, time, note}, ...]
  notes: text

Interview (面试记录)
  application_id → Application
  questions: jsonb       # [{"id":"q1","question":"...","type":"project_deep_dive","focus":"...","tips":"...","answer":null,"feedback":null}, ...]
  overall_feedback: text
  weaknesses: jsonb      # [{topic, suggestion}, ...]
  status: str            # "in_progress" | "completed"

ExperienceStory (经历故事)
  tags: jsonb            # {industry, role, years, outcome}
  content: text
  source: str            # crawled/user_contributed
  source_url: str
  is_anonymous: bool
  approved: bool
```

### Chroma（向量存储）

| Collection | 存储内容 | 用途 |
|-----------|---------|------|
| `jobs` | JD 文本 | Matching Agent 语义匹配 |
| `stories` | 经历故事文本 | Support Agent RAG 检索 |
| `profiles` | 用户画像摘要文本 | Support Agent 精准匹配相似经历 |

---

## API 设计

### REST API（确定性操作）

#### 画像
- `POST /api/profile/analyze` — 上传简历，解析生成画像
- `GET /api/profile` — 获取当前画像
- `PUT /api/profile` — 更新画像

#### 简历
- `GET /api/resumes` — 简历版本列表（从 PostgreSQL 读取）
- `GET /api/resumes/{id}` — 简历详情（含 raw_text 原文）
- `GET /api/resumes/{id}/file` — 返回原始 PDF/文件（浏览器直接打开）
- `DELETE /api/resumes/{id}` — 删除版本（同时删除磁盘文件）

#### 职位
- `GET /api/jobs/{id}` — 职位详情
- `POST /api/jobs` — 手动录入职位

#### 投递
- `POST /api/applications` — 创建投递
- `GET /api/applications` — 投递列表（支持状态筛选）
- `PUT /api/applications/{id}` — 更新投递状态（状态变更自动触发 Agent）
- `GET /api/applications/stats` — 统计数据

#### 面试
- `GET /api/interviews/{id}` — 面试记录详情（含完整 Q&A 队列）
- `PUT /api/interviews/{id}/questions/{qid}` — 提交单个问题的回答

### A2A 端点（标准协议）

- `GET /.well-known/agent-card.json` — 各 Sub-Agent 的 Agent Card
- `POST /` — JSON-RPC 2.0 `tasks/sendMessage`（向 Sub-Agent 提交任务）
- `GET /tasks/{task_id}` — 查询 Task 状态
- `POST /api/agent/registry` — 注册新 Agent（前端提交 Agent URL）
- `GET /api/agent/registry` — 列出已注册的 Agent

### Agent 对话接口

- `POST /api/agent/chat` — 与 Supervisor 对话（SSE 流式）
  - 请求：`{message: str, session_id?: str, turn_id?: str}`
  - SSE 事件：
    - `{"type": "user_question", ...}` — HITL 中断（前端渲染为系统气泡 + [同意]/[拒绝]）
    - `{"type": "response", "content": "..."}` — Synthesizer 流式文本
    - `{"type": "done"}` — 完成
- `POST /api/agent/chat/resume` — 回复中断问题（同样 SSE 流式，支持二次中断）
  - 请求：`{message: str, session_id?: str, turn_id?: str}`

### 文件解析接口

- `POST /api/agent/parse-file` — 上传简历文件（MinerU 解析为文本）
  - 请求：`multipart/form-data {file, session_id?}`
  - 响应：`{status: "ok", file_id, filename, char_count}`
- `DELETE /api/agent/parse-file/{file_id}` — 删除已解析文件
- `GET /api/agent/parse-file/{file_id}` — 获取已解析文件内容

### Agent 注册接口

- `POST /api/agent/registry` — 注册新 Agent
  - 请求：`{agent_url: str}`
- `GET /api/agent/registry` — 列出已注册 Agent
- `DELETE /api/agent/registry/{agent_name}` — 删除 Agent（系统内置 Agent 不可删除）

---

## 项目结构

```
copilot/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py
│   │   ├── database.py               # PostgreSQL 异步连接
│   │   ├── models/                   # SQLAlchemy ORM
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── resume.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   ├── session.py            # 会话模型
│   │   │   ├── chat_message.py       # 聊天消息模型
│   │   │   └── story.py
│   │   ├── api/                      # REST 路由
│   │   │   ├── auth.py               # JWT 认证
│   │   │   ├── profile.py
│   │   │   ├── resumes.py
│   │   │   ├── jobs.py
│   │   │   ├── applications.py
│   │   │   ├── interviews.py
│   │   │   ├── session.py            # 会话 CRUD
│   │   │   └── agent.py              # /api/agent/chat SSE + parse-file + registry
│   │   ├── agents/                   # Agent 定义
│   │   │   ├── supervisor/
│   │   │   │   ├── state.py          # SupervisorState 类型定义
│   │   │   │   ├── graph.py          # StateGraph 构建+编译
│   │   │   │   ├── planner.py        # LLM 生成 Plan
│   │   │   │   ├── executor.py       # 并行 A2A + interrupt
│   │   │   │   ├── replanner.py      # LLM 决策 done/rewrite
│   │   │   │   └── synthesizer.py    # LLM stream 汇总
│   │   │   ├── profile/
│   │   │   │   ├── agent.py          # create_agent() ReAct
│   │   │   │   └── server.py         # A2A 服务端点 + Agent Card
│   │   │   ├── matching/
│   │   │   │   ├── agent.py
│   │   │   │   └── server.py
│   │   │   ├── interview/
│   │   │   │   ├── agent.py
│   │   │   │   └── server.py
│   │   │   └── support/
│   │   │       ├── agent.py
│   │   │       └── server.py
│   │   ├── a2a/                      # A2A 协议层
│   │   │   ├── client.py             # A2A HTTP 客户端
│   │   │   ├── server.py             # A2A 服务端 + mount_agent_card
│   │   │   ├── agent_card.py         # AgentCard 模型 + create_agent_card()
│   │   │   ├── registry.py           # Agent 注册表（discover/register/list）
│   │   │   └── types.py              # JSON-RPC 2.0 类型定义
│   │   ├── skills/                   # SKILL .md 文件（按目录，每个含 SKILL.md）
│   │   │   ├── build-profile/
│   │   │   ├── match-jobs/
│   │   │   ├── score-match/
│   │   │   ├── optimize-resume/
│   │   │   ├── generate-interview-qs/
│   │   │   ├── evaluate-answer/
│   │   │   ├── comfort-user/
│   │   │   └── daily-checkin/
│   │   ├── tools/                    # TOOL 原子操作
│   │   │   ├── agent_tools.py        # react / load_skill / read_qa_queue
│   │   │   ├── database.py           # db_read / db_write / read_profile / save_resume / confirm_overwrite
│   │   │   ├── chroma.py             # chroma_query / chroma_insert
│   │   │   ├── llm.py                # llm 实例 + call_llm tool
│   │   │   ├── parser.py             # parse_document（LLM 结构化解析）
│   │   │   ├── search.py             # web_search（初期返回空列表）
│   │   │   └── call_support.py       # call_support_agent (A2A 封装)
│   │   └── middleware/
│   │       └── sliding_window.py     # SlidingWindowMiddleware
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── router/
│       ├── stores/
│       │   └── session.js            # Pinia store（会话/消息/画像/简历状态）
│       ├── views/
│       │   ├── Chat.vue              # 智能对话（会话+聊天+文件上传+HITL 系统气泡）
│       │   ├── Profile.vue           # 求职画像
│       │   ├── Resumes.vue           # 简历管理（查看原文+打开附件+删除）
│       │   └── ...
│       ├── components/
│       ├── api/
│       │   └── index.js              # API 封装
│       └── utils/
│           └── clientId.js           # 客户端 ID 生成
└── data/
    └── seed_stories.json
```

---

## 开发阶段

### Phase 1：核心骨架 ✅ 已完成
- [x] 项目脚手架（FastAPI + Vue + Docker Compose）
- [x] 用户认证（JWT）
- [x] 数据库模型 + Alembic 迁移（User, UserProfile, Resume, Job, Application, Interview, Session, ChatMessage）
- [x] Chroma 初始化（pgvector + chromadb 容器）
- [x] Docker Compose 一键启动 8 个服务

### Phase 2：A2A 基础 + TOOL 层 ✅ 已完成
- [x] A2A 协议框架（JSON-RPC 2.0 client/server、Agent Card、Registry）
- [x] TOOL 实现（db_read/write, chroma_query/insert, parse_document, web_search, call_support_agent, react, load_skill, read_qa_queue）
- [x] `SlidingWindowMiddleware` 实现（消息数量控制+摘要）
- [x] Agent Card 端点可访问，A2A JSON-RPC 通信正常

### Phase 3：Sub-Agent 冒烟 + 核心 SKILL ✅ 已完成
- [x] Profile Agent（`create_agent()` ReAct + build-profile + HumanInTheLoopMiddleware）
- [x] Support Agent（`create_agent()` ReAct + comfort-user + daily-checkin）
- [x] Matching Agent（`create_agent()` ReAct + match-jobs + score-match + optimize-resume）
- [x] 简历通过前端 MinerU 解析，Agent 通过 `parse_document()` tool 结构化

### Phase 4：Supervisor + 多 Agent 编排 ✅ 已完成
- [x] Supervisor Plan-and-Execute StateGraph（Planner → Executor → Replanner → Synthesizer）
- [x] `/api/agent/chat` SSE 接口 + `/api/agent/chat/resume` 中断恢复
- [x] A2A `input-required` + LangGraph `interrupt()` 中断机制
- [x] Interview Agent（`create_agent()` ReAct + generate-interview-qs + evaluate-answer）
- [x] Session 会话管理（多会话隔离，消息持久化）

### Phase 5：全流程覆盖 🚧 进行中
- [x] 投递 CRUD + REST API
- [x] Session + ChatMessage 持久化
- [x] daily-checkin SKILL（每日播报）
- [x] 经历故事数据库模型 + Chroma 索引
- [ ] 状态看板（Vue 前端）
- [ ] 状态变更自动触发 Supervisor
- [ ] 4 个场景全流程端到端测试

### Phase 6：打磨
- [ ] UI/UX 优化 + SSE 渲染体验
- [ ] 安全加固 + 错误处理
- [ ] 生产环境部署配置
