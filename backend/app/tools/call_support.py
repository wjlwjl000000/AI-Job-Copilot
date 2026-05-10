from typing import Annotated
from langchain_core.tools import tool
from app.a2a.client import A2AClient

_client = A2AClient()

_VALID_TRIGGERS = {"low_match", "rejected", "interview_fail", "offer", "onboarding", "daily"}


@tool
async def call_support_agent(
    trigger: Annotated[str, "触发事件类型，必填。可选值：low_match | rejected | interview_fail | offer | onboarding | daily"],
    profile_id: Annotated[str, "用户画像 ID，必填。用于匹配相似经历故事"],
    context: Annotated[dict, "额外上下文信息，如 {overall: 0.45, key_gaps: [...]}"] = None,
) -> dict:
    """调用 Support Agent 获取经历分享和鼓励内容。返回 {story, encouragement}。"""
    if trigger not in _VALID_TRIGGERS:
        return {"error": f"无效 trigger '{trigger}'，可选: {', '.join(sorted(_VALID_TRIGGERS))}"}
    support_url = "http://support-agent:8004"
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
