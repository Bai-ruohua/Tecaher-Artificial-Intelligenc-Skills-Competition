# -*- coding: utf-8 -*-
"""
AI命题助手模块
自动出题（5种题型）/ 难度控制 / 答案生成 / 组卷
"""
import json
from knowledge_base import get_course_chapter
from deepseek_client import deepseek


def _course_name(course_id):
    try:
        from database import get_course_by_id
        c = get_course_by_id(course_id)
        return c["course_name"] if c else "本课程"
    except Exception:
        return "本课程"

QTYPE_TEMPLATES = {
    "choice": {
        "name": "选择题",
        "format": """
### {n}. 【{difficulty_label}】
**题目**：{stem}
A. {opt_a}
B. {opt_b}
C. {opt_c}
D. {opt_d}
**正确答案**：{answer}
**解析**：{explanation}
"""
    },
    "fill": {
        "name": "填空题",
        "format": """
### {n}. 【{difficulty_label}】
**题目**：{stem}
**正确答案**：{answer}
**解析**：{explanation}
"""
    },
    "judge": {
        "name": "判断题",
        "format": """
### {n}. 【{difficulty_label}】
**题目**：{stem}
A. 正确
B. 错误
**正确答案**：{answer}
**解析**：{explanation}
"""
    },
    "programming": {
        "name": "编程题",
        "format": """
### {n}. 【{difficulty_label}】
**题目描述**：{stem}
**输入示例**：{input_example}
**输出示例**：{output_example}
**参考答案**：
```python
{reference_code}
```
**评分标准**：{scoring_rubric}
**解析**：{explanation}
"""
    },
    "short_answer": {
        "name": "简答题",
        "format": """
### {n}. 【{difficulty_label}】
**题目**：{stem}
**参考答案要点**：{answer}
**解析**：{explanation}
"""
    },
}

DIFFICULTY_MAP = {"A": "基础", "B": "中等", "C": "困难"}

QUESTION_PROMPT = """你是{course_name}课程的命题专家。请为以下知识点出题。

## 章节信息
- 章节：{chapter_title}
- 知识点：{key_points}

## 出题要求
1. 题型：{qtype_name}
2. 数量：{count}题
3. 难度：{difficulty}（{difficulty_label}）
4. 每道题必须包含：
   - 题干（清晰准确）
   - 正确答案
   - 详细解析（说明为什么选这个答案，常见错误选项的原因）
5. 选择题必须有4个选项（A/B/C/D），非明显错误选项要有迷惑性
6. 编程题必须包含：题目描述、输入输出示例、参考代码、评分标准
7. 判断题必须给出正误的判断依据

## 输出格式
{format_spec}

请确保题目覆盖本章节的核心知识点，难度符合要求，解析详细有教学价值。"""

MIXED_PAPER_PROMPT = """你是{course_name}课程的命题负责人。请生成一份完整的考试试卷。

## 试卷配置
- 考试范围：{chapter_info}
- 满分：100分
- 考试时间：90分钟

## 题型与分值
- 单选题：{choice_count}题 × {choice_score}分 = {choice_total}分
- 填空题：{fill_count}题 × {fill_score}分 = {fill_total}分
- 判断题：{judge_count}题 × {judge_score}分 = {judge_total}分
- 编程题：{prog_count}题 × {prog_score}分 = {prog_total}分
- 简答题：{short_count}题 × {short_score}分 = {short_total}分

## 输出要求
1. 试卷结构：先输出试卷头（课程名、考试时间、满分），再按题型逐一输出
2. 每道题标注分值
3. 最后单独一页输出参考答案和评分标准
4. 难度分布：基础60% + 中等30% + 困难10%
5. 编程题需要包含输入输出示例和分步评分细则

请按照标准试卷格式输出完整试卷。"""


def generate_questions(chapter_id, q_type="choice", count=5, difficulty="B", course_id=None):
    """生成题目（course_id 限定章节范围）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return "章节不存在"

    qtype_info = QTYPE_TEMPLATES.get(q_type, QTYPE_TEMPLATES["choice"])
    difficulty_label = DIFFICULTY_MAP.get(difficulty, "中等")
    cname = _course_name(course_id)

    prompt = QUESTION_PROMPT.format(
        course_name=cname,
        chapter_title=ch["title"],
        key_points="；".join(ch["key_points"]),
        qtype_name=qtype_info["name"],
        count=count,
        difficulty=difficulty,
        difficulty_label=difficulty_label,
        format_spec=qtype_info["format"],
    )

    return deepseek.chat(f"你是{cname}课程命题专家，擅长根据知识点出高质量的题目。", prompt, max_tokens=4096)


def generate_mixed_paper(chapter_id, config=None, course_id=None):
    """生成完整试卷（course_id 限定章节范围）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return "章节不存在"

    if config is None:
        config = {
            "choice": {"count": 10, "score": 3},
            "fill": {"count": 5, "score": 4},
            "judge": {"count": 5, "score": 2},
            "programming": {"count": 2, "score": 15},
            "short_answer": {"count": 2, "score": 10},
        }

    prompt = MIXED_PAPER_PROMPT.format(
        course_name=_course_name(course_id),
        chapter_info=ch["title"],
        choice_count=config["choice"]["count"],
        choice_score=config["choice"]["score"],
        choice_total=config["choice"]["count"] * config["choice"]["score"],
        fill_count=config["fill"]["count"],
        fill_score=config["fill"]["score"],
        fill_total=config["fill"]["count"] * config["fill"]["score"],
        judge_count=config["judge"]["count"],
        judge_score=config["judge"]["score"],
        judge_total=config["judge"]["count"] * config["judge"]["score"],
        prog_count=config["programming"]["count"],
        prog_score=config["programming"]["score"],
        prog_total=config["programming"]["count"] * config["programming"]["score"],
        short_count=config["short_answer"]["count"],
        short_score=config["short_answer"]["score"],
        short_total=config["short_answer"]["count"] * config["short_answer"]["score"],
    )

    return deepseek.reasoner("你是高职课程考试命题负责人，擅长设计科学合理的试卷。", prompt, max_tokens=8192)
