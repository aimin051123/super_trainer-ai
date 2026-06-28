"""错题管理"""
from datetime import datetime
from database.connection import db_query

def wrong_record(course_id, kp_id, qq_id, q_type, content, options, correct_ans, user_ans, explanation):
    db_query("""INSERT INTO wrong_answer(course_id,knowledge_point_id,quiz_question_id,
        question_type,content,options,correct_answer,user_answer,explanation)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (course_id, kp_id, qq_id, q_type, content, options, correct_ans, user_ans, explanation))

def wrong_list_unmastered(course_id):
    return db_query("""SELECT * FROM wrong_answer WHERE course_id=? AND mastered=0
        ORDER BY created_at DESC""", (course_id,), fetch=True)

def wrong_list_by_kp(course_id, kp_id):
    return db_query("""SELECT * FROM wrong_answer WHERE course_id=? AND knowledge_point_id=? AND mastered=0
        ORDER BY review_count DESC""", (course_id, kp_id), fetch=True)

def wrong_review(wrong_id, user_answer, is_correct):
    row = db_query("SELECT review_count FROM wrong_answer WHERE id=?", (wrong_id,), fetch=True)
    if row:
        new_count = row[0][0] + 1
        mastered = 1 if is_correct else 0
        db_query("""UPDATE wrong_answer SET review_count=?, last_reviewed=?, mastered=?
            WHERE id=?""", (new_count, datetime.now().isoformat(), mastered, wrong_id))
        return mastered
    return 0
