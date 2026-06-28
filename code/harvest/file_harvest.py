"""文件收割主流程"""
import re
from datetime import datetime
from config.settings import RAW, get_subjects
from harvest.parser import parse_file
from harvest.slicer import slice_text
from harvest.classifier import classify_subject
from harvest.knowledge_extractor import extract_knowledge_points
from database.course import course_list, course_create

def save_raw(subject, title, content, src_type="文件上传", src_name=""):
    folder = RAW / subject
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[\\/:*?\"<>|]", "_", title)[:50]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = folder / f"{ts}_{safe}.md"
    fm = f"---\ntype: {src_type}\nsubject: {subject}\nsource: {src_name or title}\ncreated: {datetime.now().strftime('%Y-%m-%d')}\n---\n"
    fp.write_text(fm + "\n" + content, encoding="utf-8")
    return fp

def list_raw(subject=None):
    dirs = [RAW / subject] if subject else [RAW / s for s in get_subjects()]
    files = []
    for d in dirs:
        if d.exists():
            files.extend(d.glob("*.md"))
    return files

def harvest_file(uploaded_file, course_id=None):
    text = parse_file(uploaded_file)
    if not text:
        return f"❌ 无法解析文件：{uploaded_file.name}"
    if text.startswith("[IMAGE:"):
        return f"⚠️ 检测到图片文件（{text[7:-1]}）。当前版本仅支持电子文档（PDF/PPTX/DOCX/TXT/MD）。图片识别功能计划在后续版本支持。"
    subject = classify_subject(text)
    existing_courses = {c[1] for c in course_list()}
    if subject not in existing_courses and course_id:
        course_create(subject, f"自动创建：{subject}课程")
    sections = slice_text(text)
    saved = []
    for title, content in sections:
        if len(content.strip()) < 30:
            continue
        fp = save_raw(subject, title, content, src_type="文件上传", src_name=uploaded_file.name)
        saved.append(str(fp))
    kp_count = 0
    if course_id:
        kp_count = extract_knowledge_points(course_id, text)
    kp_msg = f"，提取了 {kp_count} 个知识点" if kp_count else ""
    return f"✅ 已收割《{uploaded_file.name}》→【{subject}】{len(saved)}个片段{kp_msg}（刷题可直接使用）", saved, subject
