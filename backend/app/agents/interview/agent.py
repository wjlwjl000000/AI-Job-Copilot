import os
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_openai import ChatOpenAI
from app.config import settings
from app.tools.llm import call_llm
from app.tools.database import db_read, db_write
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import react, load_skill, read_qa_queue
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


_sl = _build_skills_list("app/skills", ["generate-interview-qs", "evaluate-answer"])
_prompt = f"""## 角色定义
你是面试备战专家。你专长于：基于JD和用户弱项生成针对性的面试问题，评估用户的模拟面试回答质量，
提供具体的改进建议。

## 规则描述
- 收到面试准备请求后，先确认JD内容和用户弱项领域是否齐全
- 使用load_skill加载技能文档获取详细工作流程指导
- 当没有匹配的技能或工具时，用react进行通用推理
- 需要从用户获取更多信息时，返回input-required状态并说明需要什么
- 使用read_qa_queue读取待评估的问答记录
- 所有子任务完成后输出Final Answer，包含面试题目或评估结果
- 可用技能: {_sl}

## 规则约束
- 不要做简历解析或画像构建（这是Profile Agent的职责）
- 不要做职位搜索（这是Matching Agent的职责）
- 生成面试题必须基于真实JD内容，不能凭空出题
- 评估回答时基于具体标准（相关性、深度、表达），不做人身评价
- 不要越权提供情感支持（如有需要可转交Support Agent）

## 输出约束
- 全程使用中文
- 生成的面试题应分类呈现（技术类、行为类、项目类等），每题标注考察意图
- 回答评估应包含：优点、不足、改进建议，逐条具体
- 避免使用"你不够好"等否定性评价，改为"可以加强"等建设性表达"""

interview_agent = create_agent(
    model=llm, system_prompt=_prompt,
    tools=[db_read, db_write, call_llm, call_support_agent, load_skill, react, read_qa_queue],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
