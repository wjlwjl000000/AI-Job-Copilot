from typing import Annotated
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.config import settings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

_VALID_COLLECTIONS = {"jobs", "stories", "profiles"}


@tool
async def chroma_query(
    collection: Annotated[str, "集合名，必填。可选值：jobs | stories | profiles"],
    query: Annotated[str, "搜索查询文本，必填。用自然语言描述要搜索的内容"],
    k: Annotated[int, "返回结果数量，默认 5"] = 5,
) -> list[dict]:
    """向量相似度检索。返回匹配文档列表及相似度分数。"""
    if collection not in _VALID_COLLECTIONS:
        return [{"error": f"无效集合名 '{collection}'，可选: {', '.join(sorted(_VALID_COLLECTIONS))}"}]
    store = Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory="./chroma_data",
    )
    docs = store.similarity_search_with_score(query, k=k)
    return [
        {"content": d.page_content, "metadata": d.metadata, "score": s}
        for d, s in docs
    ]


@tool
async def chroma_insert(
    collection: Annotated[str, "集合名，必填。可选值：jobs | stories | profiles"],
    documents: Annotated[list[str], "要写入的文档内容列表，必填。每个元素是一段文本"],
    metadatas: Annotated[list[dict], "每个文档对应的元数据列表，长度需与 documents 一致"] = None,
) -> str:
    """写入向量到 Chroma 集合。返回 'ok, inserted N docs' 或错误信息。"""
    if collection not in _VALID_COLLECTIONS:
        return f"错误：无效集合名 '{collection}'，可选: {', '.join(sorted(_VALID_COLLECTIONS))}"
    store = Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory="./chroma_data",
    )
    docs = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(documents, metadatas or [{}])
    ]
    store.add_documents(docs)
    return f"ok, inserted {len(docs)} docs"
