import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

_client = None


async def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


async def init_collections():
    client = await get_chroma_client()
    for name in ["jobs", "stories", "profiles"]:
        try:
            client.get_collection(name)
        except Exception:
            client.create_collection(name)
