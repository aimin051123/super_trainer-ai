"""碎片知识收割"""
from harvest.classifier import classify_subject, classify_entity
from harvest.file_harvest import save_raw
from harvest.knowledge_extractor import extract_knowledge_points

def harvest_fragment(text, course_id=None):
    etype, title = classify_entity(text)
    subject = classify_subject(text)
    fp = save_raw(subject, title, text, src_type=etype, src_name="碎片输入")
    kp_count = 0
    if course_id:
        kp_count = extract_knowledge_points(course_id, text)
    kp_msg = f"，提取了 {kp_count} 个知识点" if kp_count else ""
    return f"✅ 碎片已收割：{title} →【{subject}】→【{etype}】{kp_msg}（刷题可直接使用）"
