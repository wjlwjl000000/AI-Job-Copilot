from app.tools.database import db_read, db_write


def test_db_tools_are_langchain_tools():
    assert hasattr(db_read, 'name')
    assert hasattr(db_write, 'name')
