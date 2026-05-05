from langchain_core.tools import tool
from sqlalchemy import text
from app.database import async_session


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
async def db_write(table: str, data: dict, record_id: str = None) -> str:
    """写数据库。table: user_profiles|resumes|jobs|applications|experience_stories。record_id为空则创建新记录"""
    async with async_session() as session:
        if record_id:
            set_clause = ", ".join([f"{k}=:{k}" for k in data])
            query = text(f"UPDATE {table} SET {set_clause} WHERE id=:id")
            data["id"] = record_id
        else:
            cols = ", ".join(data.keys())
            vals = ", ".join([f":{k}" for k in data])
            query = text(f"INSERT INTO {table} ({cols}) VALUES ({vals})")
        await session.execute(query, data)
        await session.commit()
    return "ok"
