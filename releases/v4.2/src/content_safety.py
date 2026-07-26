# -*- coding: utf-8 -*-
"""
内容安全校验模块
- AI 生成内容标注
- 敏感词过滤
- 学科边界提示
"""
import re

# 基础敏感词列表（教育场景）
SENSITIVE_WORDS = [
    # 政治敏感
    "习近平", "李克强", "共产党", "国民党", "法轮功", "六四", "天安门",
    # 违法违规
    "作弊", "代考", "代写论文", "代写作业", "抄袭",
    # 不良内容
    "色情", "赌博", "毒品", "暴力",
    # 教育红线
    "保证通过", "包过", "保过", "100%通过",
]

# AI 生成标签
AI_GENERATED_TAG = '<span class="ai-tag">AI生成，仅供教师参考调整</span>'
AI_STUDENT_TAG = '<span class="ai-tag">AI辅助回答，请以教材和教师讲解为准</span>'


def check_sensitive(text):
    """
    检查文本是否包含敏感词
    返回 (is_safe: bool, matched_words: list)
    """
    if not text:
        return True, []
    matched = []
    for word in SENSITIVE_WORDS:
        if word in text:
            matched.append(word)
    return len(matched) == 0, matched


def filter_sensitive(text, replacement="***"):
    """
    替换文本中的敏感词
    """
    if not text:
        return text
    result = text
    for word in SENSITIVE_WORDS:
        if word in result:
            result = result.replace(word, replacement)
    return result


def add_ai_tag(content, role="teacher"):
    """
    给 AI 生成内容添加标签
    """
    tag = AI_GENERATED_TAG if role == "teacher" else AI_STUDENT_TAG
    return f'{content}\n{tag}'


def check_academic_boundary(question, course_name=""):
    """
    检查问题是否在课程学科范围内
    返回 (in_boundary: bool, suggestion: str)
    """
    if not course_name:
        return True, ""

    # 简单关键词匹配：如果问题包含课程名称相关关键词，判定为在范围内
    course_keywords = set()
    for char in course_name:
        if char.isalpha():
            course_keywords.add(char)

    # 如果课程是"Python程序设计"，"Python"作为判断关键词
    if "python" in question.lower() or "程序" in question or "编程" in question:
        return True, ""

    # 如果问题明显超出课程范围，给出提示
    out_of_scope_indicators = ["历史", "地理", "生物", "化学", "物理", "英语", "数学"]
    for indicator in out_of_scope_indicators:
        if indicator in question and "Python" not in course_name and "程序" not in course_name:
            return False, f"当前课程为「{course_name}」，该问题超出课程范围，建议咨询相关课程教师。"

    return True, ""
