from langchain_core.tools import tool


@tool
async def web_search(query: str, source: str = "boss") -> list[dict]:
    """搜索外部招聘信息。source: boss|lagou。初期返回空列表"""
    return []
