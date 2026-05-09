"""Agent tools. TOOL 绑定在 Agent 上，由 Agent 自主调用。"""
import os
from langchain_core.tools import tool


@tool
def load_skill(skill_name: str = "") -> str:
    """加载指定 SKILL 的完整工作流和指令。skill_name 是必填参数，值为 SKILL 文件名（不含 .md），如 build-profile, match-jobs, score-match, optimize-resume, generate-interview-qs, evaluate-answer, comfort-user, daily-checkin"""
    if not skill_name:
        return "错误：load_skill 必须传入 skill_name 参数。请重新调用，例如 load_skill(skill_name='build-profile')。"
    path = os.path.join("app/skills", skill_name, "SKILL.md")
    if not os.path.isfile(path):
        return f"SKILL '{skill_name}' 不存在。可用: build-profile, match-jobs, score-match, optimize-resume, generate-interview-qs, evaluate-answer, comfort-user, daily-checkin。"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---")
    body = parts[2].strip() if len(parts) >= 3 else content
    return f"=== {skill_name} 工作流 ===\n{body}"


@tool
async def read_qa_queue(interview_id: str = "") -> str:
    """读取指定面试记录 questions 字段中所有 Q&A 内容。interview_id 为必填参数。供 generate-interview-qs 和 evaluate-answer 使用。"""
    if not interview_id:
        return "错误：read_qa_queue 必须传入 interview_id 参数，例如 read_qa_queue(interview_id='iv-xxx')。"
    from app.tools.database import db_read
    rows = await db_read.ainvoke({"table": "interviews", "filters": {"id": interview_id}})
    if not rows:
        return f"Interview '{interview_id}' 不存在。"
    questions = rows[0].get("questions", [])
    if not questions:
        return "该面试记录暂无问题。"
    result = []
    for q in questions:
        qid = q.get("id", "?")
        question = q.get("question", "")
        answer = q.get("answer") or "(未回答)"
        result.append(f"[{qid}] Q: {question}\n    A: {answer}")
    return "\n\n".join(result)
