# -*- coding: utf-8 -*-
"""
AI备课助手模块
教案生成 / 课件大纲 / 思政融入 / 分层实训设计
"""
from knowledge_base import get_chapter
from deepseek_client import deepseek

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


def generate_lesson_plan(chapter_id, extra_requirements=""):
    """生成教案"""
    ch = get_chapter(chapter_id)
    if not ch:
        return "章节不存在"

    fields = {
        "teacher_name": "朱景峰",
        "school_name": "宜宾工业职业技术学院",
        "department": "数字经济学院",
        "course_name": "Python程序设计",
        "chapter_title": ch["title"],
        "level": ch["level"],
        "objectives": "；".join(ch["objectives"]),
        "key_points": "；".join(ch["key_points"]),
        "difficulties": "；".join(ch["difficulties"]),
        "class_hours": "2课时（90分钟）",
        "extra": f"\n## 七、特殊要求\n{extra_requirements}" if extra_requirements else "",
    }

    prompt = LESSON_PLAN_PROMPT.format(**fields)
    return deepseek.chat("你是一位经验丰富的高职课程教师，擅长撰写高质量教案。", prompt, max_tokens=4096)


def generate_courseware(chapter_id, lesson_plan_text=""):
    """生成课件大纲"""
    ch = get_chapter(chapter_id)
    if not ch:
        return "章节不存在"

    lesson_plan = lesson_plan_text or "（待提供教案内容）"
    prompt = COURSEWARE_PROMPT.format(
        course_name="Python程序设计",
        lesson_plan=lesson_plan[:3000]
    )
    return deepseek.chat("你是PPT课件设计专家，擅长将教案转化为清晰美观的课件大纲。", prompt, max_tokens=3072)


def generate_ideology(chapter_id, topic=""):
    """生成思政融入方案"""
    ch = get_chapter(chapter_id)
    if not ch:
        return "章节不存在"

    if not topic:
        topic = f"{ch['title']} - {', '.join(ch['key_points'][:3])}"

    prompt = IDEOLOGY_PROMPT.format(course_name="Python程序设计", topic=topic)
    return deepseek.chat("你是课程思政教育专家，擅长将思政元素自然融入专业课程教学。", prompt, max_tokens=3072)


def generate_practice(chapter_id):
    """生成分层实训项目"""
    ch = get_chapter(chapter_id)
    if not ch:
        return "章节不存在"

    prompt = PRACTICE_PROMPT.format(
        course_name="Python程序设计",
        chapter_title=ch["title"],
        key_points="；".join(ch["key_points"]),
        difficulties="；".join(ch["difficulties"]),
    )
    return deepseek.chat("你是高职实训课程设计专家，擅长设计分层递进的编程实训项目。", prompt, max_tokens=4096)
