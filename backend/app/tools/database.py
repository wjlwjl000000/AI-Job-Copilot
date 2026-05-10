import json
import uuid
from typing import Annotated

from langchain_core.tools import tool
from sqlalchemy import text, True_
from app.database import async_session


def _encode_json_fields(data: dict) -> dict:
    """将 dict 中的 list/dict 值序列化为 JSON 字符串，确保 asyncpg 能正确编码到 JSON/JSONB 列"""
    encoded = {}
    for k, v in data.items():
        if isinstance(v, (list, dict)):
            encoded[k] = json.dumps(v, ensure_ascii=False)
        else:
            encoded[k] = v
    return encoded


_VALID_TABLES = {"users", "user_profiles", "resumes", "jobs", "applications", "experience_stories", "interviews"}

# 每个表的合法列名（白名单），用于校验 filters key 和 fields
_TABLE_COLUMNS: dict[str, set[str]] = {
    "users": {"id", "email", "password_hash", "created_at"},
    "user_profiles": {"id", "name", "contact", "basic", "education", "skills",
                      "projects", "organization", "work_years", "target", "scores", "summary"},
    "resumes": {"id", "user_id", "title", "base_version", "target_role",
                "content", "file_path", "match_scores"},
    "jobs": {"id", "source", "source_id", "jd_content", "requirements",
             "company", "salary_range", "city", "status"},
    "applications": {"id", "user_id", "resume_id", "job_id", "status", "timeline", "notes"},
    "experience_stories": {"id", "tags", "content", "source", "source_url",
                           "is_anonymous", "approved"},
    "interviews": {"id", "application_id", "questions", "overall_feedback",
                   "weaknesses", "status"},
}


@tool
async def db_read(
    table: Annotated[str, "目标表名，必填。可选值：users | user_profiles | resumes | jobs | applications | experience_stories | interviews"],
    filters: Annotated[dict, "等值过滤条件，key 必须是上表中列出的真实列名。例: {'id': 'xxx'}。禁止使用 user_profile_id、task_id 等不存在的列名"] = None,
    fields: Annotated[list[str], "指定返回列名列表，不传返回全部列。可选值见上表各表列名"] = None,
) -> list[dict]:
    """读数据库查询。返回匹配记录的字典列表，空数组表示无结果。"""
    if table not in _VALID_TABLES:
        return [{"error": f"无效表名 '{table}'，可选: {', '.join(sorted(_VALID_TABLES))}"}]
    valid_cols = _TABLE_COLUMNS.get(table, set())
    if filters:
        for k in filters:
            if k not in valid_cols:
                return [{"error": f"无效列名 '{k}'（表 {table}），合法列名: {', '.join(sorted(valid_cols))}"}]
    if fields:
        for f in fields:
            if f not in valid_cols:
                return [{"error": f"无效列名 '{f}'（表 {table}），合法列名: {', '.join(sorted(valid_cols))}"}]
        cols = ", ".join(fields)
    else:
        cols = "*"
    async with async_session() as session:
        if filters:
            conditions = " AND ".join([f"{k} = :{k}" for k in filters])
            query = text(f"SELECT {cols} FROM {table} WHERE {conditions}")
        else:
            query = text(f"SELECT {cols} FROM {table}")
        result = await session.execute(query, filters or {})
        return [dict(row._mapping) for row in result.fetchall()]


_WRITABLE_TABLES = {"user_profiles", "resumes", "jobs", "applications", "experience_stories", "interviews"}


@tool
async def db_write(
    table: Annotated[str, "目标表名，必填。可选值：user_profiles | resumes | jobs | applications | experience_stories | interviews"],
    data: Annotated[dict, "要写入的字段数据，dict 格式。必须包含目标表的所有必填列"],
    record_id: Annotated[str, "记录的唯一标识符。若提供则 UPDATE 现有记录；若为 None 则 INSERT 新记录。"] = None,
) -> str:
    """向指定数据库表写入数据，返回 'ok' 或错误信息。"""
    if table not in _WRITABLE_TABLES:
        return f"错误：无效表名 '{table}'，可选: {', '.join(sorted(_WRITABLE_TABLES))}"
    data = _encode_json_fields(data)
    async with async_session() as session:
        if record_id:
            data["id"] = record_id
            set_clause = ", ".join([f"{k}=:{k}" for k in data])
            query = text(f"UPDATE {table} SET {set_clause} WHERE id=:id")
        else:
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            cols = ", ".join(data.keys())
            vals = ", ".join([f":{k}" for k in data])
            query = text(f"INSERT INTO {table} ({cols}) VALUES ({vals})")
        await session.execute(query, data)
        await session.commit()
    return "ok"


@tool
async def read_profile() -> list[dict]:
    """查询 user_profiles 表，返回画像列表。空数组表示无已有画像"""
    return await db_read.ainvoke({"table": "user_profiles"})


@tool
async def confirm_overwrite(
    messages: Annotated[str, "中断提示信息，格式：'检测到已有画像（姓名：XX），是否覆盖？'"],
) -> str:
    """确认是否覆盖已有画像。messages 仅用于向 supervisor 传递中断提示，不参与工具逻辑。"""
    return "confirmed"


@tool
async def save_resume(
    messages: Annotated[str, "纯信息传递，不参与工具逻辑。格式：'提示语-file_id'"],
) -> str:
    """保存原始简历文本到 resumes 表。messages 仅用于向 supervisor 传递中断提示信息。"""
    from app.api.agent import _parsed_files
    from app.tools.parser import _current_session_id
    files = _parsed_files.get(_current_session_id, {})
    if not files:
        return "error: 无已上传文件"
    first = next(iter(files.values()))
    return await db_write.ainvoke({
        "table": "resumes", "data": {
            "user_id": "u-default", "title": first["filename"],
            "base_version": True,
            "content": {"raw_text": first["text"]},
            "file_path": first.get("file_path", ""),
        }
    })
