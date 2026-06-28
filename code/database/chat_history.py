"""对话历史"""
from database.connection import db_query

def chat_save(course_id, role, content):
    db_query("INSERT INTO chat_history(course_id,role,content) VALUES(?,?,?)", (course_id, role, content))

def chat_recent(course_id, n=10):
    rows = db_query("SELECT role,content FROM chat_history WHERE course_id=? ORDER BY id DESC LIMIT ?",
                    (course_id, n), fetch=True)
    rows.reverse()
    return rows
