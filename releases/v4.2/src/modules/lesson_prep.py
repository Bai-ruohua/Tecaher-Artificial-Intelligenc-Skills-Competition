# -*- coding: utf-8 -*-
"""
AI备课助手模块
教案生成 / 课件大纲 / 思政融入 / 分层实训设计
"""
from knowledge_base import get_course_chapter
from deepseek_client import deepseek
from modules.prompt_cache import get_cache, set_cache
import hashlib


def _course_name(course_id):
    try:
        from database import get_course_by_id
        c = get_course_by_id(course_id)
        return c["course_name"] if c else "本课程"
    except Exception:
        return "本课程"

LESSON_PLAN_PROMPT = """你是{teacher_name}，{school_name}{department}的{course_name}课程教师。
请根据以下章节信息，生成一份完整的教案。

## 章节信息
- 章节：{chapter_title}
- 级别：{level}
- 教学目标：{objectives}
- 重点内容：{key_points}
- 难点：{difficulties}

## 教案要求
请按以下结构输出教案（使用Markdown格式）：

### 一、课程信息
- **课程名称**：{course_name}
- **授课章节**：{chapter_title}
- **授课教师**：{teacher_name}
- **课时安排**：{class_hours}
- **授课班级**：待填写
- **授课地点**：待填写

### 二、教学目标
1. **知识目标**：（学生应掌握的具体知识）
2. **能力目标**：（学生应具备的操作能力）
3. **素养目标**：（学生应形成的职业素养）

### 三、教学重点与难点
- **教学重点**：（结合章节重点内容展开）
- **教学难点**：（结合章节难点，给出突破方法）

### 四、教学过程
| 环节 | 时长 | 教师活动 | 学生活动 | 设计意图 |
|------|------|----------|----------|----------|
| 导入 | +课时 | | | |
|    |      |        |        |        |
|    |      |        |        |        |
|    |      |        |        |        |
| 小结 |  |  |  |  |

### 五、课程思政融入
（至少2-3个思政融入点，说明融入方式和预期效果）

### 六、教学反思
（预设学生可能的问题和应对策略）

{extra}

{kb_context}

请确保教案内容紧密结合章节知识点，教学目标具体可评估，教学过程详细可操作。"""

COURSEWARE_PROMPT = """你是{course_name}课程的课件设计专家。请根据以下教案，生成PPT课件逐页大纲。

## 教案内容
{lesson_plan}

## 课件要求
1. 总共12-15页幻灯片
2. 每页包含：标题 + 要点（不超过3-5条）+ 视觉建议（如代码截图、流程图、对比表格）
3. 第1页：课程标题页
4. 第2页：本节课学习目标
5. 第3-12页：知识点讲解（含代码示例）
6. 第13页：课堂练习/互动
7. 第14页：本节小结
8. 第15页：课后作业

请按页号逐一输出课件内容，格式如下：
```
第X页：
标题：XXX
要点：
- 要点1
- 要点2
视觉建议：XXX
```"""

IDEOLOGY_PROMPT = """你是{course_name}课程的思政教育专家。
请为以下知识点设计3-5个课程思政融入方案。

## 知识点
{topic}

## 思政融入要求
1. 每个方案包含：思政主题 + 融入方式 + 案例素材 + 学生活动 + 预期效果
2. 思政主题应从以下维度切入：
   - 科技报国 / 创新精神（码农→工程师的家国情怀）
   - 工匠精神 / 精益求精（代码规范的职业素养）
   - 信息安全 / 职业道德（不写恶意代码）
   - 团队协作 / 开源精神（GitHub协作文化）
   - 终身学习 / 技术迭代（行业变化快，必须持续学习）
3. 融入方式要自然，不能生硬"贴标签"
4. 案例要贴近高职学生的生活实际

请按以下格式输出每个方案：

### 方案X：{思政主题}
- **融入方式**：XXX
- **案例素材**：XXX
- **学生活动**：XXX
- **预期效果**：XXX"""

PRACTICE_PROMPT = """你是{course_name}课程的实训设计专家。
请为以下章节设计分层实训项目。

## 章节信息
- 章节：{chapter_title}
- 重点：{key_points}
- 难点：{difficulties}

## 实训设计原则
1. 三层难度分级：基础（60%学生能独立完成）→ 进阶（40%学生能完成）→ 挑战（20%学生能尝试）
2. 每个实训项目必须包含：任务描述、输入输出示例、评分标准、参考提示
3. 关联"岗课赛证"——说明该项目对应哪种岗位技能或证书考点
4. 总时长控制在90分钟内（含讲解+实操）

请按以下格式输出：

### 基础实训：{项目名称}（30分钟）
- **任务描述**：XXX
- **输入示例**：XXX
- **期望输出**：XXX
- **评分标准**：正确性60% + 规范性20% + 思路20%
- **岗赛关联**：XXX

### 进阶实训：{项目名称}（30分钟）
...

### 挑战实训：{项目名称}（30分钟）
..."""


def generate_lesson_plan(chapter_id, extra_requirements="", course_id=None):
    """生成教案（带缓存 + 知识库增强）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return "章节不存在"

    # 检查缓存
    cached = get_cache(course_id, chapter_id, "lesson_plan", extra_requirements)
    if cached:
        return cached + '\n\n<span class="ai-tag">来自缓存，内容已预先生成</span>'

    cname = _course_name(course_id)
    
    # 知识库增强：检索相关知识
    kb_context = ""
    try:
        from modules.knowledge_store import retrieve
        docs = retrieve(course_id, f"{ch['title']} {' '.join(ch['key_points'][:3])}", top_k=3)
        if docs:
            kb_context = "\n\n## 课程资料参考\n" + "\n".join(f"- {d['text'][:200]}" for d in docs)
    except Exception:
        pass  # 知识库检索失败不阻塞

    fields = {
        "teacher_name": "朱景峰",
        "school_name": "宜宾工业职业技术学院",
        "department": "数字经济学院",
        "course_name": cname,
        "chapter_title": ch["title"],
        "level": ch["level"],
        "objectives": "；".join(ch["objectives"]),
        "key_points": "；".join(ch["key_points"]),
        "difficulties": "；".join(ch["difficulties"]),
        "class_hours": "2课时（90分钟）",
        "extra": f"\n## 七、特殊要求\n{extra_requirements}" if extra_requirements else "",
        "kb_context": kb_context,
    }

    prompt = LESSON_PLAN_PROMPT.format(**fields) + kb_context
    result = deepseek.chat("你是一位经验丰富的高职课程教师，擅长撰写高质量教案。", prompt, max_tokens=4096)
    
    # 写入缓存
    if result:
        set_cache(course_id, chapter_id, "lesson_plan", result, extra_requirements)
    
    return result


def generate_courseware(chapter_id, lesson_plan_text="", course_id=None):
    """生成课件大纲（带缓存）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return "章节不存在"

    # 检查缓存
    plan_hash = hashlib.md5((lesson_plan_text or "").encode()).hexdigest()[:8] if lesson_plan_text else ""
    cached = get_cache(course_id, chapter_id, "courseware", plan_hash)
    if cached:
        return cached + '\n\n<span class="ai-tag">来自缓存</span>'

    lesson_plan = lesson_plan_text or "（待提供教案内容）"
    prompt = COURSEWARE_PROMPT.format(
        course_name=_course_name(course_id),
        lesson_plan=lesson_plan[:3000]
    )
    result = deepseek.chat("你是PPT课件设计专家，擅长将教案转化为清晰美观的课件大纲。", prompt, max_tokens=3072)
    
    if result:
        set_cache(course_id, chapter_id, "courseware", result, plan_hash)
    
    return result


def generate_ideology(chapter_id, topic="", course_id=None):
    """生成思政融入方案（带缓存）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return "章节不存在"

    if not topic:
        topic = f"{ch['title']} - {', '.join(ch['key_points'][:3])}"

    cached = get_cache(course_id, chapter_id, "ideology", topic[:100])
    if cached:
        return cached + '\n\n<span class="ai-tag">来自缓存</span>'

    prompt = IDEOLOGY_PROMPT.format(course_name=_course_name(course_id), topic=topic)
    result = deepseek.chat("你是课程思政教育专家，擅长将思政元素自然融入专业课程教学。", prompt, max_tokens=3072)
    
    if result:
        set_cache(course_id, chapter_id, "ideology", result, topic[:100])
    
    return result


def generate_practice(chapter_id, course_id=None):
    """生成分层实训项目（带缓存）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return "章节不存在"

    cached = get_cache(course_id, chapter_id, "practice", "")
    if cached:
        return cached + '\n\n<span class="ai-tag">来自缓存</span>'

    prompt = PRACTICE_PROMPT.format(
        course_name=_course_name(course_id),
        chapter_title=ch["title"],
        key_points="；".join(ch["key_points"]),
        difficulties="；".join(ch["difficulties"]),
    )
    result = deepseek.chat("你是高职实训课程设计专家，擅长设计分层递进的编程实训项目。", prompt, max_tokens=4096)
    
    if result:
        set_cache(course_id, chapter_id, "practice", result)
    
    return result
