# -*- coding: utf-8 -*-
"""
AI智能教学平台 - Flask主应用 (V3.0 课程无关化 + 师生共用智能体 + 双端首页功能区)
宜宾工业职业技术学院 · 数字经济学院
四川省第二届教师人工智能应用能力大赛 · 赛道三
"""
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
from flask_cors import CORS

from config import Config
from database import (
    init_db, save_lesson_plan, save_question, save_grade, get_or_create_student, get_grades,
    save_student_attempt, save_wrong_question, get_wrong_book, save_learning_log,
    get_student_stats, save_chat_session, get_chat_history, get_digital_human_cache,
    create_teacher, get_all_teachers, get_teacher_by_id,
    get_courses_by_teacher, get_course_by_id, get_students_by_teacher,
    get_students_by_course, get_student_by_id, get_student_courses,
    get_course_chapters, get_course_chapter, get_course_modules,
)
from knowledge_base import get_course_chapters, get_course_chapter, search_by_keyword, get_course_modules

from modules.lesson_prep import generate_lesson_plan, generate_courseware, generate_ideology, generate_practice
from modules.exam_generator import generate_questions, generate_mixed_paper
from modules.code_grader import grade_code, diagnose_bug, batch_grade, check_similarity
from modules.analytics import analyze_class_trend, detect_risk_students, analyze_chapter_mastery, generate_full_report
from modules.student_agents import (
    student_qa, generate_quiz_questions, grade_quiz_answer, get_wrong_book_summary, get_chapter_qa_guide,
)
from modules.knowledge_graph import generate_graph_data, get_chapter_detail_for_graph
from modules.digital_human import digital_human
from modules.data_sync import (
    get_teacher_dashboard, get_student_dashboard,
    sync_student_data, compute_ranking, compute_radar_data, compute_gantt_data,
)
from modules.knowledge_store import ingest_document, get_documents, count_documents, delete_documents

from auth import (
    do_login, logout_user, get_current_user,
    login_required, teacher_required, student_required,
    init_default_teacher, seed_default_courses, hash_password,
    get_current_course_id, set_current_course,
    handle_create_course, handle_get_teacher_courses,
    handle_batch_create_students, handle_batch_generate_students,
)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
CORS(app, supports_credentials=True)

# 初始化数据库 + 默认教师 + 示例课程(Python)
init_db()
init_default_teacher()
seed_default_courses()


# ===== 通用上下文助手 =====

def _course_ctx():
    """为模板准备课程上下文（当前课程/章节列表/课程列表）"""
    user = get_current_user()
    course_id = get_current_course_id(user)
    course = get_course_by_id(course_id) if course_id else None
    chapters = get_course_chapters(course_id) if course_id else []
    courses = []
    if user:
        courses = get_courses_by_teacher(user["user_id"]) if user["user_role"] == "teacher" else get_student_courses(user["user_id"])
    return course_id, course, chapters, courses


def _resolve_course_id():
    """API 中解析 course_id：优先 JSON/参数，其次会话当前课程"""
    data = request.get_json(silent=True) or {}
    cid = data.get("course_id") or request.args.get("course_id", type=int)
    if cid:
        return cid
    return get_current_course_id(get_current_user())


# ==================== 认证路由 ====================

@app.route("/login")
def login_page():
    user = get_current_user()
    if user:
        return redirect(url_for("teacher_dashboard_page" if user["user_role"] == "teacher" else "student_dashboard_page"))
    return render_template("login.html", config=Config)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login_page"))


# ==================== 仪表盘页面 ====================

@app.route("/")
@login_required
def index():
    user = get_current_user()
    if user["user_role"] == "teacher":
        return redirect(url_for("teacher_dashboard_page"))
    return redirect(url_for("student_dashboard_page"))


@app.route("/teacher/dashboard")
@teacher_required
def teacher_dashboard_page():
    user = get_current_user()
    teacher = get_teacher_by_id(user["user_id"])
    course_id, course, chapters, courses = _course_ctx()
    return render_template("teacher/dashboard.html", teacher=teacher, courses=courses,
                           course=course, course_id=course_id, chapters=chapters, config=Config, role="teacher")


@app.route("/student/dashboard")
@student_required
def student_dashboard_page():
    user = get_current_user()
    student = get_student_by_id(user["user_id"])
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/dashboard.html", student=student, courses=courses,
                           course=course, course_id=course_id, chapters=chapters, config=Config, role="student")


# ==================== 教师端页面（需教师登录）====================

@app.route("/teacher/lesson-prep")
@teacher_required
def lesson_prep_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("teacher/lesson_prep.html", course=course, course_id=course_id, chapters=chapters, courses=courses, config=Config, role="teacher")


@app.route("/teacher/exam")
@teacher_required
def exam_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("teacher/exam.html", course=course, course_id=course_id, chapters=chapters, courses=courses, config=Config, role="teacher")


@app.route("/teacher/grading")
@teacher_required
def grading_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("teacher/grading.html", course=course, course_id=course_id, chapters=chapters, courses=courses, config=Config, role="teacher")


@app.route("/teacher/analytics")
@teacher_required
def analytics_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("teacher/analytics.html", course=course, course_id=course_id, chapters=chapters, courses=courses, config=Config, role="teacher")


@app.route("/teacher/students")
@teacher_required
def student_management_page():
    user = get_current_user()
    teacher = get_teacher_by_id(user["user_id"])
    course_id, course, chapters, courses = _course_ctx()
    return render_template("teacher/students.html", teacher=teacher, courses=courses,
                           course=course, course_id=course_id, chapters=chapters, config=Config, role="teacher")


# ==================== 学生端页面（需登录）====================

@app.route("/student/qa")
@login_required
def student_qa_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_qa.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="student")


@app.route("/student/quiz")
@login_required
def student_quiz_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_quiz.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="student")


@app.route("/student/digital")
@login_required
def student_digital_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_digital.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="student")


@app.route("/student/graph")
@login_required
def student_graph_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_graph.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="student")


# ==================== 教师端 Agent 页面（师生共用一套能力）====================

@app.route("/teacher/qa")
@teacher_required
def teacher_qa_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_qa.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="teacher")


@app.route("/teacher/exam-preview")
@teacher_required
def teacher_exam_preview_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_quiz.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="teacher")


@app.route("/teacher/digital")
@teacher_required
def teacher_digital_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_digital.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="teacher")


@app.route("/teacher/graph")
@teacher_required
def teacher_graph_page():
    course_id, course, chapters, courses = _course_ctx()
    return render_template("student/agent_graph.html", course=course, course_id=course_id, chapters=chapters, config=Config, role="teacher")


# ==================== API：认证 ====================

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "auto")

    success, user_info, error = do_login(username, password, role)
    if success:
        return jsonify({"success": True, "data": user_info})
    return jsonify({"success": False, "error": error}), 401


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/auth/me")
def api_me():
    user = get_current_user()
    if user:
        return jsonify({"success": True, "data": user})
    return jsonify({"success": False, "error": "not logged in"}), 401


# ==================== API：当前课程上下文 ====================

@app.route("/api/course/select", methods=["POST"])
@login_required
def api_course_select():
    data = request.json or {}
    cid = data.get("course_id")
    if set_current_course(cid):
        return jsonify({"success": True, "course_id": cid})
    return jsonify({"success": False, "error": "无权访问该课程"}), 403


@app.route("/api/course/current")
@login_required
def api_course_current():
    course_id = get_current_course_id(get_current_user())
    course = get_course_by_id(course_id) if course_id else None
    return jsonify({"success": True, "course_id": course_id, "course": course})


@app.route("/api/course/chapters")
@login_required
def api_course_chapters():
    course_id = _resolve_course_id()
    chapters = get_course_chapters(course_id)
    return jsonify({"success": True, "course_id": course_id, "chapters": chapters})


@app.route("/api/version")
def api_version():
    return jsonify({"success": True, "platform_version": Config.PLATFORM_VERSION, "platform_name": Config.PLATFORM_NAME})


# ==================== API：教师课程管理 ====================

@app.route("/api/teacher/courses", methods=["GET"])
@teacher_required
def api_teacher_courses():
    user = get_current_user()
    courses = handle_get_teacher_courses(user["user_id"])
    return jsonify({"success": True, "courses": courses})


@app.route("/api/teacher/courses", methods=["POST"])
@teacher_required
def api_create_course():
    user = get_current_user()
    data = request.json
    cid = handle_create_course(
        user["user_id"],
        data.get("course_name", ""),
        data.get("semester", ""),
        data.get("description", ""),
    )
    return jsonify({"success": True, "course_id": cid})


# ==================== API：学生账号管理 ====================

@app.route("/api/teacher/students/list", methods=["GET"])
@teacher_required
def api_student_list():
    user = get_current_user()
    course_id = request.args.get("course_id", type=int)
    if course_id:
        students = get_students_by_course(course_id)
    else:
        students = get_students_by_teacher(user["user_id"])
    return jsonify({"success": True, "students": students, "total": len(students)})


@app.route("/api/teacher/students/batch-create", methods=["POST"])
@teacher_required
def api_batch_create():
    data = request.json
    course_id = data.get("course_id")
    student_list = data.get("students", [])
    default_password = data.get("default_password", "123456")

    results = handle_batch_create_students(
        teacher_id=get_current_user()["user_id"],
        course_id=course_id,
        student_data_list=student_list,
        default_password=default_password,
    )
    return jsonify({"success": True, "data": results})


@app.route("/api/teacher/students/batch-generate", methods=["POST"])
@teacher_required
def api_batch_generate():
    data = request.json
    course_id = data.get("course_id")
    prefix = data.get("prefix", "2024")
    count = data.get("count", 10)
    class_name = data.get("class_name", "")
    default_password = data.get("default_password", "123456")

    if count > 200:
        return jsonify({"success": False, "error": "单次最多生成200个账号"}), 400

    results = handle_batch_generate_students(
        teacher_id=get_current_user()["user_id"],
        course_id=course_id,
        prefix=prefix,
        count=count,
        class_name=class_name,
        default_password=default_password,
    )
    return jsonify({"success": True, "data": results})


# ==================== API：知识库管理（按课程上传文档）====================

@app.route("/api/teacher/knowledge/ingest", methods=["POST"])
@teacher_required
def api_knowledge_ingest():
    """上传文档到当前课程的 RAG 知识库（前端以 multipart/form-data 上传）"""
    course_id = _resolve_course_id()
    if not course_id:
        return jsonify({"success": False, "error": "未选择课程"}), 400
    if "file" not in request.files:
        return jsonify({"success": False, "error": "请选择文件"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "error": "文件名空"}), 400
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), f.filename)
    f.save(tmp)
    try:
        res = ingest_document(course_id, tmp)
    except Exception as e:
        return jsonify({"success": False, "error": f"解析失败: {str(e)}"}), 500
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    return jsonify({"success": True, "data": res})


@app.route("/api/teacher/knowledge/docs", methods=["GET"])
@teacher_required
def api_knowledge_docs():
    course_id = _resolve_course_id()
    docs = get_documents(course_id, limit=500)
    cnt = count_documents(course_id)
    return jsonify({"success": True, "count": cnt, "documents": [{"id": d["id"], "source": d["source_file"], "chapter": d["chapter_id"]} for d in docs]})


@app.route("/api/teacher/knowledge/clear", methods=["POST"])
@teacher_required
def api_knowledge_clear():
    course_id = _resolve_course_id()
    delete_documents(course_id)
    return jsonify({"success": True})


# ==================== API：教师仪表盘数据 ====================

@app.route("/api/teacher/dashboard")
@teacher_required
def api_teacher_dashboard():
    user = get_current_user()
    course_id = request.args.get("course_id", type=int)
    data = get_teacher_dashboard(user["user_id"], course_id=course_id)
    return jsonify({"success": True, "data": data})


@app.route("/api/teacher/rankings")
@teacher_required
def api_teacher_rankings():
    user = get_current_user()
    course_id = request.args.get("course_id", type=int)
    rankings = compute_ranking(course_id=course_id, teacher_id=user["user_id"] if not course_id else None)
    return jsonify({"success": True, "rankings": rankings})


@app.route("/api/teacher/radar")
@teacher_required
def api_teacher_radar():
    user = get_current_user()
    course_id = request.args.get("course_id", type=int) or get_current_course_id(user)
    from modules.data_sync import compute_class_radar
    radar = compute_class_radar(course_id=course_id, teacher_id=user["user_id"] if not course_id else None)
    return jsonify({"success": True, "radar": radar})


@app.route("/api/teacher/gantt")
@teacher_required
def api_teacher_gantt():
    user = get_current_user()
    course_id = request.args.get("course_id", type=int) or get_current_course_id(user)
    from modules.data_sync import compute_class_gantt
    gantt = compute_class_gantt(course_id=course_id, teacher_id=user["user_id"] if not course_id else None)
    return jsonify({"success": True, "gantt": gantt})


# ==================== API：学生仪表盘数据 ====================

@app.route("/api/student/dashboard")
@student_required
def api_student_dashboard():
    user = get_current_user()
    course_id = get_current_course_id(user)
    data = get_student_dashboard(user["user_id"], course_id=course_id)
    return jsonify({"success": True, "data": data})


@app.route("/api/student/radar")
@student_required
def api_student_radar():
    user = get_current_user()
    course_id = get_current_course_id(user)
    radar = compute_radar_data(user["user_id"], course_id=course_id)
    return jsonify({"success": True, "radar": radar})


@app.route("/api/student/gantt")
@student_required
def api_student_gantt():
    user = get_current_user()
    course_id = get_current_course_id(user)
    gantt = compute_gantt_data(user["user_id"], course_id=course_id)
    return jsonify({"success": True, "gantt": gantt})


@app.route("/api/student/ranking")
@student_required
def api_student_ranking():
    user = get_current_user()
    course_id = get_current_course_id(user)
    rank_info = compute_ranking(course_id=course_id)
    my_rank = None
    for i, r in enumerate(rank_info):
        if r["student_id"] == user["user_id"]:
            my_rank = r
            my_rank["total_students"] = len(rank_info)
            break
    if not my_rank:
        my_rank = {"rank": len(rank_info) + 1, "total_students": len(rank_info), "composite_score": 0}
    return jsonify({"success": True, "data": my_rank})


# ==================== API：备课助手 ====================

@app.route("/api/lesson-plan", methods=["POST"])
@teacher_required
def api_lesson_plan():
    data = request.json
    course_id = _resolve_course_id()
    result = generate_lesson_plan(data.get("chapter_id"), data.get("extra_requirements", ""), course_id=course_id)
    ch = get_course_chapter(course_id, data.get("chapter_id"))
    if ch:
        save_lesson_plan(data["chapter_id"], ch["title"], result, "lesson_plan")
    return jsonify({"success": True, "content": result})


@app.route("/api/courseware", methods=["POST"])
@teacher_required
def api_courseware():
    data = request.json
    course_id = _resolve_course_id()
    result = generate_courseware(data.get("chapter_id"), data.get("lesson_plan_text", ""), course_id=course_id)
    return jsonify({"success": True, "content": result})


@app.route("/api/ideology", methods=["POST"])
@teacher_required
def api_ideology():
    data = request.json
    course_id = _resolve_course_id()
    result = generate_ideology(data.get("chapter_id"), data.get("topic", ""), course_id=course_id)
    return jsonify({"success": True, "content": result})


@app.route("/api/practice", methods=["POST"])
@teacher_required
def api_practice():
    data = request.json
    course_id = _resolve_course_id()
    result = generate_practice(data.get("chapter_id"), course_id=course_id)
    return jsonify({"success": True, "content": result})


# ==================== API：命题助手 ====================

@app.route("/api/questions", methods=["POST"])
@teacher_required
def api_questions():
    data = request.json
    course_id = _resolve_course_id()
    result = generate_questions(
        data.get("chapter_id"), data.get("q_type", "choice"),
        data.get("count", 5), data.get("difficulty", "B"), course_id=course_id
    )
    return jsonify({"success": True, "content": result})


@app.route("/api/exam-paper", methods=["POST"])
@teacher_required
def api_exam_paper():
    data = request.json
    course_id = _resolve_course_id()
    result = generate_mixed_paper(data.get("chapter_id"), data.get("config"), course_id=course_id)
    return jsonify({"success": True, "content": result})


# ==================== API：批改助手 ====================

@app.route("/api/grade", methods=["POST"])
@teacher_required
def api_grade():
    data = request.json
    course_id = _resolve_course_id()
    result = grade_code(data.get("code", ""), data.get("task_description", ""), data.get("chapter_id"), course_id=course_id)
    return jsonify({"success": True, "content": result})


@app.route("/api/diagnose", methods=["POST"])
@teacher_required
def api_diagnose():
    data = request.json
    result = diagnose_bug(data.get("code", ""), data.get("error_message", ""), data.get("chapter_id"))
    return jsonify({"success": True, "content": result})


@app.route("/api/batch-grade", methods=["POST"])
@teacher_required
def api_batch_grade():
    data = request.json
    result = batch_grade(data.get("submissions", []), data.get("task_description", ""))
    return jsonify({"success": True, "content": result})


@app.route("/api/similarity", methods=["POST"])
@teacher_required
def api_similarity():
    data = request.json
    result = check_similarity(data.get("code_list", []))
    return jsonify({"success": True, "data": result})


# ==================== API：学情分析 ====================

@app.route("/api/analytics/trend", methods=["POST"])
@teacher_required
def api_analytics_trend():
    result = analyze_class_trend(grades=request.json.get("grades", []))
    return jsonify({"success": True, "data": result})


@app.route("/api/analytics/risk", methods=["POST"])
@teacher_required
def api_analytics_risk():
    data = request.json
    result = detect_risk_students(data.get("grades", []), data.get("threshold", 60))
    return jsonify({"success": True, "data": result})


@app.route("/api/analytics/mastery", methods=["POST"])
@teacher_required
def api_analytics_mastery():
    result = analyze_chapter_mastery(grades=request.json.get("grades", []))
    return jsonify({"success": True, "data": result})


@app.route("/api/analytics/full-report", methods=["POST"])
@teacher_required
def api_analytics_full():
    data = request.json
    result = generate_full_report(data.get("grades", []), data.get("class_name", ""))
    return jsonify({"success": True, "data": result})


@app.route("/api/analytics/import", methods=["POST"])
@teacher_required
def api_analytics_import():
    data = request.json
    grades = data.get("grades", [])
    results = []
    for g in grades:
        try:
            sid = get_or_create_student(
                g.get("student_no", ""), g.get("student_name", ""), g.get("class_name", "")
            )
            save_grade(sid, g.get("exam_name", ""), g.get("chapter_id", ""),
                       g.get("question_type", ""), g.get("score", 0), g.get("max_score", 100),
                       g.get("code_content", ""), g.get("ai_feedback", ""))
            results.append({"student_no": g.get("student_no"), "status": "ok"})
        except Exception as e:
            results.append({"student_no": g.get("student_no"), "status": "error", "error": str(e)})
    return jsonify({"success": True, "imported": len(results), "details": results})


# ==================== API：智能体（师生共用，双角色均可访问）====================

# --- Agent 1: RAG课程助教 ---

@app.route("/api/student/qa", methods=["POST"])
@login_required
def api_student_qa():
    data = request.json
    user = get_current_user()
    student_id = user["user_id"]
    question = data.get("question", "")
    history = data.get("history", [])
    course_id = _resolve_course_id()
    course = get_course_by_id(course_id)
    course_name = course["course_name"] if course else ""

    if not question.strip():
        return jsonify({"success": False, "error": "请输入问题"}), 400

    try:
        result = student_qa(student_id, question, history, course_id=course_id, course_name=course_name)
        save_learning_log(student_id, "qa_ask", detail=question[:200])
        save_chat_session(student_id, "user", question)
        save_chat_session(student_id, "assistant", result["answer"],
                          source_chapter=result.get("sources", [{}])[0].get("chapter_id", ""))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/student/qa/guide/<chapter_id>", methods=["GET"])
@login_required
def api_chapter_qa_guide(chapter_id):
    course_id = _resolve_course_id()
    questions = get_chapter_qa_guide(chapter_id, course_id=course_id)
    return jsonify({"success": True, "questions": questions})


@app.route("/api/student/chat-history", methods=["GET"])
@login_required
def api_chat_history():
    user = get_current_user()
    limit = int(request.args.get("limit", 20))
    history = get_chat_history(user["user_id"], limit)
    return jsonify({"success": True, "history": history})


@app.route("/api/student/stats", methods=["GET"])
@login_required
def api_student_stats():
    user = get_current_user()
    stats = get_student_stats(user["user_id"])
    return jsonify({"success": True, "stats": stats})


# --- Agent 2: 刷题判分 ---

@app.route("/api/student/quiz/generate", methods=["POST"])
@login_required
def api_quiz_generate():
    data = request.json
    chapter_id = data.get("chapter_id")
    count = data.get("count", 5)
    difficulty = data.get("difficulty", "B")
    course_id = _resolve_course_id()

    if not chapter_id:
        return jsonify({"success": False, "error": "请选择章节"}), 400

    try:
        result = generate_quiz_questions(chapter_id, count, difficulty, course_id=course_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/student/quiz/submit", methods=["POST"])
@login_required
def api_quiz_submit():
    data = request.json
    user = get_current_user()
    student_id = user["user_id"]
    chapter_id = data.get("chapter_id", "")
    questions = data.get("questions", [])
    answers = data.get("answers", {})
    course_id = _resolve_course_id()

    if not questions:
        return jsonify({"success": False, "error": "没有题目数据"}), 400

    results = []
    correct_count = 0

    for i, q in enumerate(questions):
        student_answer = answers.get(str(i), "")
        is_correct = grade_quiz_answer(q, student_answer)

        if is_correct:
            correct_count += 1
        else:
            save_wrong_question(
                student_id, chapter_id, i,
                q.get("question", ""), student_answer,
                q.get("answer", ""), q.get("explanation", ""), course_id=course_id
            )

        save_student_attempt(
            student_id, chapter_id, q.get("type", "choice"),
            i, student_answer, 1 if is_correct else 0,
            100 if is_correct else 0, 100,
            q.get("explanation", "")[:500], course_id=course_id
        )

        results.append({
            "index": i,
            "question": q.get("question", ""),
            "type": q.get("type", ""),
            "student_answer": student_answer,
            "correct_answer": q.get("answer", ""),
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    save_learning_log(student_id, "quiz_practice", chapter_id,
                      f"答题{len(questions)}题，正确{correct_count}题")

    # === 答题后自动同步数据（限定课程） ===
    try:
        sync_student_data(student_id, course_id=course_id)
    except Exception:
        pass

    total = len(questions)
    return jsonify({
        "success": True,
        "data": {
            "results": results,
            "total": total,
            "correct": correct_count,
            "accuracy": round(correct_count / total * 100, 1) if total > 0 else 0,
        }
    })


@app.route("/api/student/quiz/wrong-book", methods=["GET"])
@login_required
def api_wrong_book():
    user = get_current_user()
    course_id = _resolve_course_id()
    chapter_id = request.args.get("chapter_id")
    wrong_items = get_wrong_book(user["user_id"], chapter_id)
    summary = get_wrong_book_summary(wrong_items, course_id=course_id)
    return jsonify({"success": True, "items": wrong_items, "summary": summary})


# --- Agent 3: 数字人讲解 ---

@app.route("/api/student/digital/explain", methods=["POST"])
@login_required
def api_digital_explain():
    data = request.json
    user = get_current_user()
    student_id = user["user_id"]
    topic = data.get("topic", "")
    chapter_id = data.get("chapter_id", "")
    method = data.get("method", "auto")
    course_id = _resolve_course_id()

    if not topic.strip() and not chapter_id:
        return jsonify({"success": False, "error": "请输入问题或选择章节"}), 400

    try:
        course = get_course_by_id(course_id)
        course_name = course["course_name"] if course else ""
        qa_result = student_qa(student_id, topic or f"请讲解{chapter_id}章节的内容", [], course_id=course_id, course_name=course_name)

        import hashlib
        topic_key = hashlib.md5(topic.encode()).hexdigest()[:12]

        video_result = digital_human.generate_video(
            topic_key=topic_key,
            answer_text=qa_result["answer"][:500],
            chapter_id=chapter_id,
            method=method,
        )

        save_learning_log(student_id, "digital_explain", chapter_id, topic[:200])

        return jsonify({
            "success": True,
            "data": {
                "answer": qa_result["answer"],
                "sources": qa_result["sources"][:3],
                "video_path": video_result.get("video_path"),
                "audio_path": video_result.get("audio_path"),
                "method": video_result.get("method"),
                "fallback": video_result.get("fallback", False),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/student/digital/pre-generate", methods=["POST"])
@teacher_required
def api_digital_pre_generate():
    data = request.json
    chapter_id = data.get("chapter_id")
    course_id = _resolve_course_id()
    result = digital_human.pre_generate_chapters(chapter_id, course_id=course_id)
    return jsonify({"success": True, "data": result})


@app.route("/api/student/digital/config")
@login_required
def api_digital_config():
    return jsonify({
        "success": True,
        "configured": digital_human.is_configured(),
        "has_sadtalker": bool(os.environ.get("SADTALKER_PATH")),
        "has_did_api": bool(Config.DID_API_KEY),
    })


# --- Agent 4: 知识图谱 ---

@app.route("/api/student/graph/data")
@login_required
def api_graph_data():
    course_id = _resolve_course_id()
    data = generate_graph_data(course_id)
    return jsonify({"success": True, "data": data})


@app.route("/api/student/graph/detail/<chapter_id>")
@login_required
def api_graph_detail(chapter_id):
    course_id = _resolve_course_id()
    detail = get_chapter_detail_for_graph(course_id, chapter_id)
    if not detail:
        return jsonify({"success": False, "error": "章节不存在"}), 404
    return jsonify({"success": True, "data": detail})


# ==================== 通用API ====================

@app.route("/api/chapters")
@login_required
def api_chapters():
    course_id = _resolve_course_id()
    return jsonify({"success": True, "course_id": course_id, "chapters": get_course_chapters(course_id)})


@app.route("/api/chapter/<chapter_id>")
@login_required
def api_chapter(chapter_id):
    course_id = _resolve_course_id()
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return jsonify({"success": False, "error": "章节不存在"}), 404
    return jsonify({"success": True, "chapter": ch})


@app.route("/api/search", methods=["GET"])
@login_required
def api_search():
    keyword = request.args.get("q", "").strip()
    course_id = _resolve_course_id()
    if not keyword:
        return jsonify({"success": False, "error": "请输入搜索关键词"}), 400
    results = search_by_keyword(keyword, course_id=course_id)
    return jsonify({"success": True, "results": results})


@app.route("/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory(Config.VIDEO_DIR, filename)


# ==================== 启动 ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
