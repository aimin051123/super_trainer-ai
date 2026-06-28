"""数据库连接 + 建表"""
import sqlite3
from config.settings import DB

def db_query(sql, params=(), fetch=False):
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.execute(sql, params)
    if fetch:
        rows = cur.fetchall()
        conn.close()
        return rows
    conn.commit()
    conn.close()

def db_execute_many(sql, params_list):
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executemany(sql, params_list)
    conn.commit()
    conn.close()

def init_db():
    db_query("""CREATE TABLE IF NOT EXISTS course (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT DEFAULT '',
        exam_date TEXT DEFAULT '', daily_study_minutes INTEGER DEFAULT 240,
        created_at TEXT DEFAULT (datetime('now','localtime')))""")
    db_query("""CREATE TABLE IF NOT EXISTS knowledge_point (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL, name TEXT NOT NULL,
        description TEXT DEFAULT '', importance TEXT DEFAULT 'medium', mastery REAL DEFAULT 0.0,
        total_count INTEGER DEFAULT 0, correct_count INTEGER DEFAULT 0,
        is_weak INTEGER DEFAULT 0, weak_reason TEXT DEFAULT '', last_reviewed TEXT DEFAULT '',
        FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE)""")
    db_query("""CREATE TABLE IF NOT EXISTS quiz_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        quiz_type TEXT NOT NULL DEFAULT 'periodic', total_questions INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0, accuracy REAL DEFAULT 0.0,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE)""")
    db_query("""CREATE TABLE IF NOT EXISTS quiz_question (
        id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_record_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL, knowledge_point_id INTEGER, question_index INTEGER DEFAULT 1,
        question_type TEXT DEFAULT 'choice', content TEXT NOT NULL, options TEXT DEFAULT '[]',
        correct_answer TEXT NOT NULL, user_answer TEXT DEFAULT '', explanation TEXT DEFAULT '',
        difficulty TEXT DEFAULT '基础', created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (quiz_record_id) REFERENCES quiz_record(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
        FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_point(id) ON DELETE SET NULL)""")
    db_query("""CREATE TABLE IF NOT EXISTS wrong_answer (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        knowledge_point_id INTEGER, quiz_question_id INTEGER, question_type TEXT DEFAULT 'choice',
        content TEXT NOT NULL, options TEXT DEFAULT '[]', correct_answer TEXT NOT NULL,
        user_answer TEXT DEFAULT '', explanation TEXT DEFAULT '', review_count INTEGER DEFAULT 0,
        last_reviewed TEXT DEFAULT '', mastered INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
        FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_point(id) ON DELETE SET NULL)""")
    db_query("""CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        role TEXT NOT NULL, content TEXT NOT NULL,
        timestamp TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE)""")
