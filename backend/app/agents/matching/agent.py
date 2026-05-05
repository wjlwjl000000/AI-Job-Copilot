from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.chroma import chroma_query
from app.tools.search import web_search
from app.tools.call_support import call_support_agent
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

MATCHING_SYSTEM_PROMPT = """你是职位匹配与简历优化专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 匹配度 < 0.6 → 主动调 call_support_agent 获取经历分享
- 需要用户选择 → Task state 返回 input-required"""

_tools = [db_read, db_write, chroma_query, call_llm, web_search, call_support_agent]

matching_agent = create_agent(
    model=llm,
    system_prompt=MATCHING_SYSTEM_PROMPT,
    tools=_tools,
    middleware=[
        SkillLoadingMiddleware(skills_dir="app/skills/matching/"),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)

matching_agent.tools = _tools
