from pydantic import BaseModel
from typing import Any, Literal


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class JsonPart(BaseModel):
    type: Literal["application/json"] = "application/json"
    content: dict[str, Any]


class A2AMessage(BaseModel):
    role: Literal["user", "agent"]
    parts: list[TextPart | JsonPart]


class TaskStatus(BaseModel):
    state: Literal["submitted", "working", "input-required", "completed", "failed", "canceled"]
    message: str | None = None


class TaskArtifact(BaseModel):
    type: str = "application/json"
    content: dict[str, Any]


class TaskResult(BaseModel):
    id: str
    status: TaskStatus
    artifacts: list[TaskArtifact] = []


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str
    params: dict[str, Any]


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    result: TaskResult | dict[str, Any] | None = None
    error: dict[str, Any] | None = None
