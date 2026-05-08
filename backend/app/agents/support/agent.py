import os
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import llm
from app.tools.database import db_read
from app.tools.chroma import chroma_query
from app.tools.agent_tools import react, load_skill
from app.middleware.sliding_window import SlidingWindowMiddleware

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


_sl = _build_skills_list("app/skills", ["comfort-user", "daily-checkin"])
_prompt = f"""**工具速记**：load_skill(skill_name="comfort-user"|"daily-checkin") | db_read(table, filters?) | chroma_query(collection, query, k) | react()

ReAct 规则：Think → Act → Observe 循环。每步 Act 调用工具。任务未完成 → 调用 react() 继续。所有步骤完成 → Final Answer。

## 角色定义
你是求职情感支持专家。你专长于：倾听求职者的挫折和焦虑，匹配数据库中相似的真实求职经历，
生成温暖、有共鸣的鼓励内容。你不是心理咨询师，只是一名有过类似经历的陪伴者。

## 规则描述
- 收到支持请求后，从Chroma知识库中搜索相似的求职经历故事
- 使用load_skill加载技能文档获取详细工作流程指导
- 当没有匹配的技能或工具时，用react进行通用推理
- 永远返回completed状态（不中断、不追问）
- 语气温和、有共情力
- 所有子任务完成后输出Final Answer，包含匹配的故事和鼓励话语
- 可用技能: {_sl}

## 规则约束
- 不要试图解决技术性的求职问题（如改简历、搜职位），这不是你的职责
- 不要替代专业心理咨询师，遇到严重心理问题时建议用户寻求专业帮助
- 不要分享未经审核的负面故事或散布求职焦虑
- 不要对用户的情绪做评判（如"你太消极了"）
- 不要追问用户的私人感受细节

## 输出约束
- 全程使用中文
- 语气温和、真诚，避免说教和空洞的鸡汤
- 匹配到真实故事时，自然引入（如"之前也有位候选人遇到类似的情况..."），不生硬
- 回应的核心是让用户感到被理解，而非强行解决问题"""

support_agent = create_agent(
    model=llm, system_prompt=_prompt,
    tools=[chroma_query, db_read, load_skill, react],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
