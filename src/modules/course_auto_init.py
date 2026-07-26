# -*- coding: utf-8 -*-
"""
课程自动初始化模块 V4.3
新建课程后，若用户 5s 内未上传课件，自动调用 DeepSeek 生成课程知识体系。
若用户后续上传课件，自动合并/优化已有知识框架。
"""
import json
import time
from database import (
    get_db, create_course_chapter, save_course_document, get_course_chapters,
    get_course_documents, delete_course_documents,
)
from deepseek_client import deepseek


def auto_init_course(course_id, course_name, description=""):
    """
    自动为课程生成知识体系。
    1. 如果课程没有章节 → 自动生成章节体系（数量根据课程内容动态决定）
    2. 无论是否有章节 → 生成课程知识概述文档
    返回 (success, message, details)
    """
    details = {"chapters": 0, "documents": 0}
    chapters_created = 0

    # 1. 检查是否已有章节
    existing = get_course_chapters(course_id)
    if not existing:
        chapters = _ai_generate_chapters(course_name, description)
        for ch in chapters:
            try:
                # 将 job_tasks 打包到 meta_json 中
                meta = {"job_tasks": ch.get("job_tasks", [])}
                create_course_chapter(
                    course_id=course_id,
                    chapter_id=ch["id"],
                    title=ch["title"],
                    seq=ch["seq"],
                    level=ch.get("level", ""),
                    module=ch.get("module", ""),
                    keywords=ch.get("keywords", []),
                    objectives=ch.get("objectives", []),
                    key_points=ch.get("key_points", []),
                    difficulties=ch.get("difficulties", []),
                    meta_json=meta,
                )
                chapters_created += 1
            except Exception as e:
                print(f"  [auto_init] 章节创建失败 {ch.get('id','')}: {e}")
        details["chapters"] = chapters_created

    # 2. 生成课程知识概述文档（始终生成）
    doc_count = _ai_generate_knowledge_doc(course_id, course_name, description)
    details["documents"] = doc_count

    msg = f"已生成 {chapters_created} 个章节，{doc_count} 份知识文档"
    return (True, msg, details)


def merge_knowledge_on_upload(course_id, course_name=""):
    """
    用户上传课件后调用：重新生成知识框架，与已有内容合并。
    保留用户上传的文档，AI 生成的概述文档标为可覆盖。
    """
    # 标记之前 AI 生成的文档（source_file 以 "__auto__" 开头）
    conn = get_db()
    conn.execute("DELETE FROM course_documents WHERE course_id=? AND source_file LIKE '__auto__%'", (course_id,))
    conn.commit()
    conn.close()

    # 如果之前没生成过章节且现有章节为空，生成章节
    existing = get_course_chapters(course_id)
    if not existing:
        chs = _ai_generate_chapters(course_name or "本课程", "")
        for ch in chs:
            create_course_chapter(
                course_id=course_id,
                chapter_id=ch["id"],
                title=ch["title"],
                seq=ch["seq"],
                level=ch.get("level", ""),
                module=ch.get("module", ""),
                keywords=ch.get("keywords", []),
                objectives=ch.get("objectives", []),
                key_points=ch.get("key_points", []),
                difficulties=ch.get("difficulties", []),
                meta_json={"job_tasks": ch.get("job_tasks", [])},
            )

    return True


def _ai_generate_chapters(course_name, description):
    """
    调用 DeepSeek 生成课程章节体系
    返回 [{"id":"ch01","title":"...","seq":0,"level":"...","module":"...",...}]
    """
    prompt = f"""你是一位高职课程设计专家。请为课程「{course_name}」设计章节体系。
{('课程描述：'+description) if description else ''}

要求：
1. 根据课程知识量自动确定章节数量，内容多就多分、少就少分，不限制数量
2. 每章 id 格式为 ch01, ch02, ...
2. seq 从 0 开始递增
3. level 为"了解/理解/掌握/熟练"
4. module 为模块分组名称（如"基础入门""核心技能""综合实战"等）
5. keywords 为 3-5 个关键词
6. objectives 为 2-3 个教学目标
7. key_points 为 2-3 个知识要点
8. difficulties 为 1-2 个难点
9. job_tasks 为 1-2 个岗位任务

请严格按以下 JSON 格式输出，不要有其他文字：
[
  {{"id":"ch01","title":"...","seq":0,"level":"理解","module":"模块名","keywords":["..."],"objectives":["..."],"key_points":["..."],"difficulties":["..."],"job_tasks":["..."]}},
  ...
]"""

    try:
        result = deepseek.chat(
            "你是一个严谨的数据输出助手，只输出纯 JSON 数组，不包含任何解释文字。",
            prompt,
            max_tokens=4096
        )
        # 清理可能的 markdown 包裹
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

        chapters = json.loads(result)
        if isinstance(chapters, list):
            print(f"  [auto_init] AI 生成了 {len(chapters)} 个章节")
            return chapters
    except Exception as e:
        print(f"  [auto_init] AI 生成章节失败: {e}")

    # 降级：返回硬编码通用课程结构
    return _fallback_chapters(course_name)


def _extract_title(text, index=0):
    """从文本片段中提取简短标题（取第一个句号前的有意义内容，最多 20 字）"""
    import re
    # 取第一句
    text = text.strip()
    # 尝试按句号/感叹号/问号/换行分割
    sentences = re.split(r'[。！？\n]', text)
    first = sentences[0].strip() if sentences else text
    # 去掉常见的引导词
    for prefix in ["以下是", "这是", "首先", "其次", "然后", "最后", "上述", "以下为"]:
        if first.startswith(prefix):
            first = first[len(prefix):]
            break
    # 限制长度
    if len(first) > 20:
        first = first[:20]
    if first:
        return first
    return f"知识点{index+1}"


def _ai_generate_knowledge_doc(course_id, course_name, description):
    """
    调用 DeepSeek 生成课程知识概述，写入 course_documents
    返回写入的文档切片数
    """
    chapters = get_course_chapters(course_id)
    chapter_titles = [f"{c['chapter_id']} {c['title']}" for c in chapters] if chapters else ["（待定）"]

    prompt = f"""你是一位高职课程专家。请为课程「{course_name}」撰写一份课程知识概述。

已有章节：
{chr(10).join(f'- {t}' for t in chapter_titles)}

{('课程描述：'+description) if description else ''}

请生成以下内容：
1. 课程核心概念（10-15 条，每条 1-2 句话）
2. 按模块/主题分组的知识点（每个模块 3-5 条）
3. 典型应用场景（3-5 个场景，每个场景 2-3 句话）
4. 学习建议与重难点提示

要求内容准确、结构清晰、适合高职学生理解。"""

    try:
        result = deepseek.chat(
            "你是一位经验丰富的高职教育专家，擅长撰写课程知识体系。",
            prompt,
            max_tokens=4096
        )

        # 切分成知识切片并存入数据库
        chunks = _chunk_text(result, size=800, overlap=100)
        count = 0
        for i, chunk in enumerate(chunks):
            # 从内容中提取简短标题
            title = _extract_title(chunk, i)
            save_course_document(
                course_id=course_id,
                chunk_text=chunk,
                source_file=f"__auto__{course_name}—{title}",
                chapter_id=""
            )
            count += 1
        print(f"  [auto_init] 生成了 {count} 个知识切片")
        return count
    except Exception as e:
        print(f"  [auto_init] 生成知识文档失败: {e}")
        return 0


def _chunk_text(text, size=800, overlap=100):
    """将长文本切分成重叠切片"""
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # 尽量在句号/换行处断句
        cut = text.rfind("。", start, end)
        if cut > start + size // 2:
            end = cut + 1
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def _fallback_chapters(course_name):
    """AI 调用失败时的降级方案"""
    return [
        {"id": "ch01", "title": f"{course_name}概述", "seq": 0, "level": "了解",
         "module": "课程导入", "keywords": ["概述", "发展", "应用"],
         "objectives": ["了解课程背景与发展", "理解课程应用领域"],
         "key_points": ["课程定位", "应用场景"], "difficulties": ["课程体系认知"],
         "job_tasks": ["调研课程应用领域"]},
        {"id": "ch02", "title": "基础知识", "seq": 1, "level": "理解",
         "module": "基础入门", "keywords": ["基础", "概念", "原理"],
         "objectives": ["掌握核心概念", "理解基本原理"],
         "key_points": ["核心概念", "基本原理"], "difficulties": ["抽象概念理解"],
         "job_tasks": ["基础概念应用"]},
        {"id": "ch03", "title": "核心技能（一）", "seq": 2, "level": "掌握",
         "module": "核心技能", "keywords": ["技能", "实践", "操作"],
         "objectives": ["掌握核心操作技能", "能够独立完成实践任务"],
         "key_points": ["操作流程", "注意事项"], "difficulties": ["复杂操作步骤"],
         "job_tasks": ["完成实践任务"]},
        {"id": "ch04", "title": "核心技能（二）", "seq": 3, "level": "掌握",
         "module": "核心技能", "keywords": ["进阶", "应用", "综合"],
         "objectives": ["掌握进阶技能", "综合运用所学知识"],
         "key_points": ["进阶技巧", "综合案例"], "difficulties": ["知识综合运用"],
         "job_tasks": ["综合案例实践"]},
        {"id": "ch05", "title": "综合实战", "seq": 4, "level": "熟练",
         "module": "综合实战", "keywords": ["实战", "项目", "综合"],
         "objectives": ["完成综合项目", "培养解决实际问题能力"],
         "key_points": ["项目分析", "方案设计"], "difficulties": ["项目整体把控"],
         "job_tasks": ["完成综合项目"]},
        {"id": "ch06", "title": "课程总结与拓展", "seq": 5, "level": "了解",
         "module": "课程拓展", "keywords": ["总结", "拓展", "进阶"],
         "objectives": ["梳理课程知识体系", "了解进阶方向"],
         "key_points": ["知识体系梳理", "进阶方向"], "difficulties": ["知识体系融会贯通"],
         "job_tasks": ["制定个人学习计划"]},
    ]


def generate_from_uploads(course_id, course_name, description=""):
    """
    用户上传课件后调用：基于上传的文档内容，用 AI 生成课程章节体系 + 知识文档。
    返回 (success, message, details)
    """
    from modules.knowledge_store import get_course_documents, list_documents
    details = {"chapters": 0, "documents": 0}

    # 1. 收集已上传的知识切片作为 AI 的参考素材
    docs = get_course_documents(course_id, limit=500)
    if not docs:
        return (False, "知识库为空，请先上传课件", details)

    # 取前 10 个切片作为素材样本（避免超长）
    samples = []
    total_chars = 0
    for d in docs:
        text = d.get("chunk_text", "")
        if total_chars + len(text) > 6000:
            break
        samples.append(text)
        total_chars += len(text)

    sample_text = "\n---\n".join(samples[:8])

    # 2. 检查是否已有章节
    existing = get_course_chapters(course_id)
    chapters_created = 0

    # 用户点击"生成"时，始终基于上传内容重新生成/优化章节
    # 清除旧的章节（保留用户手动创建的？无需保留，因为是根据上传内容重新生成的）
    if existing:
        conn2 = get_db()
        conn2.execute("DELETE FROM course_chapters WHERE course_id=?", (course_id,))
        conn2.commit()
        conn2.close()

    # 基于上传内容生成章节
    chapters = _ai_generate_chapters_from_docs(course_name, sample_text, description)
    for ch in chapters:
        try:
            meta = {"job_tasks": ch.get("job_tasks", [])}
            create_course_chapter(
                course_id=course_id,
                chapter_id=ch["id"],
                title=ch["title"],
                seq=ch["seq"],
                level=ch.get("level", ""),
                module=ch.get("module", ""),
                keywords=ch.get("keywords", []),
                objectives=ch.get("objectives", []),
                key_points=ch.get("key_points", []),
                difficulties=ch.get("difficulties", []),
                meta_json=meta,
            )
            chapters_created += 1
        except Exception as e:
            print(f"  [gen_from_uploads] 章节创建失败: {e}")
    details["chapters"] = chapters_created

    # 3. 基于上传内容重新生成知识文档（覆盖旧的 AI 文档）
    conn = get_db()
    conn.execute("DELETE FROM course_documents WHERE course_id=? AND source_file LIKE '__auto__%'", (course_id,))
    conn.commit()
    conn.close()

    doc_count = _ai_generate_knowledge_from_docs(course_id, course_name, sample_text)
    details["documents"] = doc_count

    msg = f"基于上传课件生成 {chapters_created} 个章节，{doc_count} 份知识文档"
    return (True, msg, details)


def _ai_generate_chapters_from_docs(course_name, sample_text, description):
    """基于上传的文档内容生成章节体系"""
    prompt = f"""你是一位高职课程设计专家。以下是课程「{course_name}」的课件素材片段：

{sample_text}

{('课程描述：'+description) if description else ''}

请根据以上课件素材，为该课程设计章节体系。注意：
1. **根据课件内容的实际知识量和知识点分布自动切分章节数量**，内容多就多分几章，内容少就少分，不限制上下限
2. 每章的内容量要适中（大约相当于 1-2 课时的教学量）
3. 章与章之间要有清晰的知识递进关系

要求：
1. 章节内容必须紧扣课件素材中的知识点
2. 每章 id 格式为 ch01, ch02, ...
3. seq 从 0 开始递增
4. level 为"了解/理解/掌握/熟练"
5. module 为模块分组名称
6. keywords 为 3-5 个关键词
7. objectives/key_points/difficulties 各 2-3 条

请严格按以下 JSON 格式输出：
[
  {{"id":"ch01","title":"...","seq":0,"level":"理解","module":"模块名","keywords":["..."],"objectives":["..."],"key_points":["..."],"difficulties":["..."]}},
  ...
]"""

    try:
        result = deepseek.chat(
            "你是一个严谨的数据输出助手，只输出纯 JSON 数组。",
            prompt,
            max_tokens=4096
        )
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()
        chapters = json.loads(result)
        if isinstance(chapters, list):
            print(f"  [gen_from_uploads] AI 基于课件生成了 {len(chapters)} 个章节")
            return chapters
    except Exception as e:
        print(f"  [gen_from_uploads] AI 生成失败: {e}")

    return _fallback_chapters(course_name)


def _ai_generate_knowledge_from_docs(course_id, course_name, sample_text):
    """基于上传文档生成知识概述文档"""
    prompt = f"""你是一位高职课程专家。请根据课程「{course_name}」的课件素材，撰写一份课程知识概述。

课件素材片段：
{sample_text[:4000]}

请生成以下内容：
1. 课程核心概念（10-15 条）
2. 按模块分组的核心知识点
3. 典型应用场景
4. 学习建议

要求内容紧扣课件素材，准确、清晰，适合高职学生理解。"""

    try:
        result = deepseek.chat(
            "你是一位经验丰富的高职教育专家。",
            prompt,
            max_tokens=4096
        )
        chunks = _chunk_text(result, size=800, overlap=100)
        count = 0
        for i, chunk in enumerate(chunks):
            title = _extract_title(chunk, i)
            save_course_document(course_id, chunk, f"__auto__{course_name}—{title}", "")
            count += 1
        print(f"  [gen_from_uploads] 生成 {count} 个知识切片")
        return count
    except Exception as e:
        print(f"  [gen_from_uploads] 生成知识文档失败: {e}")
        return 0
