"""Agent tools. TOOL 绑定在 Agent 上，由 Agent 自主调用。"""
import os
from typing import Annotated
from langchain_core.tools import tool

_VALID_SKILLS = {
    "build-profile", "match-jobs", "score-match", "optimize-resume",
    "generate-interview-qs", "evaluate-answer", "comfort-user", "daily-checkin",
}


@tool
def infer(
    content: Annotated[str, "推理内容，必填。记录当前的分析思路、判断依据、中间结论等"],
) -> str:
    """记录推理过程。在 SKILL 的推理步骤（如评分分析、多维度对比）中调用，用于留存推理结果到对话历史。传入什么就返回什么。"""
    return content


@tool
def load_reference(
    skill_name: Annotated[str, "SKILL 名称，必填。如 score-match, match-jobs 等"],
    ref_path: Annotated[str, "reference 文件路径（相对于 references/ 目录），必填。如 scoring-formula.md, field-mapping.md"],
) -> str:
    """加载指定 SKILL 的 reference 文件内容。读取 app/skills/<skill_name>/references/<ref_path>。用于在 SKILL 步骤中按需获取详细规则。"""
    import os
    path = os.path.join("app/skills", skill_name, "references", ref_path)
    if not os.path.isfile(path):
        return f"Reference 文件不存在: skills/{skill_name}/references/{ref_path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@tool
def load_skill(
    skill_name: Annotated[str, "SKILL 文件名（不含 .md），必填。可选值：build-profile | match-jobs | score-match | optimize-resume | generate-interview-qs | evaluate-answer | comfort-user | daily-checkin"],
) -> str:
    """加载指定 SKILL 的完整工作流和指令。收到任务后必须第一步调用此工具。"""
    if not skill_name:
        return "错误：skill_name 是必填参数。示例: load_skill(skill_name='build-profile')"
    if skill_name not in _VALID_SKILLS:
        return f"错误：未知 SKILL '{skill_name}'。可用: {', '.join(sorted(_VALID_SKILLS))}"
    path = os.path.join("app/skills", skill_name, "SKILL.md")
    if not os.path.isfile(path):
        return f"SKILL '{skill_name}' 文件不存在。"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---")
    body = parts[2].strip() if len(parts) >= 3 else content
    return f"=== {skill_name} 工作流 ===\n{body}"


@tool
async def read_qa_queue(
    interview_id: Annotated[str, "面试记录 ID，必填。格式如 'iv-xxx'"],
) -> str:
    """读取指定面试记录的完整 Q&A 内容。返回格式化的问题和回答列表。"""
    if not interview_id:
        return "错误：interview_id 是必填参数。示例: read_qa_queue(interview_id='iv-xxx')"
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
