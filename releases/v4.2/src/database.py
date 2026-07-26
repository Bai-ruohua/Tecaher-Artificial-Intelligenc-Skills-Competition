# -*- coding: utf-8 -*-
"""
数据库模块 - V2.1 师生分离 + 认证体系 + 数据同步
新增表：teachers, courses, enrollments, sessions, ability_scores, mastery_timeline
改造表：students (加 password_hash, course_id, is_active)
"""
import sqlite3
import os
import json
from datetime import datetime
from config import Config


def get_db():
    """获取数据库连接"""
    os.makedirs(Config.DB_DIR, exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    c = conn.cursor()

    # ===== 教师端表 =====

    c.execute("""
        CREATE TABLE IF NOT EXISTS lesson_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id TEXT NOT NULL,
            chapter_title TEXT,
            content TEXT NOT NULL,
            plan_type TEXT DEFAULT 'lesson_plan',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id TEXT NOT NULL,
            q_type TEXT NOT NULL,
            difficulty TEXT DEFAULT 'B',
            question_text TEXT NOT NULL,
            options TEXT,
            answer TEXT NOT NULL,
            explanation TEXT,
            reference_code TEXT,
            test_cases TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_no TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            class_name TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            exam_name TEXT,
            chapter_id TEXT,
            question_type TEXT,
            score REAL DEFAULT 0,
            max_score REAL DEFAULT 100,
            code_content TEXT,
            ai_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== V2.0 学生端新表 =====

    c.execute("""
        CREATE TABLE IF NOT EXISTS student_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            chapter_id TEXT,
            q_type TEXT DEFAULT 'practice',
            question_id INTEGER REFERENCES questions(id),
            student_answer TEXT,
            is_correct INTEGER DEFAULT 0,
            score REAL DEFAULT 0,
            max_score REAL DEFAULT 100,
            ai_feedback TEXT,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS wrong_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            chapter_id TEXT,
            question_id INTEGER REFERENCES questions(id),
            question_text TEXT,
            wrong_answer TEXT,
            correct_answer TEXT,
            explanation TEXT,
            review_count INTEGER DEFAULT 0,
            last_reviewed TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS learning_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            action_type TEXT NOT NULL,
            chapter_id TEXT,
            detail TEXT,
            duration_seconds REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS digital_human_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id TEXT,
            topic_key TEXT,
            answer_text TEXT,
            audio_path TEXT,
            video_path TEXT,
            tts_duration REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            source_chapter TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== V2.1 新增表：认证 + 课程 + 选课 + 能力 + 时间线 =====

    c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            title TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id),
            course_name TEXT NOT NULL,
            semester TEXT DEFAULT '',
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            course_id INTEGER NOT NULL REFERENCES courses(id),
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, course_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            user_role TEXT NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            ip_address TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ability_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            course_id INTEGER REFERENCES courses(id),
            dimension TEXT NOT NULL,
            score REAL DEFAULT 0,
            max_score REAL DEFAULT 100,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mastery_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            chapter_id TEXT NOT NULL,
            chapter_title TEXT,
            start_date TEXT,
            end_date TEXT,
            mastery_level TEXT DEFAULT 'not_started',
            mastery_percent REAL DEFAULT 0,
            attempt_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== V3.0 新增表：课程体系（章节/模块数据化，取代 knowledge_base.py 硬编码）=====

    c.execute("""
        CREATE TABLE IF NOT EXISTS course_chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL REFERENCES courses(id),
            chapter_id TEXT NOT NULL,
            seq INTEGER DEFAULT 0,
            title TEXT NOT NULL,
            level TEXT DEFAULT '',
            module TEXT DEFAULT '',
            keywords TEXT DEFAULT '[]',
            objectives TEXT DEFAULT '[]',
            key_points TEXT DEFAULT '[]',
            difficulties TEXT DEFAULT '[]',
            meta_json TEXT DEFAULT '{}',
            UNIQUE(course_id, chapter_id)
        )
    """)

    # ===== V3.0 新增表：按课程的知识库切片 =====

    c.execute("""
        CREATE TABLE IF NOT EXISTS course_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL REFERENCES courses(id),
            chunk_text TEXT NOT NULL,
            source_file TEXT DEFAULT '',
            chapter_id TEXT DEFAULT '',
            embedding TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 改造现有表：补 course_id
    for tbl in ("questions", "student_attempts", "wrong_books", "mastery_timeline", "grades", "lesson_plans"):
        try:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN course_id INTEGER")
        except sqlite3.OperationalError:
            pass

    # Prompt 缓存表（v4.1）
    c.execute("""
        CREATE TABLE IF NOT EXISTS prompt_cache (
            cache_key TEXT PRIMARY KEY,
            course_id INTEGER,
            chapter_id TEXT,
            func_type TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)

    # 改造 students 表：增加 password_hash, is_active（ALTER TABLE 安全方式）
    try:
        c.execute("ALTER TABLE students ADD COLUMN password_hash TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE students ADD COLUMN is_active INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# ===== 教师端操作函数 =====

def save_lesson_plan(chapter_id, chapter_title, content, plan_type="lesson_plan"):
    conn = get_db()
    conn.execute(
        "INSERT INTO lesson_plans (chapter_id, chapter_title, content, plan_type) VALUES (?, ?, ?, ?)",
        (chapter_id, chapter_title, content, plan_type)
    )
    conn.commit()
    conn.close()


def save_question(chapter_id, q_type, difficulty, question_text, options, answer, explanation, reference_code, test_cases, course_id=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO questions (chapter_id, q_type, difficulty, question_text, options, answer, explanation, reference_code, test_cases, course_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (chapter_id, q_type, difficulty, question_text, options, answer, explanation, reference_code, test_cases, course_id)
    )
    conn.commit()
    conn.close()


def get_or_create_student(student_no, student_name, class_name=""):
    conn = get_db()
    row = conn.execute("SELECT id FROM students WHERE student_no = ?", (student_no,)).fetchone()
    if row:
        sid = row["id"]
        conn.execute("UPDATE students SET student_name=?, class_name=? WHERE id=?",
                     (student_name, class_name, sid))
    else:
        c = conn.execute(
            "INSERT INTO students (student_no, student_name, class_name) VALUES (?, ?, ?)",
            (student_no, student_name, class_name)
        )
        sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid


def save_grade(student_id, exam_name, chapter_id, question_type, score, max_score=100, code_content="", ai_feedback="", course_id=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO grades (student_id, exam_name, chapter_id, question_type, score, max_score, code_content, ai_feedback, course_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (student_id, exam_name, chapter_id, question_type, score, max_score, code_content, ai_feedback, course_id)
    )
    conn.commit()
    conn.close()


def get_grades(filters=None):
    conn = get_db()
    query = """
        SELECT g.*, s.student_no, s.student_name, s.class_name
        FROM grades g LEFT JOIN students s ON g.student_id = s.id
        WHERE 1=1
    """
    params = []
    if filters:
        if "course_id" in filters:
            query += " AND g.course_id = ?"
            params.append(filters["course_id"])
        if "chapter_id" in filters:
            query += " AND g.chapter_id = ?"
            params.append(filters["chapter_id"])
        if "exam_name" in filters:
            query += " AND g.exam_name = ?"
            params.append(filters["exam_name"])
        if "class_name" in filters:
            query += " AND s.class_name = ?"
            params.append(filters["class_name"])
    query += " ORDER BY g.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== V2.0 学生端操作函数 =====

def save_student_attempt(student_id, chapter_id, q_type, question_id, student_answer, is_correct, score, max_score, ai_feedback, course_id=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO student_attempts (student_id, chapter_id, q_type, question_id, student_answer, is_correct, score, max_score, ai_feedback, course_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (student_id, chapter_id, q_type, question_id, student_answer, is_correct, score, max_score, ai_feedback, course_id)
    )
    conn.commit()
    conn.close()


def save_wrong_question(student_id, chapter_id, question_id, question_text, wrong_answer, correct_answer, explanation, course_id=None):
    conn = get_db()
    existing = conn.execute(
        "SELECT id, review_count FROM wrong_books WHERE student_id=? AND question_id=?",
        (student_id, question_id)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE wrong_books SET review_count=review_count+1, last_reviewed=CURRENT_TIMESTAMP WHERE id=?",
            (existing["id"],)
        )
    else:
        conn.execute(
            """INSERT INTO wrong_books (student_id, chapter_id, question_id, question_text, wrong_answer, correct_answer, explanation, course_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (student_id, chapter_id, question_id, question_text, wrong_answer, correct_answer, explanation, course_id)
        )
    conn.commit()
    conn.close()


def get_wrong_book(student_id, chapter_id=None):
    conn = get_db()
    query = "SELECT * FROM wrong_books WHERE student_id = ?"
    params = [student_id]
    if chapter_id:
        query += " AND chapter_id = ?"
        params.append(chapter_id)
    query += " ORDER BY last_reviewed DESC LIMIT ?"
    params.append(Config.MAX_WRONG_BOOK_SIZE)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_learning_log(student_id, action_type, chapter_id="", detail="", duration_seconds=0):
    conn = get_db()
    conn.execute(
        "INSERT INTO learning_logs (student_id, action_type, chapter_id, detail, duration_seconds) VALUES (?, ?, ?, ?, ?)",
        (student_id, action_type, chapter_id, detail, duration_seconds)
    )
    conn.commit()
    conn.close()


def get_student_stats(student_id):
    """获取学生个人学习统计"""
    conn = get_db()
    stats = {}

    # 总答题数
    row = conn.execute("SELECT COUNT(*) as cnt FROM student_attempts WHERE student_id=?", (student_id,)).fetchone()
    stats["total_attempts"] = row["cnt"]

    # 正确率
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM student_attempts WHERE student_id=? AND is_correct=1",
        (student_id,)
    ).fetchone()
    stats["correct_count"] = row["cnt"]
    stats["accuracy"] = round(row["cnt"] / max(stats["total_attempts"], 1) * 100, 1)

    # 错题本数量
    row = conn.execute("SELECT COUNT(*) as cnt FROM wrong_books WHERE student_id=?", (student_id,)).fetchone()
    stats["wrong_count"] = row["cnt"]

    # 学习总时长（分钟）
    row = conn.execute("SELECT COALESCE(SUM(duration_seconds), 0) as total FROM learning_logs WHERE student_id=?", (student_id,)).fetchone()
    stats["total_minutes"] = round(row["total"] / 60, 1)

    conn.close()
    return stats


def save_chat_session(student_id, role, content, source_chapter=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO chat_sessions (student_id, role, content, source_chapter) VALUES (?, ?, ?, ?)",
        (student_id, role, content, source_chapter)
    )
    conn.commit()
    conn.close()


def get_chat_history(student_id, limit=20):
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content, source_chapter FROM chat_sessions WHERE student_id=? ORDER BY created_at DESC LIMIT ?",
        (student_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def save_digital_human_cache(chapter_id, topic_key, answer_text, audio_path="", video_path="", tts_duration=0):
    conn = get_db()
    conn.execute(
        "INSERT INTO digital_human_cache (chapter_id, topic_key, answer_text, audio_path, video_path, tts_duration) VALUES (?, ?, ?, ?, ?, ?)",
        (chapter_id, topic_key, answer_text, audio_path, video_path, tts_duration)
    )
    conn.commit()
    conn.close()


def get_digital_human_cache(topic_key):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM digital_human_cache WHERE topic_key=? ORDER BY created_at DESC LIMIT 1",
        (topic_key,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ===== V2.1 新增：教师端 CRUD =====

def create_teacher(username, password_hash, teacher_name, title="", phone=""):
    conn = get_db()
    try:
        c = conn.execute(
            "INSERT INTO teachers (username, password_hash, teacher_name, title, phone) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, teacher_name, title, phone)
        )
        conn.commit()
        tid = c.lastrowid
        conn.close()
        return tid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_teacher_by_username(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM teachers WHERE username=? AND is_active=1", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_teacher_by_id(teacher_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM teachers WHERE id=?", (teacher_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_teachers():
    conn = get_db()
    rows = conn.execute("SELECT id, username, teacher_name, title, phone, created_at FROM teachers WHERE is_active=1 ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== V2.1 新增：课程管理 =====

def create_course(teacher_id, course_name, semester="", description=""):
    conn = get_db()
    c = conn.execute(
        "INSERT INTO courses (teacher_id, course_name, semester, description) VALUES (?, ?, ?, ?)",
        (teacher_id, course_name, semester, description)
    )
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid


def get_courses_by_teacher(teacher_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM courses WHERE teacher_id=? AND is_active=1 ORDER BY created_at DESC",
        (teacher_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_course_by_id(course_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ===== V2.1 新增：选课关系 =====

def enroll_student(student_id, course_id):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?, ?)",
            (student_id, course_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_students_by_course(course_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT s.*, e.enrolled_at FROM students s
           JOIN enrollments e ON s.id = e.student_id
           WHERE e.course_id=? AND s.is_active=1
           ORDER BY s.student_no""",
        (course_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_students_by_teacher(teacher_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT s.*, c.course_name, c.id as course_id
           FROM students s
           JOIN enrollments e ON s.id = e.student_id
           JOIN courses c ON e.course_id = c.id
           WHERE c.teacher_id=? AND s.is_active=1
           ORDER BY s.student_no""",
        (teacher_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_courses(student_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, t.teacher_name FROM courses c
           JOIN enrollments e ON c.id = e.course_id
           JOIN teachers t ON c.teacher_id = t.id
           WHERE e.student_id=? AND c.is_active=1""",
        (student_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== V2.1 新增：学生账号管理 =====

def create_student_account(student_no, student_name, password_hash, class_name=""):
    conn = get_db()
    try:
        c = conn.execute(
            "INSERT INTO students (student_no, student_name, class_name, password_hash, is_active) VALUES (?, ?, ?, ?, 1)",
            (student_no, student_name, class_name, password_hash)
        )
        conn.commit()
        sid = c.lastrowid
        conn.close()
        return sid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def batch_create_students(student_list, course_id=None):
    """批量创建学生账号
    student_list: [{"student_no": "...", "student_name": "...", "class_name": "...", "password_hash": "..."}]
    返回: {"success": [...], "failed": [...]}
    """
    conn = get_db()
    results = {"success": [], "failed": []}
    for s in student_list:
        try:
            c = conn.execute(
                "INSERT INTO students (student_no, student_name, class_name, password_hash, is_active) VALUES (?, ?, ?, ?, 1)",
                (s["student_no"], s["student_name"], s.get("class_name", ""), s["password_hash"])
            )
            sid = c.lastrowid
            if course_id:
                conn.execute(
                    "INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?, ?)",
                    (sid, course_id)
                )
            results["success"].append({"student_no": s["student_no"], "student_name": s["student_name"], "id": sid})
        except sqlite3.IntegrityError:
            results["failed"].append({"student_no": s["student_no"], "reason": "already exists"})
    conn.commit()
    conn.close()
    return results


def get_student_by_username(student_no):
    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE student_no=? AND is_active=1", (student_no,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_student_by_id(student_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_student_password(student_id, password_hash):
    conn = get_db()
    conn.execute("UPDATE students SET password_hash=? WHERE id=?", (password_hash, student_id))
    conn.commit()
    conn.close()


# ===== V2.1 新增：Session管理 =====

def create_session(session_token, user_id, user_role, ip_address="", expires_hours=24):
    conn = get_db()
    conn.execute(
        """INSERT INTO sessions (session_token, user_id, user_role, ip_address, expires_at)
           VALUES (?, ?, ?, ?, datetime('now', '+' || ? || ' hours'))""",
        (session_token, user_id, user_role, ip_address, str(expires_hours))
    )
    conn.commit()
    conn.close()


def get_session(session_token):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_token=? AND expires_at > datetime('now')",
        (session_token,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session(session_token):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE session_token=?", (session_token,))
    conn.commit()
    conn.close()


# ===== V2.1 新增：能力评分 =====

def save_ability_score(student_id, dimension, score, max_score=100, course_id=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO ability_scores (student_id, course_id, dimension, score, max_score)
           VALUES (?, ?, ?, ?, ?)""",
        (student_id, course_id, dimension, score, max_score)
    )
    conn.commit()
    conn.close()


def get_ability_scores(student_id, course_id=None):
    conn = get_db()
    if course_id:
        rows = conn.execute(
            "SELECT * FROM ability_scores WHERE student_id=? AND course_id=? ORDER BY computed_at DESC",
            (student_id, course_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM ability_scores WHERE student_id=? ORDER BY computed_at DESC",
            (student_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== V2.1 新增：知识掌握时间线（甘特图数据源）=====

def upsert_mastery_timeline(student_id, chapter_id, chapter_title, mastery_level, mastery_percent, attempt_count, correct_count, course_id=None):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM mastery_timeline WHERE student_id=? AND chapter_id=?",
        (student_id, chapter_id)
    ).fetchone()
    if existing:
        conn.execute(
            """UPDATE mastery_timeline SET chapter_title=?, mastery_level=?, mastery_percent=?,
               attempt_count=?, correct_count=?, course_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (chapter_title, mastery_level, mastery_percent, attempt_count, correct_count, course_id, existing["id"])
        )
    else:
        conn.execute(
            """INSERT INTO mastery_timeline (student_id, chapter_id, chapter_title, mastery_level, mastery_percent, attempt_count, correct_count, course_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (student_id, chapter_id, chapter_title, mastery_level, mastery_percent, attempt_count, correct_count, course_id)
        )
    conn.commit()
    conn.close()


def get_mastery_timeline(student_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM mastery_timeline WHERE student_id=? ORDER BY chapter_id",
        (student_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== V3.0 新增：课程体系（course_chapters）CRUD =====

def get_first_course_id():
    """返回数据库中第一个课程 id（作为无显式课程上下文时的兜底）"""
    conn = get_db()
    row = conn.execute("SELECT id FROM courses WHERE is_active=1 ORDER BY id ASC LIMIT 1").fetchone()
    conn.close()
    return row["id"] if row else None


def create_course_chapter(course_id, chapter_id, title, seq=0, level="", module="",
                          keywords=None, objectives=None, key_points=None, difficulties=None, meta_json=None):
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO course_chapters
           (course_id, chapter_id, seq, title, level, module, keywords, objectives, key_points, difficulties, meta_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            course_id, chapter_id, seq, title, level, module,
            json.dumps(keywords or [], ensure_ascii=False),
            json.dumps(objectives or [], ensure_ascii=False),
            json.dumps(key_points or [], ensure_ascii=False),
            json.dumps(difficulties or [], ensure_ascii=False),
            json.dumps(meta_json or {}, ensure_ascii=False),
        )
    )
    conn.commit()
    conn.close()


def get_course_chapters(course_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM course_chapters WHERE course_id=? ORDER BY seq ASC, chapter_id ASC",
        (course_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_course_chapter(course_id, chapter_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM course_chapters WHERE course_id=? AND chapter_id=?",
        (course_id, chapter_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_chapter(course_id, chapter_id):
    """兼容旧调用的课程内章节查询（course_id 必填）"""
    return get_course_chapter(course_id, chapter_id)


def delete_course_chapter(course_id, chapter_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM course_chapters WHERE course_id=? AND chapter_id=?",
        (course_id, chapter_id)
    )
    conn.commit()
    conn.close()


def get_course_modules(course_id):
    """返回该课程去重后的模块(维度)列表，用于雷达聚合"""
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT module FROM course_chapters WHERE course_id=? AND module<>'' ORDER BY seq ASC",
        (course_id,)
    ).fetchall()
    conn.close()
    return [r["module"] for r in rows]


# ===== V3.0 新增：按课程知识库切片（course_documents）CRUD =====

def save_course_document(course_id, chunk_text, source_file="", chapter_id=""):
    conn = get_db()
    c = conn.execute(
        """INSERT INTO course_documents (course_id, chunk_text, source_file, chapter_id)
           VALUES (?, ?, ?, ?)""",
        (course_id, chunk_text, source_file, chapter_id)
    )
    cid = c.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_course_documents(course_id, limit=200):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM course_documents WHERE course_id=? ORDER BY id ASC LIMIT ?",
        (course_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_course_documents(course_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM course_documents WHERE course_id=?", (course_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0


def delete_course_documents(course_id):
    conn = get_db()
    conn.execute("DELETE FROM course_documents WHERE course_id=?", (course_id,))
    conn.commit()
    conn.close()


# ===== V3.0 新增：种子课程（把 knowledge_base 的 Python 12章写入 DB）=====

def seed_course_chapters_from_seed(course_id, seed_list):
    """seed_list: knowledge_base.SEED_PYTHON_CHAPTERS 元素，写入 course_chapters"""
    for idx, ch in enumerate(seed_list):
        create_course_chapter(
            course_id=course_id,
            chapter_id=ch["id"],
            title=ch["title"],
            seq=idx,
            level=ch.get("level", ""),
            module=ch.get("module", ""),
            keywords=ch.get("keywords", []),
            objectives=ch.get("objectives", []),
            key_points=ch.get("key_points", []),
            difficulties=ch.get("difficulties", []),
            meta_json={"relations": ch.get("relations", {})},
        )

