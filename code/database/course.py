"""课程 CRUD"""
from database.connection import db_query

def course_create(name, description=""):
    db_query("INSERT INTO course(name,description) VALUES(?,?)", (name, description))
    return db_query("SELECT last_insert_rowid()", fetch=True)[0][0]

def course_list():
    return db_query("SELECT * FROM course ORDER BY created_at DESC", fetch=True)

def course_delete(course_id):
    db_query("DELETE FROM course WHERE id=?", (course_id,))

def course_update(course_id, exam_date=None, daily_minutes=None):
    if exam_date:
        db_query("UPDATE course SET exam_date=? WHERE id=?", (str(exam_date), course_id))
    if daily_minutes:
        db_query("UPDATE course SET daily_study_minutes=? WHERE id=?", (daily_minutes, course_id))

def course_get(course_id):
    rows = db_query("SELECT * FROM course WHERE id=?", (course_id,), fetch=True)
    return rows[0] if rows else None
