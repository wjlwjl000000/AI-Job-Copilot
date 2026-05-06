from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.parser import parse_document
from app.tools.database import db_read, db_write
from app.tools.llm import call_llm
from app.tools.chroma import chroma_insert
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import react, load_skill
from app.middleware.skill_loading import SkillLoadingMiddleware
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    streaming=True,
)

PROFILE_SYSTEM_PROMPT = """你是简历与画像专家。严格 Think→Act→Observe 循环。

技能概览: {skills_list}
加载技能用 load_skill(skill_name),无工具可用时调 react()

规则: 按技能流程每步调用工具, db_write和chroma_insert不可跳过, 缺信息返回input-required, 全部完成输出Final Answer"""

profile_agent = create_agent(
    model=llm,
    system_prompt=PROFILE_SYSTEM_PROMPT,
    tools=[parse_document, db_read, db_write, call_llm, chroma_insert, call_support_agent, load_skill, react],
    middleware=[
        SkillLoadingMiddleware(skills_base_dir="app/skills", skill_names=["parse-resume", "build-profile"]),
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
    ],
)
