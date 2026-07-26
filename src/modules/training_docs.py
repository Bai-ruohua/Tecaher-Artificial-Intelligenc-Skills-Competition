# -*- coding: utf-8 -*-
"""
实训资料整理模块
- 实训报告模板生成
- 实训成绩汇总
- 实训资料目录生成
"""
import json
import os
import sys

_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _src not in sys.path:
    sys.path.insert(0, _src)

from deepseek_client import deepseek


def generate_report_template(course_name, chapter_title, student_name, requirements=""):
    """生成实训报告模板"""
    system = "你是一位高职实训指导教师，擅长设计实训报告模板。注重实践性、规范性。"
    user = f"请为以下实训生成一份报告模板（含报告标题、实训目的、实训环境、实训步骤、实训结果、实训总结等部分）：\n课程：{course_name}\n章节：{chapter_title}\n学生：{student_name}\n要求：{requirements or '标准实训报告'}"
    try:
        result = deepseek.chat(system, user)
        return {"success": True, "content": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_summary(student_data):
    """生成实训成绩汇总"""
    # student_data: list of {name, project, score, grade}
    if not student_data:
        return {"success": False, "error": "无数据"}
    total = len(student_data)
    avg_score = sum(s.get("score", 0) for s in student_data) / total
    passed = sum(1 for s in student_data if s.get("score", 0) >= 60)
    failed = total - passed
    
    rows = ""
    for s in student_data:
        rows += f"{s.get('name','')} | {s.get('project','')} | {s.get('score',0)} | {s.get('grade','')}\n"
    
    summary = f"""## 实训成绩汇总表

| 姓名 | 实训项目 | 成绩 | 等级 |
|------|---------|:----:|:----:|
{rows}

**统计信息**
- 总人数：{total}
- 平均分：{avg_score:.1f}
- 及格人数：{passed}
- 不及格人数：{failed}
- 及格率：{passed/total*100:.1f}%
"""
    return {"success": True, "content": summary, "stats": {
        "total": total, "avg_score": round(avg_score, 1),
        "passed": passed, "failed": failed,
        "pass_rate": round(passed/total*100, 1),
    }}


def organize_directory(files):
    """生成实训资料目录清单"""
    if not files:
        return {"success": False, "error": "无文件"}
    lines = []
    for i, f in enumerate(files, 1):
        lines.append(f"{i}. {f['name']} - {f.get('desc', '')} ({f.get('size', '')})")
    content = "## 实训资料目录\n\n" + "\n".join(lines)
    return {"success": True, "content": content}


# 示例数据
DEMO_GRADES = [
    {"name": "张明轩", "project": "Python数据分析实训", "score": 92, "grade": "优秀"},
    {"name": "李思琪", "project": "Python数据分析实训", "score": 88, "grade": "良好"},
    {"name": "王浩然", "project": "Python数据分析实训", "score": 75, "grade": "中等"},
    {"name": "陈雅文", "project": "Python数据分析实训", "score": 63, "grade": "及格"},
    {"name": "刘子轩", "project": "Python数据分析实训", "score": 45, "grade": "不及格"},
    {"name": "赵雪婷", "project": "Python数据分析实训", "score": 95, "grade": "优秀"},
    {"name": "周子涵", "project": "Python数据分析实训", "score": 82, "grade": "良好"},
    {"name": "吴俊豪", "project": "Python数据分析实训", "score": 70, "grade": "中等"},
    {"name": "郑雨桐", "project": "Python数据分析实训", "score": 58, "grade": "不及格"},
    {"name": "孙浩宇", "project": "Python数据分析实训", "score": 78, "grade": "中等"},
]

DEMO_FILES = [
    {"name": "实训报告_张明轩.docx", "desc": "数据分析完整报告", "size": "2.3 MB"},
    {"name": "实训报告_李思琪.docx", "desc": "数据分析完整报告", "size": "1.8 MB"},
    {"name": "实训报告_王浩然.docx", "desc": "数据分析完整报告", "size": "2.1 MB"},
    {"name": "源代码_张明轩.zip", "desc": "Python源码与数据", "size": "456 KB"},
    {"name": "源代码_李思琪.zip", "desc": "Python源码与数据", "size": "389 KB"},
    {"name": "实训照片_第一组", "desc": "实训过程照片", "size": "12.5 MB"},
    {"name": "实训照片_第二组", "desc": "实训过程照片", "size": "15.2 MB"},
    {"name": "评分表.xlsx", "desc": "实训评分汇总表", "size": "68 KB"},
]
