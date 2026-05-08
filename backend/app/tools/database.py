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


@tool
async def db_read(table: str, filters: dict = None) -> list[dict]:
    """读数据库查询。table: users|user_profiles|resumes|jobs|applications|experience_stories。filters: {column: value}"""
    async with async_session() as session:
        if filters:
            conditions = " AND ".join([f"{k} = :{k}" for k in filters])
            query = text(f"SELECT * FROM {table} WHERE {conditions}")
        else:
            query = text(f"SELECT * FROM {table}")
        result = await session.execute(query, filters or {})
        return [dict(row._mapping) for row in result.fetchall()]


@tool
async def db_write(table: Annotated[str,"目标表名，可选值：user_profiles|resumes|jobs|applications|experience_stories"],
                   data: Annotated[dict,"要写入的字段数据，dict格式"],
                   record_id: Annotated[str,"记录的唯一标识符。若提供则更新现有记录；若为 None 则创建新记录。"] = None
                   ) -> str:
    """向指定数据库表写入数据，返回ok字符串"""
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
async def save_profile(
    data: Annotated[dict, "要写入的画像数据"],
    record_id: Annotated[str, "已有画像ID，更新时传入"] = None,
) -> str:
    """保存画像到 user_profiles 表。data 直接从 parse_document 返回值复制。"""
    return await db_write.ainvoke({"table": "user_profiles", "data": data, "record_id": record_id})


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
            "base_version": True, "content": {"raw_text": first["text"]}
        }
    })
