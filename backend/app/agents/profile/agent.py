import os
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware, HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.parser import parse_document
from app.tools.database import db_read, read_profile, save_profile, save_resume, confirm_overwrite
from app.tools.chroma import chroma_insert
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import react, load_skill
from app.middleware.sliding_window import SlidingWindowMiddleware
from app.tools.llm import llm


def _build_skills_list(base_dir: str, names: list[str]) -> str:
    lines = []
    for name in names:
        path = os.path.join(base_dir, name, "SKILL.md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                parts = f.read().split("---")
            for line in parts[1].strip().split("\n") if len(parts) >= 3 else []:
                if line.startswith("description:"):
                    lines.append(f"\n- skill_name: {name}\ndescription: {line.split(':',1)[1].strip()}\n" + "-"*10)
                    break
    return "\n".join(lines)


_sl = _build_skills_list("app/skills", ["build-profile"])
_profile_prompt = f"""你是简历解析与求职画像构建专家。可调用 load_skill(skill_name)来加载SKILL.md工作流，然后严格按加载的工作流逐步执行。
可用SKILL：{_sl}

ReAct 规则：
- Think → Act → Observe 循环。每步 Act 必须实际调用工具。
- Observe 后任务未完成 → 调用 react() 继续下一轮 Think。
- 工作流所有步骤执行完毕 → 输出必须以 "Final Answer:" 开头，之后严格按 SKILL.md 中 Output Format 的结构输出画像数据。

## 约束
- 只做简历解析和画像构建。不做职位匹配、面试、情感支持（其他 Agent 职责）。
- 全程中文，不编造。"""

profile_agent = create_agent(
    model=llm, system_prompt=_profile_prompt,
    tools=[
        parse_document,
        read_profile,
        save_profile,
        save_resume,
        confirm_overwrite,
        chroma_insert, call_support_agent, load_skill, react],
    middleware=[
        SlidingWindowMiddleware(max_messages=20),
        ToolRetryMiddleware(max_retries=2),
        HumanInTheLoopMiddleware(interrupt_on={"save_resume": True, "confirm_overwrite": True}),
    ],
    checkpointer=InMemorySaver(),
)
