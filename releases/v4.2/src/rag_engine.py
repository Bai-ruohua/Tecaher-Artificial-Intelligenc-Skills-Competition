# -*- coding: utf-8 -*-
"""
RAG检索增强生成引擎 V3.0（课程无关化）
- RAGEngine(course_id) 从数据库构建该课程知识库（章节 + 上传文档切片）
- 不再引用全局硬编码 CHAPTERS，检索严格限定在 course_id 范围内
"""
from config import Config
from knowledge_base import get_course_chapters, get_chapter_text
from modules.knowledge_store import retrieve as store_retrieve


class RAGEngine:
    """轻量级RAG检索引擎（按课程隔离）"""

    def __init__(self, course_id, course_name=""):
        self.course_id = course_id
        self.course_name = course_name or "本课程"

    def search(self, query, top_k=None):
        """检索当前课程的相关资料"""
        top_k = top_k or Config.RAG_TOP_K
        return store_retrieve(self.course_id, query, top_k)

    def generate_rag_prompt(self, query, search_results):
        """生成带RAG上下文的提示词"""
        if not search_results:
            return None, "课程知识库中未找到相关内容。建议：尝试使用更具体的课程术语提问，或向老师咨询。"

        context_parts = []
        source_parts = []
        for i, r in enumerate(search_results, 1):
            context_parts.append(f"[参考{i}] 来源：{r['chapter_title']}\n{r['text']}")
            source_parts.append(f"参考{i}：{r['chapter_title']}（相关度：{r['score']}）")

        context = "\n\n---\n".join(context_parts)
        sources = "\n".join(source_parts)

        system_prompt = f"""你是《{self.course_name}》课程的智能助教。请根据以下课程资料回答学生的问题。

## 教学信息
- 学校：{Config.SCHOOL_NAME}
- 部门：{Config.DEPARTMENT}
- 课程：{self.course_name}
- 教师：{Config.TEACHER_NAME}

## 课程参考资料
{context}

## 回答规则
1. **优先使用参考资料**：答案必须基于上述课程资料，不能凭空编造
2. **标注来源**：每个回答要点后面标注来自哪个章节/资料，格式为「（来源：《章节/资料名》）」
3. **诚实限制**：如果参考资料中没有明确答案，请明确告诉学生"课程资料中未覆盖此内容，建议向老师咨询"
4. **教学风格**：用通俗易懂的语言讲解，适当使用代码示例或类比辅助理解
5. **鼓励思考**：回答完基础知识后，可以追问一个相关的思考题帮助学生加深理解
6. **格式规范**：使用清晰的层级结构（标题、要点、代码块），便于学生阅读"""

        return system_prompt, sources


def get_course_rag(course_id, course_name=""):
    """获取某课程的 RAG 引擎实例"""
    return RAGEngine(course_id, course_name)


def get_rag_context_for_chapter(course_id, chapter_id):
    """获取某个章节的完整RAG上下文（用于章节讲解）"""
    ch_text = get_chapter_text(course_id, chapter_id)
    results = store_retrieve(course_id, chapter_id.replace("ch", ""))
    return {"chapter_text": ch_text, "related_topics": results[:5]}
