import json
import uuid
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

_current_session_id: str = ""


def set_session_id(sid: str):
    global _current_session_id
    _current_session_id = sid


# 用户自行填写简历解析的 system prompt
PARSE_SYSTEM_PROMPT = """你是一名简历解析助手，负责将简历原始内容解析成固定的JSON格式。
    ## 规则(严格遵守)
    - 不能盲目猜测，无依据时字段必须留空
    - 必填的字段必须解析，严禁遗漏

    ## 输出格式(严格遵守):
    {
  "name": "string",                     // 用户姓名，**必填**
  "contact": {                         // 联系方式
    "phone": "string",                 // 手机号码
    "email": "string"                  // 电子邮箱
  },
  "basic": {                           // 基本信息
    "age": "integer",                  // 年龄
    "gender": "string",                // 性别
    "ethnicity": "string",             // 民族
    "hometown": "string",              // 籍贯/家乡
    "political": "string"              // 政治面貌
  },
  "education": [                       // 教育经历（数组），**必填**
    {
      "degree": "string",              // 学位（本科/硕士等）
      "school": "string",              // 学校名称
      "major": "string",               // 专业
      "period": "string"               // 就读时间段
    }
  ],
  "skills": [                          // 技能列表（数组），**必填**
    {
      "name": "string",                // 技能名称
      "level": "string",               // 熟练度（初级/中级/高级）
      "evidence": "string"             // 技能证明或相关项目描述
    }
  ],
  "projects": [                        // 项目经历（数组）
    {
      "name": "string",                // 项目名称
      "role": "string",                // 担任角色
      "description": "string",         // 项目简介（简短概述）
      "content": "string",             // 具体项目内容（详细描述工作重点、技术难点等）
      "tech_stack": ["string"],        // 技术栈（字符串数组）
      "achievements": "string"         // 成果指标（例如：准确率提升15%、系统响应时间缩短30%、发表论文1篇等）
    }
  ],
  "organization": [                    // 组织/社团经历（数组）
    {
      "name": "string",                // 组织名称（如"院研究生会主席团"）
      "duties": "string",              // 具体工作内容（职责描述）
      "achievements": "string"         // 工作成果指标（例如：组织活动参与人数200+、获得优秀社团称号等）
    }
  ],
  "work_years": "integer",             // 工作年限（年），**必填**
  "target": {                          // 求职目标
    "cities": ["string"],              // 意向城市（数组）
    "salary_range": "string",          // 期望薪资范围
    "industry": "string",              // 意向行业
    "roles": ["string"]                // 意向岗位（数组）
  },
  "scores": {                          // 评估分数
    "competitiveness": "float",        // 综合竞争力得分（0-1）
    "market_match": "float",           // 市场匹配度得分（0-1）
    "completeness": "float"            // 画像完整度得分（0-1）
  },
  "summary": "string",                 // 个人简介/自述
  "id": "string"                       // 唯一标识符（UUID）
}
"""


def _validate_profile(data: dict) -> list[str]:
    """校验解析结果，返回缺失/错误字段列表"""
    errors = []
    if not data.get("name"):
        errors.append("缺失: name")
    if not isinstance(data.get("skills"), list) or len(data["skills"]) == 0:
        errors.append("缺失: skills")
    if not isinstance(data.get("education"), list) or len(data["education"]) == 0:
        errors.append("缺失: education")
    if not isinstance(data.get("work_years"), int) and not isinstance(data.get("work_years"), float):
        errors.append("缺失: work_years")
    return errors


def _extract_json(text: str) -> dict | None:
    """从 LLM 输出中提取 JSON，自动去除 markdown 代码块"""
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[-1].strip() == "```":
            raw = "\n".join(lines[1:-1])
        else:
            raw = "\n".join(lines[1:])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


@tool
async def parse_document() -> dict:
    """解析当前会话第一个已上传的简历文件，返回 {table, data, errors}。data 为 null 表示无法解析，errors 非空时 data 仍可能有效（校验警告不阻断）。无需参数"""
    from app.api.agent import _parsed_files

    session_id = _current_session_id
    files = _parsed_files.get(session_id, {})
    if not files:
        return {"table": "user_profiles", "data": None, "errors": ["当前会话无已上传文件，请先上传简历"]}

    from app.tools.llm import zhipu_llm as llm

    first_file = next(iter(files.values()))
    filename = first_file["filename"]
    messages = [
        SystemMessage(content=PARSE_SYSTEM_PROMPT),
        HumanMessage(content=f"[文件: {filename}]\n\n{first_file['text']}"),
    ]
    result = await llm.ainvoke(messages)
    raw = result.content
    parsed = _extract_json(raw)
    if parsed is None:
        return {"table": "user_profiles", "data": None, "errors": [f"JSON解析失败，原始输出:\n{raw}"]}
    errors = _validate_profile(parsed)
    parsed["id"] = str(uuid.uuid4())
    return {
        "table": "user_profiles",
        "data": parsed,
        "errors": errors,
    }
