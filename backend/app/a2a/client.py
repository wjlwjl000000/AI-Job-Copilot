import httpx
from app.a2a.types import JsonRpcRequest, JsonRpcResponse


class A2AClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=300.0)

    async def _post(self, url: str, payload: dict) -> JsonRpcResponse:
        resp = await self._client.post(url, json=payload)
        data = resp.json()
        return JsonRpcResponse(**data)

    async def _get(self, url: str) -> dict:
        resp = await self._client.get(url)
        return resp.json()

    async def send_message(self, agent_url: str, message: dict, task_id: str = None) -> JsonRpcResponse:
        params = {"message": message}
        if task_id:
            params["taskId"] = task_id
        return await self._post(agent_url, {
            "jsonrpc": "2.0", "id": 1,
            "method": "tasks/sendMessage",
            "params": params,
        })

    async def fetch_agent_card(self, agent_url: str) -> dict:
        return await self._get(f"{agent_url.rstrip('/')}/.well-known/agent-card.json")
