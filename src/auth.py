# -*- coding: utf-8 -*-
"""
认证模块 V2.1
功能：统一登录 / Session管理 / 角色鉴权 / 密码哈希 / 批量建号
"""
import hashlib
import secrets
import functools
from datetime import datetime
from flask import session, redirect, url_for, jsonify, request

from database import (
    get_teacher_by_username, get_student_by_username,
    create_session, get_session, delete_session,
    create_teacher, get_all_teachers,
    create_course, get_courses_by_teacher,
    batch_create_students, get_students_by_teacher,
    enroll_student, get_student_by_id, get_teacher_by_id,
)


# ===== 密码哈希 =====

def hash_password(password: str) -> str:
    """SHA-256 + 随机salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, hashed = stored_hash.split("$", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == hashed


# ===== Session管理 =====

def make_session_token() -> str:
    return secrets.token_urlsafe(32)


def login_user(user_id: int, user_role: str, username: str, name: str):
    """登录成功后创建session，写入flask session和数据库"""
    token = make_session_token()
    ip = request.remote_addr or ""
    create_session(token, user_id, user_role, ip, expires_hours=48)

    session["token"] = token
    session["user_id"] = user_id
    session["user_role"] = user_role
    session["username"] = username
    session["display_name"] = name
    return token


def logout_user():
    """登出：清除session"""
    token = session.pop("token", None)
    if token:
        delete_session(token)
    session.clear()


def get_current_user():
    """获取当前登录用户信息，未登录返回None"""
    token = session.get("token")
    if not token:
        return None
    db_session = get_session(token)
    if not db_session:
        session.clear()
        return None
    return {
        "user_id": db_session["user_id"],
        "user_role": db_session["user_role"],
        "username": session.get("username", ""),
        "display_name": session.get("display_name", ""),
    }


# ===== 鉴权装饰器 =====

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "请先登录"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "请先登录"}), 401
            return redirect(url_for("login_page"))
        if user["user_role"] != "teacher":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "无权访问"}), 403
            return redirect(url_for("student_dashboard_page"))
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "请先登录"}), 401
            return redirect(url_for("login_page"))
        if user["user_role"] != "student":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "无权访问"}), 403
            return redirect(url_for("teacher_dashboard_page"))
        return f(*args, **kwargs)
    return decorated


# ===== 登录/注册逻辑 =====

def do_login(username: str, password: str, role: str = "auto"):
    """统一登录入口
    role: 'teacher' / 'student' / 'auto'（自动判断）
    返回: (success: bool, user_info: dict, error: str)
    """
    username = username.strip()

    # 尝试教师登录
    if role in ("teacher", "auto"):
        teacher = get_teacher_by_username(username)
        if teacher and verify_password(password, teacher.get("password_hash", "")):
            login_user(teacher["id"], "teacher", teacher["username"], teacher["teacher_name"])
            return True, {
                "role": "teacher",
                "user_id": teacher["id"],
                "name": teacher["teacher_name"],
                "redirect": "/teacher/dashboard",
            }, ""

    # 尝试学生登录
    if role in ("student", "auto"):
        student = get_student_by_username(username)
        if student and verify_password(password, student.get("password_hash", "")):
            login_user(student["id"], "student", student["student_no"], student["student_name"])
            return True, {
                "role": "student",
                "user_id": student["id"],
                "name": student["student_name"],
                "redirect": "/student/dashboard",
            }, ""

    return False, {}, "用户名或密码错误"


# ===== 初始化默认教师账号 =====

def init_default_teacher():
    """首次运行时创建默认教师账号"""
    teachers = get_all_teachers()
    if not teachers:
        create_teacher(
            username="admin",
            password_hash=hash_password("admin123"),
            teacher_name="管理员教师",
            title="系统管理员",
        )


# ===== 当前课程上下文（V3.0 课程即租户）=====

def get_current_course_id(user=None):
    """返回当前会话选中的课程 id；未选中则返回首个可访问课程"""
    from database import get_first_course_id, get_courses_by_teacher, get_student_courses
    cid = session.get("current_course_id")
    if cid:
        # 校验访问权限
        if user:
            ok = False
            if user["user_role"] == "teacher":
                ok = any(c["id"] == cid for c in get_courses_by_teacher(user["user_id"]))
            else:
                ok = any(c["id"] == cid for c in get_student_courses(user["user_id"]))
            if not ok:
                cid = None
        if cid:
            return cid
    return get_first_course_id()


def set_current_course(course_id):
    """设置当前课程（校验访问权限）"""
    user = get_current_user()
    if not user or not course_id:
        return False
    from database import get_courses_by_teacher, get_student_courses
    if user["user_role"] == "teacher":
        owned = any(c["id"] == course_id for c in get_courses_by_teacher(user["user_id"]))
    else:
        owned = any(c["id"] == course_id for c in get_student_courses(user["user_id"]))
    if not owned:
        return False
    session["current_course_id"] = course_id
    return True


def seed_default_courses():
    """首次运行时为默认教师创建示例课程(Python) 并写入12章种子数据"""
    from database import get_courses_by_teacher, create_course
    from knowledge_base import seed_course_template
    teachers = get_all_teachers()
    if not teachers:
        return
    admin = teachers[0]
    if get_courses_by_teacher(admin["id"]):
        return
    cid = create_course(admin["id"], "Python程序设计", "2026春季", "示例课程：Python编程基础（12章）")
    seed_course_template(cid, "Python程序设计")
    return cid


# ===== 课程管理逻辑 =====

def handle_create_course(teacher_id, course_name, semester="", description="", textbook=""):
    cid = create_course(teacher_id, course_name, semester, description, textbook)
    return cid


def handle_get_teacher_courses(teacher_id):
    return get_courses_by_teacher(teacher_id)


def handle_delete_course(teacher_id, course_id):
    """删除课程（含权限校验 + 级联删除）"""
    from database import delete_course
    return delete_course(course_id, teacher_id=teacher_id)


# ===== 批量创建学生账号 =====

def handle_batch_create_students(teacher_id, course_id, student_data_list, default_password="123456"):
    """
    批量创建学生账号并选课
    student_data_list: [{"student_no": "...", "student_name": "...", "class_name": "..."}]
    可选自定义密码，否则使用默认密码
    """
    pwd_hash = hash_password(default_password)
    prepared = []
    for s in student_data_list:
        prepared.append({
            "student_no": s.get("student_no", "").strip(),
            "student_name": s.get("student_name", "").strip(),
            "class_name": s.get("class_name", "").strip(),
            "password_hash": pwd_hash,
        })

    # 过滤无效数据
    prepared = [s for s in prepared if s["student_no"] and s["student_name"]]

    if not prepared:
        return {"success": [], "failed": [], "error": "没有有效的学生数据"}

    results = batch_create_students(prepared, course_id)
    return results


def handle_batch_generate_students(teacher_id, course_id, prefix, count, class_name="", default_password="123456"):
    """
    自动批量生成学生账号
    prefix: 学号前缀（如 "2024001"），自动补序号
    count: 生成数量
    """
    pwd_hash = hash_password(default_password)
    prepared = []
    for i in range(1, count + 1):
        student_no = f"{prefix}{i:03d}"
        prepared.append({
            "student_no": student_no,
            "student_name": f"学生{student_no}",
            "class_name": class_name,
            "password_hash": pwd_hash,
        })

    results = batch_create_students(prepared, course_id)
    return results
