"""
TDD RED: parse_document with real files.
Design doc requires parsing PDF, Word, and TXT files.
Current test only checks the tool is registered — never verifies actual parsing.
"""
import os
import tempfile
import pytest
from app.tools.parser import parse_document


@pytest.mark.asyncio
async def test_parse_txt_file():
    """RED: Write test first. parse_document on .txt file should return text."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("张三\nPython工程师\n3年经验\n技能：FastAPI, PostgreSQL")
        tmp_path = f.name

    try:
        result = await parse_document.ainvoke({"file_path": tmp_path})
        assert "张三" in result["text"]
        assert "Python" in result["text"]
        assert result["metadata"]["type"] == "text"
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_unsupported_format_returns_error():
    """RED: Unknown file extension should return error dict."""
    result = await parse_document.ainvoke({"file_path": "/fake/file.xyz"})
    assert "error" in result
    assert "xyz" in result["error"].lower()
