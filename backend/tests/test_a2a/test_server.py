import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.a2a.server import create_a2a_router
from app.a2a.types import JsonRpcRequest, JsonRpcResponse, TaskResult, TaskStatus

# 构建测试 FastAPI app
app = FastAPI()

async def a2a_handler(request: JsonRpcRequest) -> JsonRpcResponse:
    return JsonRpcResponse(
        id=request.id,
        result=TaskResult(
            id="task-test",
            status=TaskStatus(state="completed"),
            artifacts=[],
        ),
    )

a2a_router = create_a2a_router(handler=a2a_handler)
app.include_router(a2a_router)


@pytest.mark.asyncio
async def test_send_message_returns_jsonrpc_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/", json={
            "jsonrpc": "2.0", "id": 1,
            "method": "tasks/sendMessage",
            "params": {"message": {"role": "user", "parts": [{"type": "text", "text": "hello"}]}}
        })
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert data["result"]["status"]["state"] == "completed"


@pytest.mark.asyncio
async def test_unknown_method_returns_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/", json={
            "jsonrpc": "2.0", "id": 2, "method": "tasks/unknown", "params": {}
        })
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32601
