# -*- coding: utf-8 -*-
"""
AI学情分析模块
班级趋势 / 风险预警 / 知识点掌握度 / 完整报告
"""
from deepseek_client import deepseek

TREND_PROMPT = """你是教育数据分析专家。请分析以下成绩数据，给出班级学习趋势。

## 成绩数据
{grades_text}

## 分析要求
1. **整体趋势**：班级平均分、及格率的变化趋势
2. **分层分析**：优秀（≥85）、良好（70-84）、及格（60-69）、不及格（<60）各层次的人数变化
3. **突出问题**：哪些学生持续退步，哪些知识点是普遍薄弱点
4. **教学建议**：基于数据给出具体的教学调整建议

请输出结构化的分析报告。"""

RISK_PROMPT = """你是学生学业风险预警专家。请识别以下学生中的高风险个体。

## 成绩数据
{grades_text}

## 预警标准
- 🔴 高风险：连续2次以上不及格（<60分）或成绩持续下降趋势明显
- 🟡 中风险：最近一次不及格或成绩有下降趋势
- 🟢 低风险：成绩稳定或上升

## 输出要求
为每位预警学生输出：
1. 姓名/学号
2. 风险等级
3. 成绩变化趋势
4. 可能存在的原因
5. 建议的干预措施"""

CHAPTER_MASTERY_PROMPT = """你是教育专家。请分析学生对各知识点的掌握情况。

## 按章节的答题数据
{chapter_data}

## 输出要求
1. 每个章节的掌握度（0-100%）
2. 薄弱知识点排名
3. 班级共性问题
4. 教学重点调整建议"""

REPORT_PROMPT = """你是教育数据分析专家。请基于以下数据生成一份完整的学情分析报告。

## 基本信息
- 班级：{class_name}
- 课程：Python程序设计
- 分析时间：当前

## 数据
{grades_text}

## 报告结构

### 一、总体概况
（班级人数、平均分、及格率、优秀率、标准差等统计指标）

### 二、成绩分布
（按分数段分布统计和解读）

### 三、趋势分析
（如果有多次考试数据，分析成绩变化趋势）

### 四、风险学生识别
（标注需要重点关注的学生名单）

### 五、知识点掌握分析
（各知识点的班级整体掌握情况）

### 六、教学建议
（基于数据的教学改进建议，包括教学方法、内容节奏、辅导策略等）

### 七、总结
（一句话概括班级学情）

请确保数据解读准确，建议具体可操作。"""


def analyze_class_trend(grades):
    """班级趋势分析"""
    if not grades:
        return {"error": "没有成绩数据", "summary": "请先导入成绩数据"}

    grades_text = _format_grades(grades)
    prompt = TREND_PROMPT.format(grades_text=grades_text[:5000])

    ai_analysis = None
    try:
        ai_analysis = deepseek.chat("你是教育数据分析专家。", prompt, max_tokens=3072)
    except Exception:
        pass

    # 基本统计
    scores = [g.get("score", 0) for g in grades]
    avg = sum(scores) / len(scores) if scores else 0
    passed = sum(1 for s in scores if s >= 60)
    excellent = sum(1 for s in scores if s >= 85)

    return {
        "count": len(scores),
        "avg_score": round(avg, 1),
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "pass_rate": round(passed / len(scores) * 100, 1) if scores else 0,
        "excellent_rate": round(excellent / len(scores) * 100, 1) if scores else 0,
        "ai_analysis": ai_analysis,
    }


def detect_risk_students(grades, threshold=60):
    """风险预警"""
    if not grades:
        return {"risk_students": [], "summary": "没有成绩数据"}

    grades_text = _format_grades(grades)
    prompt = RISK_PROMPT.format(grades_text=grades_text[:5000])

    ai_analysis = None
    try:
        ai_analysis = deepseek.chat("你是学生学业风险预警专家。", prompt, max_tokens=3072)
    except Exception:
        pass

    # 基础风险检测
    risk_students = []
    student_grades = {}
    for g in grades:
        name = f"{g.get('student_name', '')}({g.get('student_no', '')})"
        if name not in student_grades:
            student_grades[name] = []
        student_grades[name].append(g.get("score", 0))

    for name, scores in student_grades.items():
        avg_s = sum(scores) / len(scores)
        if avg_s < threshold:
            level = "🔴 高风险" if avg_s < 50 else "🟡 中风险"
            risk_students.append({
                "student": name,
                "avg_score": round(avg_s, 1),
                "exam_count": len(scores),
                "risk_level": level,
            })

    risk_students.sort(key=lambda x: x["avg_score"])
    return {"risk_students": risk_students, "ai_analysis": ai_analysis}


def analyze_chapter_mastery(grades):
    """知识点掌握度分析"""
    if not grades:
        return {"mastery": [], "weak_chapters": [], "ai_analysis": None}

    chapter_data = _format_chapter_grades(grades)
    prompt = CHAPTER_MASTERY_PROMPT.format(chapter_data=chapter_data[:4000])

    ai_analysis = None
    try:
        ai_analysis = deepseek.chat("你是教育数据分析专家。", prompt, max_tokens=3072)
    except Exception:
        pass

    # 基础掌握度计算
    chapter_scores = {}
    for g in grades:
        ch = g.get("chapter_id", "unknown")
        if ch not in chapter_scores:
            chapter_scores[ch] = []
        chapter_scores[ch].append(g.get("score", 0))

    mastery = []
    for ch, scores in chapter_scores.items():
        avg = sum(scores) / len(scores)
        mastery.append({"chapter_id": ch, "avg_score": round(avg, 1), "count": len(scores)})

    mastery.sort(key=lambda x: x["avg_score"])
    weak_chapters = [m for m in mastery if m["avg_score"] < 60]

    return {"mastery": mastery, "weak_chapters": weak_chapters, "ai_analysis": ai_analysis}


def generate_full_report(grades, class_name=""):
    """生成完整学情报告"""
    if not grades:
        return {"error": "没有成绩数据", "report": "请先导入成绩数据"}

    grades_text = _format_grades(grades)
    prompt = REPORT_PROMPT.format(
        class_name=class_name or "全体学生",
        grades_text=grades_text[:5000]
    )

    report = deepseek.reasoner("你是教育数据分析专家。", prompt, max_tokens=8192)

    return {
        "class_name": class_name,
        "total_students": len(set(g.get("student_no", "") for g in grades)),
        "report": report,
    }


def _format_grades(grades):
    """格式化成绩数据"""
    lines = []
    current_student = None
    for g in grades:
        name = g.get("student_name", "未知")
        no = g.get("student_no", "未知")
        ch = g.get("chapter_id", "")
        exam = g.get("exam_name", "")
        score = g.get("score", 0)
        student_label = f"{name}({no})"
        if student_label != current_student:
            current_student = student_label
            lines.append(f"\n## {student_label}")
        lines.append(f"- {exam or ch}: {score}分")
    return "\n".join(lines)


def _format_chapter_grades(grades):
    """按章节分组格式化"""
    from collections import defaultdict
    chapters = defaultdict(list)
    for g in grades:
        ch = g.get("chapter_id", "unknown")
        chapters[ch].append(g.get("score", 0))

    lines = []
    for ch, scores in sorted(chapters.items()):
        avg = sum(scores) / len(scores)
        lines.append(f"{ch}: 平均{avg:.1f}分 (共{len(scores)}人次)")
    return "\n".join(lines)
