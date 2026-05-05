import pytest
from app.main import app


def test_agent_chat_endpoint_exists():
    """验证 /api/agent/chat POST 路由已注册"""
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/api/agent/chat" in routes


def test_agent_chat_resume_exists():
    """验证 /api/agent/chat/resume POST 路由已注册"""
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/api/agent/chat/resume" in routes
