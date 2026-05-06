import os
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


_sl = _build_skills_list("app/skills", ["parse-resume", "build-profile"])
_profile_prompt = f"你是简历与画像专家。Think→Act→Observe。技能: {_sl}。加载技能用load_skill,无工具用react,缺信息返回input-required,全部完成输出Final Answer。"

profile_agent = create_agent(
    model=llm, system_prompt=_profile_prompt,
    tools=[parse_document, db_read, db_write, call_llm, chroma_insert, call_support_agent, load_skill, react],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
