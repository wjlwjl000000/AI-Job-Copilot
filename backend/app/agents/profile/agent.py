from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.parser import parse_document
from app.tools.database import db_read, db_write
from app.tools.llm import call_llm
from app.tools.chroma import chroma_insert
from app.tools.call_support import call_support_agent
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

PROFILE_SYSTEM_PROMPT = """你是简历与画像专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 遇到关键信息缺失（学历、联系方式等）→ Task state 返回 input-required
- Support Agent 永远不返回 input-required，只返回 completed"""

_tools = [parse_document, db_read, db_write, call_llm, chroma_insert, call_support_agent]

profile_agent = create_agent(
    model=llm,
    system_prompt=PROFILE_SYSTEM_PROMPT,
    tools=_tools,
    middleware=[
        SkillLoadingMiddleware(skills_base_dir="app/skills", skill_names=["parse-resume", "build-profile"]),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)

profile_agent.tools = _tools
