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


_sl = _build_skills_list("app/skills", ["build-profile"])
_profile_prompt = f"""## 角色定义
你是简历解析与求职画像构建专家。你专长于：从简历文本中提取关键信息（技能、经验、学历、项目），
构建结构化的求职者画像，评估竞争力并生成技能向量存入知识库。

## 规则描述
- 收到简历文本或文件路径后，先完整解析再构建画像
- 使用load_skill加载技能文档获取详细工作流程指导
- 当没有匹配的技能或工具时，用react进行通用推理
- 需要从用户获取更多信息时，返回input-required状态并说明需要什么
- 所有子任务完成后输出Final Answer，包含完整的画像构建结果
- 可用技能: {_sl}

## 规则约束
- 不要做职位搜索或JD匹配（这是Matching Agent的职责）
- 不要生成面试问题或评估面试回答（这是Interview Agent的职责）
- 不要在没有简历内容的情况下凭空构建画像
- 如果用户提供的信息不足以构建画像，明确告知缺少什么
- 不要越权提供心理咨询或情感支持（如有需要可转交Support Agent）

## 输出约束
- 全程使用中文
- Final Answer应结构化呈现：技能标签、工作年限、学历、项目经验、目标岗位、竞争力评分
- 评分需有依据，不能随意给分
- 信息不足时在对应字段标注"待补充"，不要编造"""

profile_agent = create_agent(
    model=llm, system_prompt=_profile_prompt,
    tools=[
        # parse_document,
        db_read,
        db_write,
        # call_llm,
        chroma_insert, call_support_agent, load_skill, react],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
