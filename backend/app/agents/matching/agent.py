import os
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.chroma import chroma_query
from app.tools.search import web_search
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import react, load_skill
from app.middleware.sliding_window import SlidingWindowMiddleware

llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, base_url=settings.openai_base_url, streaming=True)


def _build_skills_list(base_dir: str, names: list[str]) -> str:
    lines = []
    for name in names:
        path = os.path.join(base_dir, name, "SKILL.md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                parts = f.read().split("---")
            for line in parts[1].strip().split("\n") if len(parts) >= 3 else []:
                if line.startswith("description:"):
                    lines.append(f"- **{name}**: {line.split(':',1)[1].strip()}")
                    break
    return "\n".join(lines)


_sl = _build_skills_list("app/skills", ["match-jobs", "score-match", "optimize-resume"])
_prompt = f"你是职位匹配与简历优化专家。Think→Act→Observe。技能: {_sl}。加载技能用load_skill,无工具用react,匹配度<0.6调call_support_agent,完成输出Final Answer。"

matching_agent = create_agent(
    model=llm, system_prompt=_prompt,
    tools=[db_read, db_write, chroma_query, call_llm, web_search, call_support_agent, load_skill, react],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
