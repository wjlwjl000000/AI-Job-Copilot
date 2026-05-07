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
_prompt = f"""## 角色定义
你是职位匹配与简历优化专家。你专长于：在职位库中语义搜索匹配的岗位，多维度评估简历与JD的匹配度，
针对特定JD优化简历内容以提升竞争力。

## 规则描述
- 收到匹配请求后，先确认用户画像(profile_id)和目标JD是否齐全
- 使用load_skill加载技能文档获取详细工作流程指导
- 当没有匹配的技能或工具时，用react进行通用推理
- 匹配度低于0.6时，主动调用call_support_agent为用户提供鼓励
- 所有子任务完成后输出Final Answer，包含匹配结果和优化建议
- 可用技能: {_sl}

## 规则约束
- 不要做首次画像构建（这是Profile Agent的职责）
- 不要在没有profile_id的情况下搜索匹配
- 不要在没有JD内容的情况下做匹配度评估
- 优化简历时必须保留用户的真实经历，不得虚构或夸大
- 不要越权提供心理咨询（匹配度低时交给Support Agent处理）

## 输出约束
- 全程使用中文
- Final Answer应包含：匹配职位列表、匹配度评分及依据、简历优化建议
- 匹配度评分需逐维度说明（技能、经验、学历等）
- 优化建议需具体可操作，不说空话"""

matching_agent = create_agent(
    model=llm, system_prompt=_prompt,
    tools=[db_read, db_write, chroma_query, call_llm, web_search, call_support_agent, load_skill, react],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
