"""
TDD RED: Chroma end-to-end — insert documents, then query them back.
Verifies design doc requirement: add_documents() write + similarity_search retrieval.
"""
import pytest
from app.rag.vector_store import get_chroma_client, init_collections


@pytest.mark.asyncio
async def test_insert_and_query_jobs_collection():
    """
    RED: Write test FIRST, then verify implementation makes it pass.
    Insert job-like documents into Chroma, query by skill keyword,
    verify semantically similar results return.
    """
    client = await get_chroma_client()
    await init_collections()

    jobs = client.get_collection("jobs")
    # Clean up any existing test data
    try:
        jobs.delete(where={"test": True})
    except Exception:
        pass  # Collection might be empty

    # Insert test documents using add() (low-level, mirrors add_documents)
    jobs.add(
        documents=[
            "Python后端工程师，负责Django和FastAPI微服务开发",
            "前端工程师，负责React和Vue.js页面开发",
            "AI算法工程师，负责大模型训练和LangChain应用开发",
        ],
        metadatas=[
            {"title": "Python Backend", "source": "boss", "test": True},
            {"title": "Frontend Engineer", "source": "lagou", "test": True},
            {"title": "AI Engineer", "source": "boss", "test": True},
        ],
        ids=["job-1", "job-2", "job-3"],
    )

    # Query for AI-related positions
    results = jobs.query(query_texts=["AI 大模型 LangChain"], n_results=3)

    # The AI Engineer document should be top result (highest semantic similarity)
    top_document = results["documents"][0][0]
    assert "AI" in top_document or "大模型" in top_document or "LangChain" in top_document, \
        f"Expected AI-related document first, got: {top_document}"

    # Cleanup
    jobs.delete(ids=["job-1", "job-2", "job-3"])


@pytest.mark.asyncio
async def test_profiles_and_stories_collections():
    """Verify all 3 design-specified collections exist and accept inserts."""
    client = await get_chroma_client()
    await init_collections()

    # Profiles collection
    profiles = client.get_collection("profiles")
    profiles.add(
        documents=["3年Python后端，熟悉FastAPI和PostgreSQL"],
        metadatas=[{"user_id": "u-test", "test": True}],
        ids=["prof-1"],
    )
    assert profiles.count() >= 1

    # Stories collection
    stories = client.get_collection("stories")
    stories.add(
        documents=["被拒20次后终于拿到AI公司Offer"],
        metadatas=[{"trigger": "rejected", "test": True}],
        ids=["story-1"],
    )
    assert stories.count() >= 1

    # Cleanup
    profiles.delete(ids=["prof-1"])
    stories.delete(ids=["story-1"])
