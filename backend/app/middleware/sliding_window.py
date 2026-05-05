from langchain.agents.middleware import AgentMiddleware


class SlidingWindowMiddleware(AgentMiddleware):
    """按消息数量控制上下文窗口，窗口外自动压缩为摘要"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages

    def _process_window(self, messages: list[dict]) -> list[dict]:
        if len(messages) <= self.max_messages:
            return messages

        split_point = len(messages) - self.max_messages
        outside = messages[:split_point]
        inside = messages[split_point:]

        summary_parts = []
        for msg in outside:
            role = msg.get("role", "unknown")
            content_preview = str(msg.get("content", ""))[:50]
            summary_parts.append(f"[{role}]: {content_preview}...")

        summary = f"**历史摘要**: {'; '.join(summary_parts)}"
        inside.insert(0, {"role": "system", "content": summary, "_summary": True})

        for m in inside:
            if not m.get("_summary"):
                m["_in_window"] = True
        return inside
