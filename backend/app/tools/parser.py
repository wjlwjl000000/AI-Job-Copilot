from langchain_core.tools import tool
import os


@tool
async def parse_document(file_path: str) -> dict:
    """解析PDF/Word/文本文件，返回结构化内容。file_path: 绝对路径"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return {"text":f"以下是简历原始文本内容：\n{f.read()}", "metadata": {"type": "text"}}
    elif ext == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        return {"text":f"以下是简历原始文本内容：\n{text}", "metadata": {"type": "pdf"}}
    elif ext in (".docx", ".doc"):
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"text":f"以下是简历原始文本内容：\n{text}", "metadata": {"type": "docx"}}
    return {"error": f"Unsupported format: {ext}"}
