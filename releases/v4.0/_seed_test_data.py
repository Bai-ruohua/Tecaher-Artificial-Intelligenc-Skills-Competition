# -*- coding: utf-8 -*-
"""
为9大模块生成测试数据 — 一键填充，让首页9卡 + 学情看板 + 学情分析页都有数据展示
模块清单：
  1. 课程管理   → 已有 Python程序设计 (12章)
  2. 学生管理   → 生成10名学生 + 选课
  3. 智能备课   → 生成3份教案
  4. AI智能答疑  → 生成8条问答日志
  5. 智能出题    → 生成15道题目
  6. 数字人讲解  → 生成3个缓存记录
  7. 知识图谱    → 已有12章节点
  8. 代码批改    → 生成8份成绩
  9. 学情看板    → 生成30条答题记录 + 5条错题 + 10条学习日志
"""
import sqlite3, json, os, random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "db", "ai_platform.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 获取第一个课程
    course = c.execute("SELECT id, course_name FROM courses WHERE is_active=1 ORDER BY id LIMIT 1").fetchone()
    if not course:
        print("ERROR: 没有课程，先运行 app.py 初始化")
        return
    course_id = course["id"]
    course_name = course["course_name"]
    print(f"课程: {course_name} (id={course_id})")

    # 获取章节
    chapters = c.execute("SELECT chapter_id, title, module FROM course_chapters WHERE course_id=? ORDER BY seq", (course_id,)).fetchall()
    chapter_ids = [ch["chapter_id"] for ch in chapters]
    print(f"章节: {len(chapters)} 个")

    # 获取教师
    teacher = c.execute("SELECT id FROM teachers WHERE username='admin' LIMIT 1").fetchone()
    teacher_id = teacher["id"] if teacher else 1

    # ===== 2. 学生管理 =====
    print("\n--- 学生管理 ---")
    students_data = [
        ("2025001", "张明轩", "计应2501"),
        ("2025002", "李思琪", "计应2501"),
        ("2025003", "王浩然", "计应2501"),
        ("2025004", "赵雨欣", "计应2501"),
        ("2025005", "刘子涵", "计应2502"),
        ("2025006", "陈宇航", "计应2502"),
        ("2025007", "杨梦瑶", "计应2502"),
        ("2025008", "周天乐", "计应2502"),
        ("2025009", "吴诗涵", "计应2501"),
        ("2025010", "郑凯文", "计应2502"),
    ]
    student_ids = []
    for sno, sname, cls in students_data:
        # 检查是否已存在
        existing = c.execute("SELECT id FROM students WHERE student_no=?", (sno,)).fetchone()
        if existing:
            student_ids.append(existing["id"])
            continue
        c.execute("INSERT INTO students (student_no, student_name, class_name, password_hash, is_active) VALUES (?,?,?,?,1)",
                  (sno, sname, cls, ""))
        sid = c.lastrowid
        # 选课
        try:
            c.execute("INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?,?)", (sid, course_id))
        except Exception:
            pass
        student_ids.append(sid)
    conn.commit()
    print(f"  学生: {len(student_ids)} 名")

    # ===== 3. 智能备课 =====
    print("\n--- 智能备课 ---")
    lesson_count = c.execute("SELECT COUNT(*) FROM lesson_plans WHERE course_id=?", (course_id,)).fetchone()[0]
    if lesson_count == 0:
        lesson_templates = [
            ("ch01", "Python入门与环境搭建", "# 教案：Python入门\n\n## 教学目标\n1. 了解Python语言特点\n2. 掌握环境安装\n3. 编写第一个程序\n\n## 教学重点\n- 解释器与IDE\n- print函数\n- 变量与数据类型\n\n## 教学难点\n- 环境变量配置\n- 编码问题\n\n## 思政融入\n- 国产开源技术精神\n- 编程改变世界案例\n\n## 分层实训\n- 基础：输出Hello World\n- 进阶：计算器小程序\n- 拓展：读取CSV文件"),
            ("ch04", "条件判断与分支结构", "# 教案：条件判断\n\n## 教学目标\n1. 掌握if-elif-else语法\n2. 理解布尔表达式\n3. 能编写分支程序\n\n## 教学重点\n- 比较运算符\n- 逻辑运算符 and/or/not\n- 嵌套分支\n\n## 教学难点\n- 多条件组合逻辑\n- 三元表达式\n\n## 思政融入\n- 人工智能决策伦理\n- 交通信号灯案例\n\n## 分层实训\n- 基础：成绩等级判断\n- 进阶：闰年判断\n- 拓展：BMI计算器"),
            ("ch09", "函数定义与调用", "# 教案：函数\n\n## 教学目标\n1. 掌握def定义函数\n2. 理解参数与返回值\n3. 能模块化编程\n\n## 教学重点\n- 位置参数与关键字参数\n- 默认参数\n- 可变参数 *args/**kwargs\n- return语句\n\n## 教学难点\n- 作用域（局部/全局）\n- 递归\n\n## 思政融入\n- 模块化思维与团队协作\n- 航天工程模块化案例\n\n## 分层实训\n- 基础：温度转换函数\n- 进阶：递归求阶乘\n- 拓展：学生成绩统计函数"),
        ]
        for ch_id, title, content in lesson_templates:
            c.execute("INSERT INTO lesson_plans (chapter_id, chapter_title, content, plan_type, course_id) VALUES (?,?,?,?,?)",
                      (ch_id, title, content, "lesson_plan", course_id))
        conn.commit()
        lesson_count = 3
    print(f"  教案: {lesson_count} 份")

    # ===== 4. AI智能答疑 =====
    print("\n--- AI智能答疑 ---")
    qa_count = c.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0]
    if qa_count == 0:
        qa_pairs = [
            ("student", "什么是Python的列表推导式？", "ch06"),
            ("assistant", "列表推导式是Python中用简洁语法创建列表的方式。基本格式：[表达式 for 变量 in 可迭代对象 if 条件]。例如 [x**2 for x in range(10) if x%2==0] 生成偶数的平方列表。", "ch06"),
            ("student", "for循环和while循环有什么区别？", "ch04"),
            ("assistant", "for循环用于遍历已知序列（列表/字符串/range等），while循环在条件为True时重复执行。for适合确定次数的迭代，while适合不确定次数但有终止条件的场景。", "ch04"),
            ("student", "Python中如何读取CSV文件？", "ch12"),
            ("assistant", "推荐使用csv模块或pandas库。csv模块：import csv; with open('file.csv') as f: reader = csv.reader(f)。pandas：import pandas as pd; df = pd.read_csv('file.csv')。", "ch12"),
            ("student", "什么是面向对象编程？", "ch09"),
            ("assistant", "面向对象编程(OOP)是一种以对象为核心的编程范式。对象包含数据（属性）和行为（方法）。Python中用class定义类，通过类创建对象实例。OOP四大特性：封装、继承、多态、抽象。", "ch09"),
        ]
        for role, content, ch in qa_pairs:
            # 随机关联一个学生
            sid = random.choice(student_ids)
            c.execute("INSERT INTO chat_sessions (student_id, role, content, source_chapter) VALUES (?,?,?,?)",
                      (sid, role, content, ch))
        conn.commit()
        qa_count = len(qa_pairs)
    print(f"  问答: {qa_count} 条")

    # ===== 5. 智能出题 =====
    print("\n--- 智能出题 ---")
    q_count = c.execute("SELECT COUNT(*) FROM questions WHERE course_id=?", (course_id,)).fetchone()[0]
    if q_count == 0:
        questions_data = [
            ("ch01", "choice", "A", "Python是哪种类型的语言？", json.dumps(["编译型", "解释型", "汇编型", "机器语言"]), "Python是解释型语言，代码由解释器逐行执行。"),
            ("ch01", "choice", "C", "以下哪个是合法的变量名？", json.dumps(["2name", "class", "_score", "a-b"]), "Python变量名不能以数字开头，不能是关键字，不能含特殊符号。"),
            ("ch01", "fill", "print", "在Python中输出文本到控制台使用______函数。", None, "print()是Python最基本的输出函数。"),
            ("ch02", "choice", "B", "表达式 10 // 3 的结果是？", json.dumps(["3.33", "3", "4", "3.0"]), "// 是整除运算符，返回商的整数部分。"),
            ("ch02", "choice", "D", "以下哪个不是Python的基本数据类型？", json.dumps(["int", "str", "list", "array"]), "array不是Python内置基本数据类型，需import array模块。"),
            ("ch03", "choice", "B", "字符串 'Hello'[1:3] 的结果是？", json.dumps(["He", "el", "ell", "llo"]), "切片[1:3]从索引1开始到3之前结束，即'el'。"),
            ("ch04", "choice", "C", "if语句中条件为假时执行哪个分支？", json.dumps(["if", "elif", "else", "for"]), "else分支在if条件为False时执行。"),
            ("ch04", "fill", "elif", "多重条件判断使用______关键字连接多个条件。", None, "elif用于if和else之间的多条件分支。"),
            ("ch05", "choice", "A", "for i in range(5)循环执行几次？", json.dumps(["5", "4", "6", "0"]), "range(5)生成0,1,2,3,4共5个数。"),
            ("ch05", "choice", "B", "break语句的作用是？", json.dumps(["跳过本次循环", "跳出整个循环", "继续下一次循环", "终止程序"]), "break立即终止当前循环。"),
            ("ch06", "choice", "D", "以下哪个方法向列表末尾添加元素？", json.dumps(["add()", "insert()", "push()", "append()"]), "append()在列表末尾追加一个元素。"),
            ("ch06", "choice", "A", "列表 [1,2,3] + [4,5] 的结果是？", json.dumps(["[1,2,3,4,5]", "[5,7]", "[1,2,3,[4,5]]", "错误"]), "+ 运算符拼接两个列表。"),
            ("ch09", "choice", "B", "定义函数使用哪个关键字？", json.dumps(["class", "def", "function", "func"]), "def是Python定义函数的关键字。"),
            ("ch09", "fill", "return", "函数中用______语句返回结果。", None, "return语句将值返回给调用者。"),
            ("ch10", "choice", "C", "定义类使用哪个关键字？", json.dumps(["def", "struct", "class", "object"]), "class是Python定义类的关键字。"),
        ]
        for ch_id, q_type, answer, q_text, options, explanation in questions_data:
            c.execute("INSERT INTO questions (chapter_id, q_type, difficulty, question_text, options, answer, explanation, course_id) VALUES (?,?,?,?,?,?,?,?)",
                      (ch_id, q_type, random.choice(["A", "B", "C"]), q_text, options, answer, explanation, course_id))
        conn.commit()
        q_count = len(questions_data)
    print(f"  题目: {q_count} 道")

    # ===== 6. 数字人讲解 =====
    print("\n--- 数字人讲解 ---")
    dh_count = c.execute("SELECT COUNT(*) FROM digital_human_cache").fetchone()[0]
    if dh_count == 0:
        dh_data = [
            ("ch01", "intro", "Python是一种简洁、易学、功能强大的编程语言。它由Guido van Rossum于1989年创建，以代码可读性和简洁语法著称。Python支持多种编程范式，拥有庞大的标准库和第三方生态。", 45.5),
            ("ch04", "if_else", "条件判断是程序控制流的核心。Python使用if-elif-else结构实现分支逻辑。条件表达式求值为True或False，决定执行哪个代码块。", 38.2),
            ("ch09", "function", "函数是可复用的代码块，通过def关键字定义。函数可以接收参数、返回值、被多次调用。良好的函数设计应遵循单一职责原则。", 52.8),
        ]
        for ch_id, topic, text, dur in dh_data:
            c.execute("INSERT INTO digital_human_cache (chapter_id, topic_key, answer_text, audio_path, video_path, tts_duration) VALUES (?,?,?,?,?,?)",
                      (ch_id, topic, text, "", "", dur))
        conn.commit()
        dh_count = len(dh_data)
    print(f"  数字人缓存: {dh_count} 个")

    # ===== 8. 代码批改 / 成绩 =====
    print("\n--- 代码批改 ---")
    grade_count = c.execute("SELECT COUNT(*) FROM grades WHERE course_id=?", (course_id,)).fetchone()[0]
    if grade_count == 0:
        for i, sid in enumerate(student_ids[:8]):
            ch = random.choice(chapter_ids)
            score = random.randint(55, 95)
            feedback = "代码逻辑清晰，变量命名规范。" if score >= 80 else "基本功能实现，但存在边界条件处理不足。" if score >= 70 else "代码有bug，建议检查循环条件和异常处理。"
            c.execute("INSERT INTO grades (student_id, exam_name, chapter_id, question_type, score, max_score, code_content, ai_feedback, course_id) VALUES (?,?,?,?,?,?,?,?,?)",
                      (sid, f"第{i+1}次作业", ch, "code", score, 100, f"# student {sid} code...", feedback, course_id))
        conn.commit()
        grade_count = 8
    print(f"  成绩: {grade_count} 份")

    # ===== 9. 学情看板 =====
    print("\n--- 学情看板（答题记录 + 错题 + 学习日志）---")
    attempt_count = c.execute("SELECT COUNT(*) FROM student_attempts WHERE course_id=?", (course_id,)).fetchone()[0]
    if attempt_count == 0:
        for sid in student_ids:
            # 每个学生 2-5 条答题
            num = random.randint(2, 5)
            for _ in range(num):
                ch = random.choice(chapter_ids)
                is_correct = random.random() > 0.35
                score = random.randint(60, 100) if is_correct else random.randint(20, 59)
                c.execute("INSERT INTO student_attempts (student_id, chapter_id, q_type, question_id, student_answer, is_correct, score, max_score, ai_feedback, course_id, attempt_time) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (sid, ch, "practice", random.randint(1, 15), f"answer_{sid}", 1 if is_correct else 0, score, 100, "", course_id,
                           (datetime.now() - timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        attempt_count = c.execute("SELECT COUNT(*) FROM student_attempts WHERE course_id=?", (course_id,)).fetchone()[0]
    print(f"  答题记录: {attempt_count} 条")

    # 错题本
    wrong_count = c.execute("SELECT COUNT(*) FROM wrong_books").fetchone()[0]
    if wrong_count == 0:
        for sid in student_ids[:5]:
            ch = random.choice(chapter_ids)
            c.execute("INSERT INTO wrong_books (student_id, chapter_id, question_id, question_text, wrong_answer, correct_answer, explanation, review_count) VALUES (?,?,?,?,?,?,?,?)",
                      (sid, ch, random.randint(1, 15), "以下哪个不是Python基本数据类型？", "list", "array", "array需要import array模块，不是内置基本类型。", 0))
        conn.commit()
        wrong_count = 5
    print(f"  错题: {wrong_count} 条")

    # 学习日志
    log_count = c.execute("SELECT COUNT(*) FROM learning_logs").fetchone()[0]
    if log_count == 0:
        actions = [("study", 1800), ("practice", 600), ("qa_ask", 120), ("review", 900)]
        for sid in student_ids:
            for act, dur in random.sample(actions, k=random.randint(2, 4)):
                ch = random.choice(chapter_ids)
                c.execute("INSERT INTO learning_logs (student_id, action_type, chapter_id, detail, duration_seconds, created_at) VALUES (?,?,?,?,?,?)",
                          (sid, act, ch, f"{act} on {ch}", dur, (datetime.now() - timedelta(days=random.randint(0, 7))).strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        log_count = c.execute("SELECT COUNT(*) FROM learning_logs").fetchone()[0]
    print(f"  学习日志: {log_count} 条")

    conn.close()
    print("\n===== 测试数据生成完毕 =====")
    print(f"课程: {course_name} | 学生: {len(student_ids)} | 教案: {lesson_count} | 问答: {qa_count} | 题目: {q_count} | 数字人: {dh_count} | 成绩: {grade_count} | 答题: {attempt_count} | 错题: {wrong_count} | 学习日志: {log_count}")


if __name__ == "__main__":
    main()
