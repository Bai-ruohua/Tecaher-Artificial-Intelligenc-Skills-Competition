# -*- coding: utf-8 -*-
"""
AI批改助手模块
代码评分 / Bug诊断 / 批量批改 / 代码相似度检测
"""
import hashlib
from deepseek_client import deepseek
from knowledge_base import get_course_chapter

GRADING_PROMPT = """你是Python课程的代码评阅专家。请对学生提交的代码进行评分和点评。

## 题目说明
{task_description}

## 章节知识点
{chapter_knowledge}

## 评分标准（满分100分）
- **正确性（40分）**：代码逻辑正确，能实现题目要求的功能
- **规范性（20分）**：命名规范、缩进正确、有适当注释
- **效率性（20分）**：算法选择合理，时间复杂度合理
- **创新性（20分）**：有独到的解题思路或使用了高级技巧

## 学生代码
```python
{code}
```

## 评分要求
请按以下格式输出评分结果：

### 评分明细
| 维度 | 得分 | 满分 | 理由 |
|------|------|------|------|
| 正确性 | | 40 | |
| 规范性 | | 20 | |
| 效率性 | | 20 | |
| 创新性 | | 20 | |
| **总分** | | **100** | |

### 优点
- （学生做得好的地方）

### 改进建议
- （具體的修改建议）

### 参考代码/思路
```python
（给出更优的解法或关键提示）
```"""

DIAGNOSE_PROMPT = """你是Python课程的Bug诊断专家。请诊断以下代码中的错误。

## 学生代码
```python
{code}
```

## 错误信息
{error_message}

## 诊断要求
1. **错误定位**：精确到第几行，说明是什么类型的错误
2. **原因分析**：用通俗语言解释为什么会出错
3. **修正方案**：给出修正后的代码
4. **预防建议**：告诉学生如何避免类似错误

请按以下格式输出：
### 错误定位与类型
### 原因分析
### 修正代码
### 预防建议"""

BATCH_GRADING_PROMPT = """你是Python课程的批量批改助手。请批改以下{count}份学生代码。

## 题目说明
{task_description}

## 评分标准
正确性(40分) + 规范性(20分) + 效率性(20分) + 创新性(20分) = 满分100分

## 学生提交
{submissions}

请为每份代码输出评分明细（得分和简短点评），最后输出一份成绩汇总表。"""


def grade_code(code, task_description, chapter_id=None, course_id=None):
    """单份代码评分"""
    if not code.strip():
        return "### 评分结果\n**得分：0分** — 未提交代码或代码为空。"

    chapter_knowledge = ""
    if chapter_id:
        ch = get_course_chapter(course_id, chapter_id)
        if ch:
            chapter_knowledge = f"{ch['title']}：{'；'.join(ch['key_points'])}"

    prompt = GRADING_PROMPT.format(
        task_description=task_description,
        chapter_knowledge=chapter_knowledge,
        code=code[:3000]
    )

    return deepseek.chat("你是课程代码评阅专家，擅长客观公正地评估学生代码。", prompt, max_tokens=2048)


def diagnose_bug(code, error_message, chapter_id=None):
    """Bug诊断"""
    if not code.strip():
        return "### 诊断结果\n代码为空，请提供需要诊断的代码。"

    prompt = DIAGNOSE_PROMPT.format(
        code=code[:3000],
        error_message=error_message or "（未提供错误信息，请根据代码本身进行分析）"
    )

    return deepseek.chat("你是Python调试专家，擅长帮助学生定位和理解代码错误。", prompt, max_tokens=2048)


def batch_grade(submissions, task_description):
    """批量评分"""
    if not submissions:
        return "没有提交需要批改。"

    submission_text = ""
    for i, sub in enumerate(submissions, 1):
        name = sub.get("name", f"匿名{i}")
        code = sub.get("code", "")
        submission_text += f"\n### 学生{i}：{name}\n```python\n{code[:500]}\n```\n"

    prompt = BATCH_GRADING_PROMPT.format(
        count=len(submissions),
        task_description=task_description,
        submissions=submission_text[:5000]
    )

    return deepseek.chat("你是高效的批量代码评审专家。", prompt, max_tokens=4096)


def check_similarity(code_list):
    """代码相似度检测（基于结构哈希）"""
    if len(code_list) < 2:
        return {"matrix": [], "suspicious": []}

    def normalize(code):
        """代码归一化（去除空白和注释）"""
        lines = [l.strip() for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]
        return "\n".join(lines)

    def hash_code(code):
        """结构哈希"""
        return hashlib.md5(code.encode("utf-8")).hexdigest()[:8]

    n = len(code_list)
    matrix = [[0.0] * n for _ in range(n)]
    suspicious = []
    hashes = [hash_code(normalize(c)) for c in code_list]

    for i in range(n):
        for j in range(i + 1, n):
            ci = normalize(code_list[i])
            cj = normalize(code_list[j])

            # 完全相同
            if ci == cj:
                matrix[i][j] = matrix[j][i] = 1.0
                suspicious.append({"i": i, "j": j, "similarity": 1.0, "level": "高度相似（完全相同）"})
            # 结构哈希相同
            elif hashes[i] == hashes[j]:
                sim = 0.95
                matrix[i][j] = matrix[j][i] = sim
                suspicious.append({"i": i, "j": j, "similarity": sim, "level": "高度相似（结构相同）"})
            else:
                # 行级相似度
                lines_i = set(ci.split("\n"))
                lines_j = set(cj.split("\n"))
                if lines_i and lines_j:
                    intersection = lines_i & lines_j
                    union = lines_i | lines_j
                    sim = len(intersection) / len(union)
                    matrix[i][j] = matrix[j][i] = round(sim, 2)
                    if sim > 0.7:
                        level = "中度相似" if sim < 0.85 else "高度相似"
                        suspicious.append({"i": i, "j": j, "similarity": round(sim, 2), "level": level})

    suspicious.sort(key=lambda x: x["similarity"], reverse=True)
    return {"matrix": matrix, "suspicious": suspicious}
