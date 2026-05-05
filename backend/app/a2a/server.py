from fastapi import APIRouter, FastAPI
from typing import Callable, Awaitable
from app.a2a.types import JsonRpcRequest, JsonRpcResponse


async def default_handler(request: JsonRpcRequest) -> JsonRpcResponse:
    return JsonRpcResponse(id=request.id, error={"code": -32601, "message": "Method not found"})


def create_a2a_router(handler: Callable[[JsonRpcRequest], Awaitable[JsonRpcResponse]] = None) -> APIRouter:
    router = APIRouter()
    h = handler or default_handler

    @router.post("/")
    async def handle_jsonrpc(request: JsonRpcRequest):
        if request.method == "tasks/sendMessage":
            return await h(request)
        return JsonRpcResponse(id=request.id, error={"code": -32601, "message": f"Unknown method: {request.method}"})

    return router


def mount_agent_card(app: FastAPI, card: dict, path: str = "/.well-known/agent-card.json"):
    @app.get(path)
    def get_agent_card():
        return card
