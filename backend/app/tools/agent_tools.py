"""ReAct cycle helper tools and SKILL loader. TOOL 绑定在 Agent 上，由 Agent 在 ReAct 循环中自主调用。"""
import os
from langchain_core.tools import tool


@tool
def react() -> str:
    """Agent 仍处于思考阶段，暂无合适工具可调用时使用。返回提示让 Agent 继续 Think 阶段。"""
    return "任务未完成，仍需思考。请继续分析下一步应该调用哪个工具。"


@tool
def load_skill(skill_name: str) -> str:
    """加载指定 SKILL 的完整工作流和指令。skill_name 是 SKILL 文件名（不含 .md），如 build-profile, parse-resume, score-match, match-jobs, optimize-resume, generate-interview-qs, evaluate-answer, comfort-user, daily-checkin"""
    path = os.path.join("app/skills", skill_name, "SKILL.md")
    if not os.path.isfile(path):
        return f"SKILL '{skill_name}' 不存在。可用的 SKILL 请参考技能列表。"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---")
    body = parts[2].strip() if len(parts) >= 3 else content
    return f"=== {skill_name} 工作流 ===\n{body}"
