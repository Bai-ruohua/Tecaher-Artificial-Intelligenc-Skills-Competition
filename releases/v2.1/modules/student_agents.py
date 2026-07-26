# -*- coding: utf-8 -*-
"""
学生端 Agent ① + ②：RAG课程助教 + 刷题判分
"""
import json
import random
from deepseek_client import deepseek
from knowledge_base import CHAPTERS, get_chapter
from rag_engine import rag


# ==================== Agent ①：RAG课程助教 ====================

STUDENT_QA_SYSTEM_PROMPT = """你是{teacher_name}老师的AI课程助教，负责回答学生在{course_name}课程中的问题。

## 你的特点
1. **专业但亲切**：用通俗的语言解释复杂概念，让学生感觉在和真人助教聊天
2. **引用有据**：每个知识点尽量标注来自哪一章节
3. **诚实谨慎**：不知道的不乱编，明确告诉学生"这个问题超出了课程范围，建议向老师咨询"
4. **鼓励思考**：不只是给答案，适当反问引导学生自己思考
5. **案例驱动**：用简单的代码示例帮助理解

## 你的知识范围
- {course_name}课程1-12章全部内容
- Python基础语法、数据结构、函数、面向对象等
- 不涉及课程以外的专业领域深度问题"""


def student_qa(student_id, question, history=None):
    """学生提问，基于RAG检索回答"""
    # RAG检索
    search_results = rag.search(question, top_k=5)
    rag_prompt, sources = rag.generate_rag_prompt(question, search_results)

    # 构造消息
    messages = [
        {"role": "system", "content": rag_prompt or STUDENT_QA_SYSTEM_PROMPT.format(
            teacher_name="朱景峰", course_name="Python程序设计"
        )},
    ]

    if history:
        for h in history[-10:]:
            messages.append(h)

    messages.append({"role": "user", "content": question})

    answer = deepseek.chat_with_history(messages, max_tokens=2048, temperature=0.5)

    # 提取参考来源
    sources_lines = []
    if search_results:
        for r in search_results[:3]:
            sources_lines.append(f"【第{r['chapter_id'].replace('ch', '').lstrip('0')}章】{r['chapter_title']}（相关度：{r['score']}）")

    return {
        "answer": answer,
        "sources": search_results[:5],
        "sources_text": "\n".join(sources_lines) if sources_lines else "课程知识库未精确匹配，以下回答基于AI通用知识，请谨慎参考。",
        "is_from_knowledge_base": len(search_results) > 0 and search_results[0]["score"] > 2,
    }


def get_chapter_qa_guide(chapter_id):
    """获取章节导学问答（课前引导问题）"""
    ch = get_chapter(chapter_id)
    if not ch:
        return []

    questions = [
        f"{ch['title']}主要讲什么内容？请用一句话概括。",
        f"学习{ch['title']}前需要掌握哪些前置知识？",
        f"{ch['title']}有哪些重点需要特别注意？",
    ]

    return questions


# ==================== Agent ②：刷题判分 ====================

QUIZ_GENERATION_PROMPT = """你是Python课程的出题助手。请为以下知识点随机生成{count}道练习题。

## 章节信息
- 章节：{chapter_title}
- 知识点：{key_points}
- 难度：{difficulty_label}

## 题型比例
- 选择题：{choice_count}题
- 填空题：{fill_count}题
- 判断题：{judge_count}题

## 输出格式
请输出一个JSON数组，每道题格式如下：
```json
[
  {{
    "type": "choice",
    "difficulty": "B",
    "question": "题目文本",
    "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
    "answer": "B",
    "explanation": "解析文本"
  }},
  ...
]
```

请确保题目质量高，覆盖核心知识点，解析详细。只输出JSON数组，不要其他文字。"""


def generate_quiz_questions(chapter_id, count=5, difficulty="B"):
    """随机生成练习题"""
    ch = get_chapter(chapter_id)
    if not ch:
        return {"error": "章节不存在", "questions": []}

    difficulty_label = {"A": "基础", "B": "中等", "C": "困难"}.get(difficulty, "中等")
    choice_count = max(2, count * 2 // 3)
    fill_count = max(1, (count - choice_count) // 2)
    judge_count = count - choice_count - fill_count

    prompt = QUIZ_GENERATION_PROMPT.format(
        chapter_title=ch["title"],
        key_points="；".join(ch["key_points"]),
        difficulty_label=difficulty_label,
        count=count,
        choice_count=choice_count,
        fill_count=fill_count,
        judge_count=judge_count,
    )

    try:
        result = deepseek.chat("你是Python课程出题助手，请严格按JSON格式输出。", prompt, max_tokens=3072, temperature=0.7)
        # 尝试解析JSON
        json_str = result.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1]
            json_str = json_str.rsplit("```", 1)[0]
        questions = json.loads(json_str)
        return {"chapter_title": ch["title"], "questions": questions, "count": len(questions)}
    except (json.JSONDecodeError, Exception) as e:
        return {"error": f"题目生成失败: {str(e)}", "questions": [], "raw": result}


def grade_quiz_answer(question, student_answer):
    """判分单个答案"""
    q_type = question.get("type", "choice")
    correct = question.get("answer", "").strip().upper()
    student = student_answer.strip().upper()

    if q_type == "choice":
        # 提取选项字母
        is_correct = (student == correct or (len(student) == 1 and student in "ABCD" and student == correct))
    elif q_type == "judge":
        is_correct = (student == correct)
    else:
        # 填空/简答：模糊匹配
        is_correct = (student == correct) if len(student) < 20 else False

    return is_correct


def get_wrong_book_summary(wrong_book):
    """错题本摘要分析"""
    if not wrong_book:
        return "错题本为空，继续保持！"

    chapters = {}
    for item in wrong_book:
        ch = item.get("chapter_id", "unknown")
        chapters[ch] = chapters.get(ch, 0) + 1

    summary = "## 错题本分析\n\n"
    summary += f"共 {len(wrong_book)} 道错题\n\n"

    # 按章节统计
    for ch, cnt in sorted(chapters.items(), key=lambda x: -x[1]):
        ch_obj = get_chapter(ch)
        title = ch_obj["title"] if ch_obj else ch
        summary += f"- {title}：{cnt}题\n"

    # 弱点分析
    top_weak = max(chapters, key=chapters.get) if chapters else None
    if top_weak:
        ch_obj = get_chapter(top_weak)
        if ch_obj:
            summary += f"\n### 重点加强\n建议重点复习 **{ch_obj['title']}**，这是你的薄弱环节。\n"
            summary += f"知识点：{'、'.join(ch_obj['key_points'][:5])}"

    return summary
