from langchain_core.tools import tool
from app.a2a.client import A2AClient

_client = A2AClient()


@tool
async def call_support_agent(trigger: str, profile_id: str, context: dict = None) -> dict:
    """调用Support Agent获取经历分享和鼓励。trigger: low_match|rejected|interview_fail|offer|onboarding|daily"""
    support_url = "http://localhost:8004"
    response = await _client.send_message(support_url, message={
        "role": "user",
        "parts": [
            {"type": "text", "text": f"触发事件: {trigger}"},
            {"type": "application/json", "content": {"profile_id": profile_id, "trigger": trigger, **(context or {})}}
        ]
    })
    if response.result and response.result.artifacts:
        return response.result.artifacts[0].content
    return {"story": "", "encouragement": ""}
