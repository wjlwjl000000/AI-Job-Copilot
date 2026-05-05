from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.call_support import call_support_agent
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

INTERVIEW_SYSTEM_PROMPT = """你是面试备战专家。

## 可用技能
{skills_list}

## 当前技能详情
{skill_content}

## 规则
- 使用 ReAct 模式完成任务
- 基于 JD + 用户弱项生成针对性问题
- 评估回答时给出评分和改进建议
- 需要用户补充信息时返回 state: input-required"""

interview_agent = create_agent(
    model=llm,
    system_prompt=INTERVIEW_SYSTEM_PROMPT,
    tools=[db_read, db_write, call_llm, call_support_agent],
    middleware=[
        SkillLoadingMiddleware(skills_base_dir="app/skills", skill_names=["generate-interview-qs", "evaluate-answer"]),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
