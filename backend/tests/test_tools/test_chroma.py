from app.tools.chroma import chroma_query, chroma_insert


def test_chroma_tools_are_langchain_tools():
    assert hasattr(chroma_query, 'name')
    assert hasattr(chroma_insert, 'name')
