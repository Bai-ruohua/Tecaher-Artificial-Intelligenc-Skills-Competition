# -*- coding: utf-8 -*-
"""
数据同步引擎 V3.0（课程无关化）
1. 能力雷达图：按课程的"模块(module)"动态聚合（维度数由数据决定）
2. 排名计算：按课程/章节计算（course_id 过滤，互不串扰）
3. 甘特图数据：遍历该课程的 course_chapters
4. 教师仪表盘聚合：汇总所有学生的同步数据
"""
from database import get_db
from knowledge_base import get_course_chapters, get_course_modules, get_course_chapter


def _get_db_conn():
    import sqlite3
    from config import Config
    import os
    os.makedirs(Config.DB_DIR, exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _chapter_module_map(course_id):
    """chapter_id -> module 映射（用于雷达按模块聚合）"""
    chapters = get_course_chapters(course_id)
    return {c["chapter_id"]: c.get("module", "") for c in chapters}


# ===== 1. 能力雷达图 =====

def compute_radar_data(student_id, course_id=None):
    """计算学生的能力雷达图（维度=该课程的 module 集合）"""
    conn = _get_db_conn()

    if not course_id:
        # 无课程上下文时返回空雷达
        conn.close()
        return []

    modules = get_course_modules(course_id)
    ch2mod = _chapter_module_map(course_id)
    mod_chapters = {}
    for cid, mod in ch2mod.items():
        mod_chapters.setdefault(mod, []).append(cid)

    radar = []
    for mod in modules:
        chs = mod_chapters.get(mod, [])
        if not chs:
            radar.append({"dimension": mod, "label": mod, "score": 0, "max_score": 100,
                          "total_attempts": 0, "correct_count": 0, "accuracy": 0})
            continue
        placeholders = ",".join(["?"] * len(chs))
        row = conn.execute(
            f"""SELECT COUNT(*) as total,
                       SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct,
                       AVG(score) as avg_score
                FROM student_attempts
                WHERE student_id=? AND chapter_id IN ({placeholders}) AND course_id=?""",
            [student_id] + chs + [course_id]
        ).fetchone()

        total = row["total"] if row else 0
        correct = row["correct"] if row else 0
        avg_score = row["avg_score"] if row and row["avg_score"] else 0

        if total > 0:
            accuracy = correct / total * 100
            ability_score = round(accuracy * 0.6 + min(avg_score, 100) * 0.4, 1)
        else:
            ability_score = 0

        radar.append({
            "dimension": mod,
            "label": mod,
            "score": ability_score,
            "max_score": 100,
            "total_attempts": total,
            "correct_count": correct,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        })

    conn.close()
    return radar


def compute_class_radar(course_id=None, teacher_id=None):
    """班级整体雷达图平均值（按课程 module）"""
    conn = _get_db_conn()

    if course_id:
        students = conn.execute(
            "SELECT s.id FROM students s JOIN enrollments e ON s.id=e.student_id WHERE e.course_id=? AND s.is_active=1",
            (course_id,)
        ).fetchall()
    elif teacher_id:
        students = conn.execute(
            """SELECT DISTINCT s.id FROM students s
               JOIN enrollments e ON s.id=e.student_id
               JOIN courses c ON e.course_id=c.id
               WHERE c.teacher_id=? AND s.is_active=1""",
            (teacher_id,)
        ).fetchall()
    else:
        students = conn.execute("SELECT id FROM students WHERE is_active=1").fetchall()

    student_ids = [s["id"] for s in students]
    conn.close()

    if not course_id:
        return []
    modules = get_course_modules(course_id)
    if not modules:
        return []
    if not student_ids:
        return [{"dimension": m, "label": m, "score": 0, "max_score": 100} for m in modules]

    all_radars = [compute_radar_data(sid, course_id) for sid in student_ids]
    class_radar = []
    for i, mod in enumerate(modules):
        scores = [r[i]["score"] for r in all_radars if i < len(r) and r[i]["score"] > 0]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        class_radar.append({"dimension": mod, "label": mod, "score": avg, "max_score": 100})
    return class_radar


# ===== 2. 排名计算 =====

def compute_ranking(course_id=None, teacher_id=None, limit=100):
    """计算学生排名（course_id 范围内聚合，避免跨课程串扰）"""
    conn = _get_db_conn()

    if course_id:
        students = conn.execute(
            """SELECT s.id, s.student_no, s.student_name, s.class_name
               FROM students s JOIN enrollments e ON s.id=e.student_id
               WHERE e.course_id=? AND s.is_active=1 ORDER BY s.student_no""",
            (course_id,)
        ).fetchall()
    elif teacher_id:
        students = conn.execute(
            """SELECT DISTINCT s.id, s.student_no, s.student_name, s.class_name, c.course_name
               FROM students s
               JOIN enrollments e ON s.id=e.student_id
               JOIN courses c ON e.course_id=c.id
               WHERE c.teacher_id=? AND s.is_active=1 ORDER BY s.student_no""",
            (teacher_id,)
        ).fetchall()
    else:
        students = conn.execute(
            "SELECT id, student_no, student_name, class_name FROM students WHERE is_active=1 ORDER BY student_no"
        ).fetchall()

    rankings = []
    for s in students:
        course_filter = "AND course_id=?" if course_id else ""
        params = (s["id"], course_id) if course_id else (s["id"],)
        att = conn.execute(
            f"""SELECT COUNT(*) as total,
                      SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct,
                      COALESCE(AVG(score), 0) as avg_score
               FROM student_attempts WHERE student_id=? {course_filter}""",
            params
        ).fetchone()

        log = conn.execute(
            "SELECT COALESCE(SUM(duration_seconds), 0) as total_seconds, COUNT(*) as log_count FROM learning_logs WHERE student_id=?",
            (s["id"],)
        ).fetchone()

        wrong = conn.execute(
            "SELECT COUNT(*) as cnt FROM wrong_books WHERE student_id=?", (s["id"],)
        ).fetchone()

        total = att["total"] if att else 0
        correct = att["correct"] if att else 0
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        avg_score = round(att["avg_score"], 1) if att and att["avg_score"] else 0
        study_minutes = round(log["total_seconds"] / 60, 1) if log and log["total_seconds"] else 0

        volume_score = min(total / 50 * 100, 100)
        time_score = min(study_minutes / 300 * 100, 100)
        composite = round(accuracy * 0.4 + avg_score * 0.3 + volume_score * 0.2 + time_score * 0.1, 1)

        rankings.append({
            "student_id": s["id"],
            "student_no": s["student_no"],
            "student_name": s["student_name"],
            "class_name": s["class_name"] if "class_name" in s.keys() else "",
            "total_attempts": total,
            "correct_count": correct,
            "accuracy": accuracy,
            "avg_score": avg_score,
            "study_minutes": study_minutes,
            "wrong_count": wrong["cnt"] if wrong else 0,
            "composite_score": composite,
        })

    conn.close()
    rankings.sort(key=lambda x: x["composite_score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    return rankings[:limit] if limit else rankings


def get_student_rank(student_id, course_id=None, teacher_id=None):
    rankings = compute_ranking(course_id=course_id, teacher_id=teacher_id)
    for r in rankings:
        if r["student_id"] == student_id:
            return r
    return {"rank": 0, "student_no": "", "student_name": "", "composite_score": 0, "accuracy": 0}


# ===== 3. 甘特图数据（知识掌握时间线）=====

def compute_gantt_data(student_id, course_id=None):
    """计算学生的知识掌握甘特图（遍历该课程 course_chapters）"""
    conn = _get_db_conn()

    chapters = get_course_chapters(course_id) if course_id else []
    gantt = []
    for ch in chapters:
        cid = ch["chapter_id"]
        att = conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct,
                      MIN(attempt_time) as first_attempt,
                      MAX(attempt_time) as last_attempt
               FROM student_attempts WHERE student_id=? AND chapter_id=? AND course_id=?""",
            (student_id, cid, course_id)
        ).fetchone()

        log = conn.execute(
            """SELECT MIN(created_at) as first_log, MAX(created_at) as last_log, COUNT(*) as log_count
               FROM learning_logs WHERE student_id=? AND chapter_id=?""",
            (student_id, cid)
        ).fetchone()

        total = att["total"] if att and att["total"] else 0
        correct = att["correct"] if att and att["correct"] else 0

        if total == 0:
            mastery_level, mastery_percent = "not_started", 0
        else:
            accuracy = correct / total
            if accuracy >= 0.8 and total >= 3:
                mastery_level, mastery_percent = "mastered", round(accuracy * 100, 1)
            elif accuracy >= 0.6:
                mastery_level, mastery_percent = "in_progress", round(accuracy * 100, 1)
            elif accuracy >= 0.4:
                mastery_level, mastery_percent = "weak", round(accuracy * 100, 1)
            else:
                mastery_level, mastery_percent = "very_weak", round(accuracy * 100, 1)

        start = end = ""
        if att and att["first_attempt"]:
            start = str(att["first_attempt"])[:10]
            end = str(att["last_attempt"])[:10] if att["last_attempt"] else start
        elif log and log["first_log"]:
            start = str(log["first_log"])[:10]
            end = str(log["last_log"])[:10] if log["last_log"] else start

        gantt.append({
            "chapter_id": cid,
            "chapter_title": ch["title"],
            "mastery_level": mastery_level,
            "mastery_percent": mastery_percent,
            "attempt_count": total,
            "correct_count": correct,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
            "start_date": start,
            "end_date": end,
        })

    conn.close()
    return gantt


def compute_class_gantt(course_id=None, teacher_id=None):
    """班级整体甘特图（各章节平均掌握度）"""
    conn = _get_db_conn()

    if course_id:
        students = conn.execute(
            "SELECT s.id FROM students s JOIN enrollments e ON s.id=e.student_id WHERE e.course_id=? AND s.is_active=1",
            (course_id,)
        ).fetchall()
    elif teacher_id:
        students = conn.execute(
            """SELECT DISTINCT s.id FROM students s
               JOIN enrollments e ON s.id=e.student_id
               JOIN courses c ON e.course_id=c.id
               WHERE c.teacher_id=? AND s.is_active=1""",
            (teacher_id,)
        ).fetchall()
    else:
        students = conn.execute("SELECT id FROM students WHERE is_active=1").fetchall()

    student_ids = [s["id"] for s in students]
    conn.close()

    if not student_ids or not course_id:
        return []

    all_gantts = [compute_gantt_data(sid, course_id) for sid in student_ids]
    chapters = get_course_chapters(course_id)
    class_gantt = []
    for i, ch in enumerate(chapters):
        percents = [g[i]["mastery_percent"] for g in all_gantts if i < len(g) and g[i]["mastery_percent"] > 0]
        avg = round(sum(percents) / len(percents), 1) if percents else 0
        attempts = [g[i]["attempt_count"] for g in all_gantts if i < len(g)]
        total_attempts = sum(attempts)
        if avg >= 80:
            level = "mastered"
        elif avg >= 60:
            level = "in_progress"
        elif avg >= 40:
            level = "weak"
        elif avg > 0:
            level = "very_weak"
        else:
            level = "not_started"
        class_gantt.append({
            "chapter_id": ch["chapter_id"],
            "chapter_title": ch["title"],
            "mastery_level": level,
            "mastery_percent": avg,
            "total_attempts": total_attempts,
            "student_count": len(student_ids),
        })
    return class_gantt


# ===== 4. 同步入口（学生答题后自动调用）=====

def sync_student_data(student_id, course_id=None):
    """同步学生数据：雷达图 + 甘特图写入数据库缓存"""
    from database import save_ability_score, upsert_mastery_timeline

    radar = compute_radar_data(student_id, course_id=course_id)
    for dim in radar:
        save_ability_score(student_id, dim["dimension"], dim["score"], dim["max_score"], course_id=course_id)

    gantt = compute_gantt_data(student_id, course_id=course_id)
    for g in gantt:
        ch = get_course_chapter(course_id, g["chapter_id"])
        title = ch["title"] if ch else g["chapter_id"]
        upsert_mastery_timeline(
            student_id, g["chapter_id"], title,
            g["mastery_level"], g["mastery_percent"],
            g["attempt_count"], g["correct_count"], course_id=course_id
        )
    return {"radar": radar, "gantt": gantt}


# ===== 5. 教师仪表盘聚合 =====

def get_teacher_dashboard(teacher_id, course_id=None):
    rankings = compute_ranking(course_id=course_id, teacher_id=teacher_id if not course_id else None)
    class_radar = compute_class_radar(course_id=course_id, teacher_id=teacher_id if not course_id else None)
    class_gantt = compute_class_gantt(course_id=course_id, teacher_id=teacher_id if not course_id else None)

    total_students = len(rankings)
    active_students = len([r for r in rankings if r["total_attempts"] > 0])
    avg_accuracy = round(sum(r["accuracy"] for r in rankings) / max(total_students, 1), 1)
    avg_composite = round(sum(r["composite_score"] for r in rankings) / max(total_students, 1), 1)

    return {
        "summary": {
            "total_students": total_students,
            "active_students": active_students,
            "avg_accuracy": avg_accuracy,
            "avg_composite": avg_composite,
        },
        "rankings": rankings,
        "class_radar": class_radar,
        "class_gantt": class_gantt,
    }


def get_student_dashboard(student_id, course_id=None):
    radar = compute_radar_data(student_id, course_id=course_id)
    gantt = compute_gantt_data(student_id, course_id=course_id)
    rank_info = get_student_rank(student_id, course_id=course_id)

    from database import get_student_stats, get_wrong_book
    stats = get_student_stats(student_id)
    wrong_book = get_wrong_book(student_id)

    return {
        "stats": stats,
        "radar": radar,
        "gantt": gantt,
        "rank_info": rank_info,
        "wrong_count": len(wrong_book),
    }
