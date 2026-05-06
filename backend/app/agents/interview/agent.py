from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import react, load_skill
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, base_url=settings.openai_base_url, streaming=True)

INTERVIEW_SYSTEM_PROMPT = "你是面试备战专家。Think→Act→Observe循环。技能: {skills_list}。加载技能用load_skill,无工具用react, 缺信息返回input-required, 完成输出Final Answer。"

interview_agent = create_agent(
    model=llm, system_prompt=INTERVIEW_SYSTEM_PROMPT,
    tools=[db_read, db_write, call_llm, call_support_agent, load_skill, react],
    middleware=[
        SkillLoadingMiddleware(skills_base_dir="app/skills", skill_names=["generate-interview-qs", "evaluate-answer"]),
        SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2),
    ],
)
