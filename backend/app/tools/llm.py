from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.config import settings

# llm = ChatOpenAI(
#     model=settings.openai_model,
#     api_key=settings.openai_api_key,
#     base_url=settings.openai_base_url,
#     streaming=True,
# )
llm = ChatOpenAI(
    model=settings.zhipuai_model,
    api_key=settings.zhipuai_api_key,
    base_url=settings.zhipuai_base_url,
    streaming=True,
)

zhipu_llm = ChatOpenAI(
    model=settings.zhipuai_model,
    api_key=settings.zhipuai_api_key,
    base_url=settings.zhipuai_base_url,
    streaming=True,
)


@tool
async def call_llm(prompt: str, temperature: float = 0.7) -> str:
    """调用大语言模型，传入 prompt 获取回复。用于文本生成、分析、总结等场景。"""
    response = await llm.ainvoke(prompt)
    return response.content
