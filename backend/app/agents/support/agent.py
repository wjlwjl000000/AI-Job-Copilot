from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read
from app.tools.chroma import chroma_query
from app.tools.agent_tools import react, load_skill
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, base_url=settings.openai_base_url, streaming=True)

SUPPORT_SYSTEM_PROMPT = "你是求职情感支持专家。Think→Act→Observe循环。技能: {skills_list}。加载技能用load_skill,无工具用react, 永远返回completed不返回input-required, 语气温和, 完成输出Final Answer。"

support_agent = create_agent(
    model=llm, system_prompt=SUPPORT_SYSTEM_PROMPT,
    tools=[chroma_query, db_read, call_llm, load_skill, react],
    middleware=[
        SkillLoadingMiddleware(skills_base_dir="app/skills", skill_names=["comfort-user", "daily-checkin"]),
        SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2),
    ],
)
