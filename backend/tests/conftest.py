import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """使用 session 级别事件循环，避免 SQLAlchemy async greenlet 与 strict 模式冲突"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
