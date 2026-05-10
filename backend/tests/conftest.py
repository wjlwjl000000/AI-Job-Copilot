import os
import uuid
import pytest
import asyncio
import httpx
from sqlalchemy import text
from app.database import async_session

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as c:
        yield c


@pytest.fixture(scope="module")
async def seed_user():
    """直接写入 DB 创建测试用户（绕过 passlib bcrypt Docker bug）"""
    uid = str(uuid.uuid4())
    async with async_session() as db:
        await db.execute(text(
            "INSERT INTO users (id, email, password_hash, created_at) "
            "VALUES (:id, :email, :pw, :ca) "
            "ON CONFLICT (id) DO NOTHING"
        ), {"id": uid, "email": f"e2e-{uid[:8]}@test.com", "pw": "test-hash",
            "ca": "2026-01-01T00:00:00"})
        await db.commit()
    return uid
