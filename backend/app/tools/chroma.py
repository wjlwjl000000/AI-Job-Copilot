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


@tool
async def chroma_query(collection: str, query: str, k: int = 5) -> list[dict]:
    """向量相似度检索。collection: jobs|stories|profiles。返回匹配文档及相似度分数"""
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
    collection: Annotated[str, "集合名，可选值：jobs|stories|profiles"],
    documents: Annotated[list[str], "要写入的文档内容列表"],
    metadatas: Annotated[list[dict], "每个文档对应的元数据列表"] = None,
) -> str:
    """写入向量到Chroma，使用add_documents一行写入"""
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
