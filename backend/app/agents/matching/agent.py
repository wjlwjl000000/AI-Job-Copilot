from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from app.tools.llm import llm
from app.tools.database import db_read, db_write, read_profile
from app.tools.chroma import chroma_query
from app.tools.search import web_search
from app.tools.call_support import call_support_agent
from app.tools.agent_tools import load_skill
from app.tools.skill_utils import build_skills_list
from app.middleware.sliding_window import SlidingWindowMiddleware


_sl = build_skills_list("app/skills", ["match-jobs", "score-match", "optimize-resume"])
_prompt = f"""你是职位匹配与简历优化专家。
你的职责是：帮助求职用户发现合适的职位机会、评估与目标岗位的匹配程度、以及针对特定JD优化简历。

可用技能：{_sl}

## SKILL First 规则
- 你对任务工作流一无所知。load_skill 是你获取正确执行步骤的唯一途径
- 收到任务后，第一步必须是 load_skill，禁止在此之前调用任何其他工具
- 加载 SKILL 后严格按其中列出的步骤顺序逐一执行，不跳过、不变更顺序，不提前结束流程
- SKILL 中未列出的工具调用，不得自行添加
- 所有步骤执行完毕 → 以自然语言输出全面、具体的总结

## 约束
- 只做职位匹配、匹配度评估和简历优化。不做首次画像构建（Profile Agent 职责）、面试准备（Interview Agent 职责）、情感支持
- 匹配度低于 0.6 时，主动调用 call_support_agent 获取鼓励内容，但不做心理咨询
- 优化简历时必须保留用户的真实经历，不得虚构或夸大

## 输出规则
- 全程中文，不编造
- 匹配结果：按评分排序，每题包含公司、岗位、薪资、城市、综合匹配分、匹配理由
- 评分结果：逐维度说明（技能、经验、学历、薪资），输出加权总分和差距分析
- 优化结果：标注每处改动（原文 → 优化后 → 改动理由），版本标题明确目标岗位
- 所有任务完成后以自然语言总结"""

matching_agent = create_agent(
    model=llm, system_prompt=_prompt,
    tools=[read_profile, db_read, db_write, chroma_query, web_search, call_support_agent, load_skill],
    middleware=[SlidingWindowMiddleware(max_messages=20), ToolRetryMiddleware(max_retries=2)],
)
