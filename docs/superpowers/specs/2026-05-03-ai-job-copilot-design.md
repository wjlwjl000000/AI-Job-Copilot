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
| AI 模型 | `ChatOpenAI(model="gpt-5-mini")` | 可切换 provider |
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
│  SKILL: onboard-user                                         │
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
│ parse-     │             │ generate-        │
│  resume    │             │  interview-qs    │
│ build-     │             │ evaluate-        │
│  profile   │             │  answer          │
│            │             │                  │
│ TOOL:      │             │ TOOL:            │
│ parse_     │             │ db_read/write    │
│  document  │             │ call_llm         │
│ db_read/   │             │                  │
│  write     │             │                  │
│ call_llm   │             │                  │
│ chroma_    │             │                  │
│  insert    │             │                  │
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
│ call_llm   │  │                 │           │
│ call_      │  │                 │           │
│  support  ─┼──┘                 │           │
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
       │       db_read, call_llm    │
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
- `input-required` → 需要用户补充信息（等同于旧的 priority=true）
- Support Agent 永远返回 `completed`，不会返回 `input-required`

**SSE 流式事件：**
- `messageDelta` — 增量文本块（Synthesizer 逐字输出）
- `taskStatusUpdate` — Task 状态变更
- `taskArtifactUpdate` — 产出物增量

### 中断处理（A2A `input-required` → LangGraph `interrupt()`）

```
Sub-Agent 返回 state: "completed":
  → Executor 正常收集 artifact → 继续 asyncio.as_completed() 循环

Sub-Agent 返回 state: "input-required":
  → Executor 调用 interrupt() 立即挂起（不等待其他任务完成）
  → SSE 推送问题给用户
  → 用户回复 → graph.astream(Command(resume={...}), config) 恢复
  → Executor 把回复发给原 Agent 继续 → 得到最终结果
  → 继续收集其他任务结果
```

**关键：** `interrupt()` 是 LangGraph 原生机制，其返回值就是用户回复。不需要额外 state 字段或 TurnQueue 类。

---

## Supervisor Agent：Plan-and-Execute

Supervisor 内部使用 LangGraph StateGraph 实现 Plan-and-Execute 模式。Supervisor 不直接调用 TOOL，而是通过 A2A 客户端分发任务。

### 状态定义

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class SupervisorState(TypedDict):
    user_id: str
    messages: Annotated[list, add_messages]
    goal: str                           # 用户原始目标
    plan: list[dict]                    # [{agent, action, data}]
    pending_tasks: list[str]            # 未完成的 A2A task_id
    all_results: dict                   # 所有轮次的 {agent: result}
    synthesized_response: str
    loop_count: int                     # 当前循环次数
    max_loops: int                      # 最大循环次数 (默认3)
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
│   .as_completed│ ● priority=true → interrupt() 立即挂起
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


# ---- Executor (内部 interrupt，Command(resume=...) 恢复) ----
async def executor_node(state: SupervisorState):
    """
    并行 A2A 执行 Plan，asyncio.as_completed() 逐个收结果。
    发现 state: "input-required" → 立即 interrupt()。
    """
    pending = [t for t in state["plan"] 
               if t.get("task_id") not in state["all_results"]]
    
    a2a_tasks = {
        asyncio.create_task(
            a2a_client.send_message(agent_name=t["agent"], message=...)
        ): t for t in pending
    }
    
    for coro in asyncio.as_completed(a2a_tasks):
        result = await coro
        task = a2a_tasks[coro]
        
        if result["status"]["state"] == "input-required":
            # interrupt() 返回值就是用户回复，不需要额外 state 字段
            user_answer = interrupt({
                "type": "user_question",
                "question": result["status"]["message"],
                "task_id": result["id"],
            })
            # 恢复后，user_answer = 用户回复内容
            # 发给原 Agent 继续执行
            continued = await a2a_client.send_message(
                agent_name=task["agent"],
                message={
                    "role": "user",
                    "parts": [
                        {"type": "text", "text": user_answer["answer"]}
                    ]
                },
                task_id=result["id"],  # 同一个 task，继续
            )
            state["all_results"][task["agent"]] = continued["result"]["artifacts"]
        else:
            state["all_results"][task["agent"]] = result["result"]["artifacts"]
    
    return {"all_results": state["all_results"]}


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
  │   Profile 返回 state: "input-required" (2s)
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
  │   Matching 返回 state: "completed" (30s) → 直接写入 results
  │
  └─ 全部完成 → return results
```

**为什么不会阻塞：**
- `asyncio.as_completed()` 顺序是"谁先完成谁先处理"
- Profile 2秒返回 `input-required` → `interrupt()` 立即触发
- 未完成的 asyncio 协程不丢失
- `interrupt()` 的返回值就是用户回复，无需额外 state 字段

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
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            if event.get("__interrupt__"):
                # 中断事件 → 推给前端
                yield f"data: {json.dumps(event['__interrupt__'])}\n\n"
            elif event.get("synthesizer"):
                content = event["synthesizer"]["synthesized_response"]
                # 逐 chunk 推送（Synthesizer 内 LLM astream 产生）
                yield f"data: {json.dumps({'type': 'response', 'content': content})}\n\n"
        
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
    
    return {"turn_queue": queue.to_dict()}
```

---

## Sub-Agent：ReAct 模式

每个 Sub-Agent 用 `create_agent()` 创建，自带 ReAct 模式。TOOL 通过 `tools=[...]` 绑定在 Agent 上。

**LLM 配置（所有 Agent 共享）：**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-5-mini",
    api_key="sk-AfFjOyI0IT8ZELF7mXMQ3voviAIwDYaGvoJnxfpGOcJpXWAj",
    base_url="https://api.chatanywhere.tech",
    streaming=True,
)
```

### Profile Agent

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware

# system_prompt 使用占位符，SkillLoadingMiddleware 动态填充
PROFILE_SYSTEM_PROMPT = """你是简历与画像专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 遇到关键信息缺失（学历、联系方式等）→ Task state 返回 input-required
- Support Agent 永远不返回 input-required，只返回 completed"""

profile_agent = create_agent(
    llm=llm,
    system_prompt=PROFILE_SYSTEM_PROMPT,
    tools=[parse_document, db_read, db_write, call_llm, chroma_insert],
    middleware=[
        SkillLoadingMiddleware(skills_dir="skills/profile/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

### Matching Agent

```python
MATCHING_SYSTEM_PROMPT = """你是职位匹配与简历优化专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 匹配度 < 0.6 → 主动调 call_support_agent 获取经历分享
- 需要用户选择 → Task state 返回 input-required"""

matching_agent = create_agent(
    llm=llm,
    system_prompt=MATCHING_SYSTEM_PROMPT,
    tools=[db_read, db_write, chroma_query, call_llm, call_support_agent],
    middleware=[
        SkillLoadingMiddleware(skills_dir="skills/matching/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

### Interview Agent / Support Agent

同模式，`create_agent()` + 各自的 `tools` + 占位符 system_prompt。

**Support Agent 特别注意：** `call_llm` 中 prompt 不生成 `input-required`。

### 关键说明

- **TOOL 绑定于 Agent**：`tools=[...]` 传给 `create_agent()`
- **ReAct 是内置的**：`create_agent()` 默认 ReAct，不手动写循环
- **占位符动态填充**：`{skills_list}` 在 middleware 初始化时填充 name+description 列表，`{skill_content}` 在每次加载 SKILL 时填充
- **`SlidingWindowMiddleware`**：自定义，按消息数量控制窗口。窗口内保留原文，窗口外自动生成摘要
- **`ToolRetryMiddleware`**：LangChain 内置
- **`call_support_agent`**：A2A 封装 Tool，Sub-Agent 间唯一通信例外

---

## SKILL 与 TOOL

### TOOL（原子操作层，绑定于 Agent）

| Tool | 功能 | 绑定于 |
|------|------|--------|
| `parse_document` | 解析 PDF/Word/文本文件 | Profile |
| `call_llm` | 调用大模型（统一封装，可切换 provider） | 全部 Agent |
| `db_read` | 读数据库 | Profile, Matching, Interview, Support |
| `db_write` | 写数据库（创建/更新） | Profile, Matching, Interview |
| `chroma_query` | 向量相似度检索 | Matching, Support |
| `chroma_insert` | 写入向量到 Chroma | Profile |
| `web_search` | 搜索外部信息（职位/公司） | Matching |
| `call_support_agent` | A2A 调用 Support Agent | Profile, Matching, Interview |
| `read_qa_queue` | 读面试问答队列 | Interview |
| `react` | ReAct 思考循环占位 | 全部 Agent |
| `load_skill` | 按需加载 SKILL 完整内容 | 全部 Agent |

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
| `onboard-user.md` | Supervisor | 当新用户首次使用系统、或需要识别用户意图并分派任务时 |
| `parse-resume.md` | Profile | 当用户上传或更新简历文件，需要解析并提取结构化信息时 |
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
  → SkillLoadingMiddleware 只加载本 Agent 的 SKILL
    name + description 列表（每个几十 token）

Supervisor 发来任务
  → Agent 的 ReAct 循环中，LLM 根据 description 判断需要哪个 SKILL
  → SkillLoadingMiddleware 加载该 SKILL 完整 body → 注入上下文
  → Agent 按 SKILL 工作流程执行，调用 TOOL
  → 任务完成后卸载 SKILL body，释放 token

  → 执行中 LLM 判定需要新 SKILL → 加载 → 继续 → 卸载
```

---

## 关键场景实现逻辑

### 场景一：新用户上传简历

```
1. 前端 POST /api/agent/chat (SSE)
   {message: "我上传了简历 resume.pdf"}

2. Supervisor Planner:
   加载 onboard-user SKILL
   基于 Agent Card Registry 生成 Plan（不含 Support）:
     [
       {agent: "profile", action: "parse", data: {file_path: "resume.pdf"}},
       {agent: "profile", action: "build_profile", data: {}},
       {agent: "matching", action: "match", data: {}}
     ]

3. Supervisor Executor 并行 A2A:
   发出 Profile:parse + Profile:build_profile + Matching:match
   （build_profile 等 parse 完成 → 在 Executor 内顺序编排，或 Planner 拆分）

4. Profile Agent (ReAct) 完成 parse + build_profile:
   Thought: "需要构建画像" → 加载 build-profile.md
   Act: call_llm → db_write(profile) → chroma_insert(profile_summary)
   → {priority: false, result: {profile_id, skill_tags, ...}}

5. Matching Agent (ReAct):
   Thought: "搜索匹配职位" → 加载 match-jobs.md
   Act: chroma_query(profile_embedding, "jobs") → call_llm → 排序
   → {priority: false, result: {matches: [...]}}

   Matching 内部发现是首次使用:
   Act: call_support_agent(trigger="onboarding")
   # Support Agent (ReAct): comfort-user → chroma_query → call_llm
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
   Plan: [{agent: "matching", action: "score", data: {job_id: "xxx"}}]

3. Executor → Matching Agent (ReAct):
   Thought: "评估匹配度" → 加载 score-match.md
   Act: db_read("profile") + db_read("job", "xxx")
   Act: call_llm(profile + jd, 四维度对比)
   Observe: "overall=0.45，偏低"
   
   Thought: "应生成优化版并获取鼓励"
   Act: call_llm(optimize) → db_write(optimized_resume)
   Act: call_support_agent(trigger="low_match")
   → {priority: false, result: {overall: 0.45, gaps: [...], 
        optimized_resume_id: "...", support_content: {...}}}

4. Executor → Replanner:
   Replanner 分析: 初始 Plan 只有 score，但 Matching 返回了优化版简历。
   匹配度低(0.45)，优化版已生成，已有鼓励内容。目标达成 → done。

5. Synthesizer:
   "匹配度 45%，主要差距在 LangChain 经验...
    已生成优化版简历。这里有一个相似经历：3个月前..."
   → SSE 推送

# 注：如果 Replanner 发现需要追加任务（如匹配度低但未生成优化版），
#   会 rewite Plan [{agent: "matching", action: "optimize", ...}]
#   路由回 Executor 继续执行
```

### 场景三：优先级中断（Sub-Agent 需要用户输入）

```
时间线:
  0s: Executor 并行发出 Profile:parse / Matching:match
  2s: Profile 返回 priority=true
  
1. Executor asyncio.as_completed() 收到 Profile 返回:
   Thought: "缺少学历信息"
   → {priority: true, user_question: "请补充您的学历信息（学校、专业）"}

2. Executor 调用 interrupt():
   → LangGraph 图挂起（Matching 的 asyncio 协程仍在执行）
   → MemorySaver 保存状态
   → SSE yield interrupt 事件: {type: "user_question", question: "请补充学历信息",
                                task_id: "t_001_profile"}
   → 图暂停，等待...

3. 用户回复: "北京大学 计算机科学 本科"

4. 前端 POST /api/agent/chat {message: "北京大学 计算机科学 本科",
                                turn_id: "turn_abc123"}

5. graph.astream(None, config) → 图从 interrupt() 处恢复执行

6. Executor 恢复后:
   → A2A Profile: {action: "continue", data: {answer: "北京大学..."}}
   → Profile 继续 ReAct: db_write(profile, education)
   → {priority: false, result: {profile_id, ...}}

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
     [{agent: "matching", action: "match", data: {}}]

3. Matching Agent (ReAct):
   Thought: "投递被拒，搜索新职位"
   Act: chroma_query(profile_embedding, "jobs") → 5个匹配
   
   Thought: "用户可能需要鼓励"
   Act: call_support_agent(trigger="rejected", job_id)
   # Support Agent (ReAct): comfort-user → chroma_query("被拒 同行业") → call_llm
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
  user_id → User
  skill_tags: jsonb      # [{name, level}, ...]
  work_years: int
  education: jsonb       # {degree, school, major}
  projects: jsonb        # [{name, description, tech_stack}, ...]
  target: jsonb          # {cities, salary_range, industry, roles}
  preference: jsonb      # {notice_frequency, ...}
  scores: jsonb          # {competitiveness, market_match, completeness}

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
  source_id: str         # 平台原始ID
  jd_content: text       # 职位描述原文
  requirements: jsonb    # [{skill, level, required}, ...]
  company: str
  salary_range: str
  city: str
  status: str            # open/closed

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
- `POST /api/resumes/upload` — 上传基础简历
- `GET /api/resumes` — 简历版本列表
- `DELETE /api/resumes/{id}` — 删除版本

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
  - 请求：`{message: str, turn_id?: str}`
  - SSE 事件：
    - `{"type": "user_question", ...}` — interrupt 中断
    - `{"type": "response", "content": "..."}` — Synthesizer 流式文本
    - `{"type": "done"}` — 完成
- `POST /api/agent/chat/resume` — 回复中断问题
  - 请求：`{message: str, turn_id: str}`

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
│   │   ├── database.py               # PostgreSQL 连接
│   │   ├── models/                   # SQLAlchemy ORM
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── resume.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   └── story.py
│   │   ├── api/                      # REST 路由
│   │   │   ├── profile.py
│   │   │   ├── resumes.py
│   │   │   ├── jobs.py
│   │   │   ├── applications.py
│   │   │   ├── interviews.py
│   │   │   └── agent.py              # /api/agent/chat SSE
│   │   ├── agents/                   # Agent 定义
│   │   │   ├── supervisor/
│   │   │   │   ├── agent.py          # Plan-and-Execute StateGraph
│   │   │   │   ├── planner.py
│   │   │   │   ├── executor.py       # A2A 客户端调用
│   │   │   │   └── synthesizer.py
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
│   │   │   ├── client.py             # A2A 客户端
│   │   │   ├── server.py             # A2A 服务端框架
│   │   │   ├── agent_card.py         # Agent Card 生成
│   │   │   ├── registry.py           # Supervisor 注册表
│   │   │   └── turn_queue.py         # 消息队列
│   │   ├── skills/                   # SKILL .md 文件
│   │   │   ├── supervisor/
│   │   │   │   └── onboard-user.md
│   │   │   ├── profile/
│   │   │   │   ├── parse-resume.md
│   │   │   │   └── build-profile.md
│   │   │   ├── matching/
│   │   │   │   ├── match-jobs.md
│   │   │   │   ├── score-match.md
│   │   │   │   └── optimize-resume.md
│   │   │   ├── interview/
│   │   │   │   ├── generate-interview-qs.md
│   │   │   │   └── evaluate-answer.md
│   │   │   └── support/
│   │   │       ├── comfort-user.md
│   │   │       └── daily-checkin.md
│   │   ├── tools/                    # TOOL 原子操作
│   │   │   ├── database.py           # db_read / db_write
│   │   │   ├── chroma.py             # chroma_query / chroma_insert
│   │   │   ├── llm.py                # call_llm
│   │   │   ├── parser.py             # parse_document
│   │   │   ├── search.py             # web_search
│   │   │   └── call_support.py       # call_support_agent (A2A 封装)
│   │   ├── middleware/               # 仅自定义中间件
│   │   │   ├── skill_loading.py      # SkillLoadingMiddleware（占位符填充+SKILL加载）
│   │   │   └── sliding_window.py     # SlidingWindowMiddleware（消息数量控制+摘要）
│   │   ├── rag/
│   │   │   ├── vector_store.py
│   │   │   └── embeddings.py
│   │   └── tasks/                    # Celery（非 Agent 批量任务）
│   │       ├── worker.py
│   │       └── jobs.py
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
│       ├── views/
│       │   ├── Dashboard.vue
│       │   ├── Profile.vue
│       │   ├── Resumes.vue
│       │   ├── JobMatch.vue
│       │   ├── Applications.vue
│       │   ├── InterviewPrep.vue
│       │   ├── SupportFeed.vue
│       │   └── AgentRegistry.vue     # Agent Card 注册管理
│       ├── components/
│       │   ├── agent/                # Agent 对话 + priority 中断 UI
│       │   └── common/
│       └── api/
└── data/
    └── seed_stories.json
```

---

## 开发阶段

### Phase 1：核心骨架
- 项目脚手架（FastAPI + Vue + Docker Compose）
- 用户认证（JWT）
- 数据库模型 + Alembic 迁移
- Chroma 初始化
- **验证：** Docker Compose 一键启动，`/auth/login` 返回 JWT，数据库表创建成功

### Phase 2：A2A 基础 + TOOL 层
- A2A 协议框架（JSON-RPC 2.0 client/server、Agent Card、Registry）
- 8 个 TOOL 实现 + 单元测试
- `SkillLoadingMiddleware` + `SlidingWindowMiddleware` 实现
- **验证：** Agent Card 端点可访问，A2A JSON-RPC 通信正确

### Phase 3：Sub-Agent 冒烟 + 核心 SKILL
- Profile Agent（`create_agent()` ReAct + parse-resume + build-profile）
- Support Agent（`create_agent()` ReAct + comfort-user）
- Matching Agent（`create_agent()` ReAct + match-jobs + score-match + optimize-resume）
- **验证：** 上传简历 → Profile Agent 独立完成解析+画像构建

### Phase 4：Supervisor + 多 Agent 编排
- Supervisor Plan-and-Execute StateGraph
- `/api/agent/chat` SSE 接口
- TurnQueue + priority 中断
- Interview Agent（`create_agent()` ReAct + generate-interview-qs + evaluate-answer）
- **验证：** 用户一句话 → Planner 生成 Plan → 并行调 Profile + Support → 汇总响应

### Phase 5：全流程覆盖
- 投递 CRUD + 状态看板（Vue）
- 状态变更自动触发 Supervisor
- onboard-user + daily-checkin SKILL
- 经历故事入库 + Chroma 索引
- **验证：** 4 个场景流程全部通过，被拒自动触发鼓励 + 新推荐

### Phase 6：打磨
- UI/UX 优化 + SSE 渲染体验
- 安全加固 + 错误处理
