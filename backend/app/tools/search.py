from typing import Annotated
from langchain_core.tools import tool

_VALID_SOURCES = {"boss", "lagou"}


@tool
async def web_search(
    query: Annotated[str, "搜索关键词，必填。使用岗位名+技能+城市拼接，如 'AI工程师 Python FastAPI 北京'"],
    source: Annotated[str, "招聘平台，必填。可选值：boss | lagou"] = "boss",
) -> list[dict]:
    """搜索外部招聘平台的开放职位。初期返回空列表。"""
    if source not in _VALID_SOURCES:
        return [{"error": f"无效数据源 '{source}'，可选: {', '.join(sorted(_VALID_SOURCES))}"}]
    return []
