# -*- coding: utf-8 -*-
"""
学生端 / 师生共用 Agent ① + ②：RAG课程助教 + 刷题判分 (V3.0 课程无关化)
所有函数均接受 course_id，检索/出题严格限定在该课程范围内。
"""
import json
import random
from deepseek_client import deepseek
from knowledge_base import get_course_chapter, get_chapter
from rag_engine import get_course_rag


# ==================== Agent ①：RAG课程助教 ====================

def student_qa(student_id, question, history=None, course_id=None, course_name=""):
    """学生/教师提问，基于RAG检索回答（限定在 course_id 课程内）"""
    rag = get_course_rag(course_id, course_name)
    search_results = rag.search(question, top_k=5)
    rag_prompt, sources = rag.generate_rag_prompt(question, search_results)

    messages = []
    if rag_prompt:
        messages.append({"role": "system", "content": rag_prompt})
    else:
        messages.append({"role": "system", "content":
            f"你是《{course_name or '本课程'}》的AI助教，请基于课程资料回答问题；资料不足时建议学生向老师咨询。"})

    if history:
        for h in history[-10:]:
            messages.append(h)

    messages.append({"role": "user", "content": question})

    answer = deepseek.chat_with_history(messages, max_tokens=2048, temperature=0.5)

    sources_lines = []
    if search_results:
        for r in search_results[:3]:
            label = r["chapter_title"]
            sources_lines.append(f"【{label}】（相关度：{r['score']}）")

    return {
        "answer": answer,
        "sources": search_results[:5],
        "sources_text": "\n".join(sources_lines) if sources_lines else "课程知识库未精确匹配，以下回答基于AI通用知识，请谨慎参考。",
        "is_from_knowledge_base": len(search_results) > 0 and search_results[0]["score"] > 2,
    }


def get_chapter_qa_guide(chapter_id, course_id=None):
    """获取章节导学问答（课前引导问题）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return []

    questions = [
        f"{ch['title']}主要讲什么内容？请用一句话概括。",
        f"学习{ch['title']}前需要掌握哪些前置知识？",
        f"{ch['title']}有哪些重点需要特别注意？",
    ]
    return questions


# ==================== Agent ②：刷题判分 ====================

QUIZ_GENERATION_PROMPT = """你是《{course_name}》课程的出题助手。请为以下知识点随机生成{count}道练习题。

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


def generate_quiz_questions(chapter_id, count=5, difficulty="B", course_id=None):
    """随机生成练习题（限定在某课程章节内）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return {"error": "章节不存在", "questions": []}

    course_name = ""
    try:
        from database import get_course_by_id
        c = get_course_by_id(course_id)
        course_name = c["course_name"] if c else ""
    except Exception:
        pass

    key_points = ch.get("key_points", [])
    if isinstance(key_points, str):
        key_points = json.loads(key_points)

    difficulty_label = {"A": "基础", "B": "中等", "C": "困难"}.get(difficulty, "中等")
    choice_count = max(2, count * 2 // 3)
    fill_count = max(1, (count - choice_count) // 2)
    judge_count = count - choice_count - fill_count

    prompt = QUIZ_GENERATION_PROMPT.format(
        course_name=course_name or "本课程",
        chapter_title=ch["title"],
        key_points="；".join(key_points),
        difficulty_label=difficulty_label,
        count=count,
        choice_count=choice_count,
        fill_count=fill_count,
        judge_count=judge_count,
    )

    try:
        result = deepseek.chat("你是课程出题助手，请严格按JSON格式输出。", prompt, max_tokens=3072, temperature=0.7)
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
        is_correct = (student == correct or (len(student) == 1 and student in "ABCD" and student == correct))
    elif q_type == "judge":
        is_correct = (student == correct)
    else:
        is_correct = (student == correct) if len(student) < 20 else False

    return is_correct


def get_wrong_book_summary(wrong_book, course_id=None):
    """错题本摘要分析"""
    if not wrong_book:
        return "错题本为空，继续保持！"

    chapters = {}
    for item in wrong_book:
        ch = item.get("chapter_id", "unknown")
        chapters[ch] = chapters.get(ch, 0) + 1

    summary = "## 错题本分析\n\n"
    summary += f"共 {len(wrong_book)} 道错题\n\n"

    for ch, cnt in sorted(chapters.items(), key=lambda x: -x[1]):
        ch_obj = get_chapter(course_id, ch)
        title = ch_obj["title"] if ch_obj else ch
        summary += f"- {title}：{cnt}题\n"

    top_weak = max(chapters, key=chapters.get) if chapters else None
    if top_weak:
        ch_obj = get_chapter(course_id, top_weak)
        if ch_obj:
            kps = ch_obj.get("key_points", [])
            if isinstance(kps, str):
                kps = json.loads(kps)
            summary += f"\n### 重点加强\n建议重点复习 **{ch_obj['title']}**，这是你的薄弱环节。\n"
            summary += f"知识点：{'、'.join(kps[:5])}"

    return summary
