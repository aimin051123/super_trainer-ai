"""薄弱点判定 + 掌握度更新"""
from datetime import datetime
from database.connection import db_query

def judge_weak(kp_id, accuracy, total, last_correct):
    if total < 3 and not last_correct:
        return False, "待观察"
    recent = db_query("""SELECT user_answer,correct_answer FROM quiz_question
        WHERE knowledge_point_id=? ORDER BY created_at DESC LIMIT 5""", (kp_id,), fetch=True)
    if len(recent) >= 2:
        cons_err = 0
        for ua, ca in recent:
            if ua and ua[0] == ca[0]:
                break
            cons_err += 1
        if cons_err >= 2:
            return True, f"连续错误{cons_err}次"
    if total >= 3 and accuracy < 0.6:
        return True, f"答题{total}次正确率{accuracy:.0%}<60%"
    if total >= 5 and accuracy >= 0.6 and len(recent) >= 3:
        last3 = sum(1 for ua, ca in recent[:3] if ua and ua[0] == ca[0]) / 3
        if last3 < 0.4:
            return True, f"总正确率{accuracy:.0%}但近3次降至{last3:.0%}"
    return False, ""

def kp_update_mastery(kp_id, is_correct):
    row = db_query("SELECT mastery,total_count,correct_count FROM knowledge_point WHERE id=?",
                   (kp_id,), fetch=True)
    if not row:
        return
    mastery, total, correct = row[0]
    total += 1
    correct += int(is_correct)
    new_mastery = correct / total if total > 0 else 0
    is_weak, reason = judge_weak(kp_id, new_mastery, total, is_correct)
    db_query("""UPDATE knowledge_point
        SET mastery=?, total_count=?, correct_count=?, is_weak=?, weak_reason=?, last_reviewed=?
        WHERE id=?""",
        (new_mastery, total, correct, int(is_weak), reason, datetime.now().isoformat(), kp_id))

def detect_weak_points(course_id):
    from database.knowledge_point import kp_get_weak, kp_get_observing
    weak = [{"page": r[2], "subject": r[1], "accuracy": r[5], "total": r[6], "reason": r[9]}
            for r in kp_get_weak(course_id)]
    obs = [{"page": r[2], "subject": r[1], "accuracy": r[5], "total": r[6], "reason": r[9]}
           for r in kp_get_observing(course_id)]
    return weak, obs
