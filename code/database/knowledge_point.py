"""知识点 CRUD"""
import sqlite3
from config.settings import DB
from database.connection import db_query

def kp_upsert(course_id, name, description="", importance="medium"):
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.execute("SELECT id FROM knowledge_point WHERE course_id=? AND name=?", (course_id, name))
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]
    cur.execute("INSERT INTO knowledge_point(course_id,name,description,importance) VALUES(?,?,?,?)",
                (course_id, name, description, importance))
    kp_id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return kp_id

def kp_list(course_id):
    return db_query("SELECT * FROM knowledge_point WHERE course_id=? ORDER BY name", (course_id,), fetch=True)

def kp_get_weak(course_id):
    return db_query("SELECT * FROM knowledge_point WHERE course_id=? AND is_weak=1", (course_id,), fetch=True)

def kp_get_observing(course_id):
    return db_query("SELECT * FROM knowledge_point WHERE course_id=? AND is_weak=0 AND weak_reason='待观察'",
                    (course_id,), fetch=True)
