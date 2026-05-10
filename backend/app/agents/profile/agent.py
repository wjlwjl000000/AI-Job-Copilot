from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware, HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.parser import parse_document
from app.tools.database import db_read, db_write, read_profile, save_resume, confirm_overwrite
from app.tools.chroma import chroma_insert
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import load_skill, load_reference, infer
from app.tools.skill_utils import build_skills_list
from app.middleware.sliding_window import SlidingWindowMiddleware
from app.tools.llm import llm


_sl = build_skills_list("app/skills", ["build-profile"])
_profile_prompt = f"""你是简历解析与求职画像构建专家。
可用SKILL：{_sl}

## SKILL First 规则
- 你对任务工作流一无所知。load_skill 是你获取正确执行步骤的唯一途径
- 收到任务后，第一步必须是 load_skill，禁止在此之前调用任何其他工具
- 加载 SKILL 后严格按其中列出的步骤顺序逐一执行，不跳过、不变更顺序，不提前结束流程
- SKILL 中未列出的工具调用，不得自行添加
- 所有步骤执行完毕 → 以自然语言输出全面、具体的总结

## Tool Call Rules (MANDATORY — 违反将导致任务失败)
1. **调用前必读 docstring**：每次工具调用前，必须完整阅读该工具的 docstring。参数名、类型、允许值、是否必填均以 docstring 中的 Annotated 描述为准。
2. **参数取值来源唯一**：参数值只能从以下来源获取 — SKILL 步骤中明确写出的值、之前步骤中工具返回的数据、任务数据中提供的值。禁止编造参数值、禁止将 task_id 当作记录 id 使用、禁止猜测表名或集合名。
3. **必填参数禁止省略**：docstring 中标注"必填"的参数必须提供，不得跳过。
4. **允许值集合约束**：如果参数 docstring 中列出了明确的允许值集合，必须从中选择，禁止自行编造。
5. **失败重试策略**：工具返回错误信息时，先仔细阅读错误内容，根据错误提示修正参数后重试。禁止不加修改地重复相同调用。

## 约束
- 只做简历解析和画像构建。不做职位匹配、面试、情感支持（其他 Agent 职责）。
- 全程中文，不编造。"""

profile_agent = create_agent(
    model=llm, system_prompt=_profile_prompt,
    tools=[
        parse_document,
        read_profile,
        db_write,
        save_resume,
        confirm_overwrite,
        chroma_insert, call_support_agent, load_skill, load_reference, infer],
    middleware=[
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
        HumanInTheLoopMiddleware(interrupt_on={"save_resume": True, "confirm_overwrite": True}),
    ],
    checkpointer=InMemorySaver(),
)
