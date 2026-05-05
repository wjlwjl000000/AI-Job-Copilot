from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read
from app.tools.chroma import chroma_query
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

SUPPORT_SYSTEM_PROMPT = """你是求职情感支持专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 你的结果总是嵌入调用者的返回值，不作为独立消息推送
- 永远不返回 input-required，只返回 state: "completed"
- 语气温和真诚，像朋友一样鼓励"""

_tools = [chroma_query, db_read, call_llm]

support_agent = create_agent(
    model=llm,
    system_prompt=SUPPORT_SYSTEM_PROMPT,
    tools=_tools,
    middleware=[
        SkillLoadingMiddleware(skills_base_dir="app/skills", skill_names=["comfort-user", "daily-checkin"]),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)

support_agent.tools = _tools
