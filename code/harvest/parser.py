"""文件解析：PDF/PPTX/DOCX/TXT/MD"""
from pathlib import Path

def parse_file(uploaded_file):
    name = uploaded_file.name.lower()
    ext = Path(name).suffix
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(uploaded_file).pages)
    if ext in (".ppt", ".pptx"):
        from pptx import Presentation
        return "\n".join(s.text_frame.text for s in Presentation(uploaded_file).slides
                         for shape in s.shapes if shape.has_text_frame)
    if ext in (".doc", ".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(uploaded_file).paragraphs)
    if ext in (".txt", ".md", ".markdown"):
        try:
            return uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return uploaded_file.read().decode("gbk")
    if ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
        return "[IMAGE:" + uploaded_file.name + "]"
    return ""
