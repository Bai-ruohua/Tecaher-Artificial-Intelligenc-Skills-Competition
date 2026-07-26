# -*- coding: utf-8 -*-
"""
数据同步引擎 V2.1
功能：
1. 能力雷达图：从答题记录计算5维能力分数
2. 排名计算：按课程/章节计算学生排名
3. 甘特图数据：各章节知识掌握时间线
4. 教师仪表盘聚合：汇总所有学生的同步数据
"""
from database import get_db
from knowledge_base import CHAPTERS, get_chapter
from datetime import datetime


# 12章 -> 5个能力维度映射
ABILITY_DIMENSIONS = [
    {"name": "基础语法", "chapters": ["ch01", "ch02", "ch03"], "label": "Python基础语法"},
    {"name": "控制流", "chapters": ["ch04", "ch05"], "label": "条件与循环"},
    {"name": "数据结构", "chapters": ["ch06", "ch07", "ch08"], "label": "字符串/列表/字典"},
    {"name": "函数模块", "chapters": ["ch09", "ch10"], "label": "函数/文件/异常"},
    {"name": "面向对象", "chapters": ["ch11", "ch12"], "label": "OOP/综合应用"},
]


def _get_db_conn():
    import sqlite3
    from config import Config
    import os
    os.makedirs(Config.DB_DIR, exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===== 1. 能力雷达图 =====

def compute_radar_data(student_id, course_id=None):
    """计算学生的5维能力雷达图数据"""
    conn = _get_db_conn()

    radar = []
    for dim in ABILITY_DIMENSIONS:
        placeholders = ",".join(["?"] * len(dim["chapters"]))
        # 统计该维度下所有章节的答题情况
        row = conn.execute(
            f"""SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct,
                AVG(score) as avg_score
              FROM student_attempts
              WHERE student_id=? AND chapter_id IN ({placeholders})""",
            [student_id] + dim["chapters"]
        ).fetchone()

        total = row["total"] if row else 0
        correct = row["correct"] if row else 0
        avg_score = row["avg_score"] if row and row["avg_score"] else 0

        # 能力分 = 正确率 * 60% + 平均分(归一化到100) * 40%
        if total > 0:
            accuracy = correct / total * 100
            ability_score = round(accuracy * 0.6 + min(avg_score, 100) * 0.4, 1)
        else:
            ability_score = 0

        radar.append({
            "dimension": dim["name"],
            "label": dim["label"],
            "score": ability_score,
            "max_score": 100,
            "total_attempts": total,
            "correct_count": correct,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        })

    conn.close()
    return radar


def compute_class_radar(course_id=None, teacher_id=None):
    """计算班级整体（或教师所有学生）的雷达图平均值"""
    conn = _get_db_conn()

    # 获取学生列表
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

    if not student_ids:
        return [{"dimension": d["name"], "label": d["label"], "score": 0, "max_score": 100} for d in ABILITY_DIMENSIONS]

    # 汇总每个学生的雷达数据
    all_radars = []
    for sid in student_ids:
        r = compute_radar_data(sid)
        all_radars.append(r)

    # 取平均
    class_radar = []
    for i, dim in enumerate(ABILITY_DIMENSIONS):
        scores = [r[i]["score"] for r in all_radars if r[i]["score"] > 0]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        class_radar.append({
            "dimension": dim["name"],
            "label": dim["label"],
            "score": avg,
            "max_score": 100,
        })

    return class_radar


# ===== 2. 排名计算 =====

def compute_ranking(course_id=None, teacher_id=None, limit=100):
    """计算学生排名
    排名依据：总答题数 * 权重 + 正确率 * 权重 + 学习时长 * 权重
    """
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
        # 答题统计
        att = conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct,
                      COALESCE(AVG(score), 0) as avg_score
               FROM student_attempts WHERE student_id=?""",
            (s["id"],)
        ).fetchone()

        # 学习时长
        log = conn.execute(
            "SELECT COALESCE(SUM(duration_seconds), 0) as total_seconds, COUNT(*) as log_count FROM learning_logs WHERE student_id=?",
            (s["id"],)
        ).fetchone()

        # 错题数
        wrong = conn.execute(
            "SELECT COUNT(*) as cnt FROM wrong_books WHERE student_id=?",
            (s["id"],)
        ).fetchone()

        total = att["total"] if att else 0
        correct = att["correct"] if att else 0
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        avg_score = round(att["avg_score"], 1) if att and att["avg_score"] else 0
        study_minutes = round(log["total_seconds"] / 60, 1) if log and log["total_seconds"] else 0

        # 综合得分 = 正确率*40% + 平均分*30% + 答题量归一化*20% + 学习时长归一化*10%
        # 答题量归一化：50题满分
        volume_score = min(total / 50 * 100, 100)
        # 学习时长归一化：300分钟满分
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

    # 按综合得分排序
    rankings.sort(key=lambda x: x["composite_score"], reverse=True)

    # 加排名序号
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return rankings[:limit] if limit else rankings


def get_student_rank(student_id, course_id=None, teacher_id=None):
    """获取单个学生的排名信息"""
    rankings = compute_ranking(course_id=course_id, teacher_id=teacher_id)
    for r in rankings:
        if r["student_id"] == student_id:
            return r
    return {"rank": 0, "student_no": "", "student_name": "", "composite_score": 0, "accuracy": 0}


# ===== 3. 甘特图数据（知识掌握时间线）=====

def compute_gantt_data(student_id):
    """计算学生的知识掌握甘特图数据
    每个章节一个条目，显示掌握程度和进度
    """
    conn = _get_db_conn()

    gantt = []
    for ch in CHAPTERS:
        # 查该章节的答题情况
        att = conn.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct,
                      MIN(attempt_time) as first_attempt,
                      MAX(attempt_time) as last_attempt
               FROM student_attempts WHERE student_id=? AND chapter_id=?""",
            (student_id, ch["id"])
        ).fetchone()

        # 查该章节的学习日志
        log = conn.execute(
            """SELECT MIN(created_at) as first_log, MAX(created_at) as last_log, COUNT(*) as log_count
               FROM learning_logs WHERE student_id=? AND chapter_id=?""",
            (student_id, ch["id"])
        ).fetchone()

        total = att["total"] if att and att["total"] else 0
        correct = att["correct"] if att and att["correct"] else 0

        # 掌握程度
        if total == 0:
            mastery_level = "not_started"
            mastery_percent = 0
        else:
            accuracy = correct / total
            if accuracy >= 0.8 and total >= 3:
                mastery_level = "mastered"
                mastery_percent = round(accuracy * 100, 1)
            elif accuracy >= 0.6:
                mastery_level = "in_progress"
                mastery_percent = round(accuracy * 100, 1)
            elif accuracy >= 0.4:
                mastery_level = "weak"
                mastery_percent = round(accuracy * 100, 1)
            else:
                mastery_level = "very_weak"
                mastery_percent = round(accuracy * 100, 1)

        # 时间线
        start = ""
        end = ""
        if att and att["first_attempt"]:
            start = str(att["first_attempt"])[:10]
            end = str(att["last_attempt"])[:10] if att["last_attempt"] else start
        elif log and log["first_log"]:
            start = str(log["first_log"])[:10]
            end = str(log["last_log"])[:10] if log["last_log"] else start

        gantt.append({
            "chapter_id": ch["id"],
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
    """计算班级整体的甘特图数据（各章节平均掌握度）"""
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

    if not student_ids:
        return []

    # 汇总每个学生的甘特图数据
    all_gantts = []
    for sid in student_ids:
        g = compute_gantt_data(sid)
        all_gantts.append(g)

    # 按章节取平均
    class_gantt = []
    for i, ch in enumerate(CHAPTERS):
        percents = [g[i]["mastery_percent"] for g in all_gantts if g[i]["mastery_percent"] > 0]
        avg = round(sum(percents) / len(percents), 1) if percents else 0

        attempts = [g[i]["attempt_count"] for g in all_gantts]
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
            "chapter_id": ch["id"],
            "chapter_title": ch["title"],
            "mastery_level": level,
            "mastery_percent": avg,
            "total_attempts": total_attempts,
            "student_count": len(student_ids),
        })

    return class_gantt


# ===== 4. 同步入口（学生答题后自动调用）=====

def sync_student_data(student_id):
    """同步学生的所有数据：雷达图 + 甘特图写入数据库缓存"""
    from database import save_ability_score, upsert_mastery_timeline

    # 计算并存储雷达图
    radar = compute_radar_data(student_id)
    for dim in radar:
        save_ability_score(student_id, dim["dimension"], dim["score"], dim["max_score"])

    # 计算并存储甘特图时间线
    gantt = compute_gantt_data(student_id)
    for g in gantt:
        ch = get_chapter(g["chapter_id"])
        title = ch["title"] if ch else g["chapter_id"]
        upsert_mastery_timeline(
            student_id, g["chapter_id"], title,
            g["mastery_level"], g["mastery_percent"],
            g["attempt_count"], g["correct_count"]
        )

    return {"radar": radar, "gantt": gantt}


# ===== 5. 教师仪表盘聚合数据 =====

def get_teacher_dashboard(teacher_id, course_id=None):
    """获取教师仪表盘所有数据"""
    # 排名
    rankings = compute_ranking(course_id=course_id, teacher_id=teacher_id if not course_id else None)

    # 班级雷达图
    class_radar = compute_class_radar(course_id=course_id, teacher_id=teacher_id if not course_id else None)

    # 班级甘特图
    class_gantt = compute_class_gantt(course_id=course_id, teacher_id=teacher_id if not course_id else None)

    # 汇总统计
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


def get_student_dashboard(student_id):
    """获取学生个人仪表盘数据"""
    radar = compute_radar_data(student_id)
    gantt = compute_gantt_data(student_id)
    rank_info = get_student_rank(student_id)

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
