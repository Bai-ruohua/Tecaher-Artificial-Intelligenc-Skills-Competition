# -*- coding: utf-8 -*-
"""
RAG检索增强生成引擎
支持课件向量化、语义检索、答案溯源
"""
import os
import json
import hashlib
from config import Config
from knowledge_base import CHAPTERS, get_chapter_text


class RAGEngine:
    """轻量级RAG检索引擎"""

    def __init__(self):
        self.documents = []
        self.embeddings_cache = {}
        self._build_knowledge_base()

    def _build_knowledge_base(self):
        """构建课程知识库（基于关键词匹配 + TF-IDF思想）"""
        for ch in CHAPTERS:
            # 每个章节作为一个文档块
            doc_text = get_chapter_text(ch["id"])
            self.documents.append({
                "chapter_id": ch["id"],
                "chapter_title": ch["title"],
                "text": doc_text,
                "keywords": ch["keywords"],
                "level": ch["level"],
            })

            # 将重点和难点单独作为细粒度块
            for kp in ch["key_points"]:
                self.documents.append({
                    "chapter_id": ch["id"],
                    "chapter_title": ch["title"],
                    "text": f"【{ch['title']}】重点：{kp}",
                    "keywords": [kp],
                    "level": ch["level"],
                })

            for diff in ch["difficulties"]:
                self.documents.append({
                    "chapter_id": ch["id"],
                    "chapter_title": ch["title"],
                    "text": f"【{ch['title']}】难点：{diff}",
                    "keywords": [diff],
                    "level": ch["level"],
                })

            # 练习问答块
            for pq in ch["practice_questions"]:
                self.documents.append({
                    "chapter_id": ch["id"],
                    "chapter_title": ch["title"],
                    "text": f"【{ch['title']}】问答：{pq['q']} 答案：{pq['a']}",
                    "keywords": [pq["q"]],
                    "level": ch["level"],
                })

            # 代码示例块
            for i, code in enumerate(ch["code_examples"]):
                self.documents.append({
                    "chapter_id": ch["id"],
                    "chapter_title": ch["title"],
                    "text": f"【{ch['title']}】代码示例：\n{code}",
                    "keywords": [],
                    "level": ch["level"],
                })

    def _compute_relevance(self, query, doc):
        """计算查询与文档的相关性分数（基于关键词重叠率+字符串匹配）"""
        query_lower = query.lower()
        text_lower = doc["text"].lower()
        score = 0.0

        # 关键词精确匹配
        for kw in doc.get("keywords", []):
            if kw.lower() in query_lower or query_lower in kw.lower():
                score += 5.0

        # 文本中包含查询词（逐词匹配）
        query_words = query_lower.split()
        for word in query_words:
            if word in text_lower:
                score += 2.0

        # 较长的子串匹配
        for i in range(len(query_lower)):
            for j in range(i + 2, min(i + 20, len(query_lower) + 1)):
                sub = query_lower[i:j]
                if sub in text_lower:
                    score += len(sub) * 0.3

        # 章节标题匹配
        if doc["chapter_title"].lower() in query_lower:
            score += 3.0

        return score

    def search(self, query, top_k=None):
        """语义搜索（基于关键词+文本匹配的轻量实现）"""
        top_k = top_k or Config.RAG_TOP_K
        scored_docs = []

        for doc in self.documents:
            score = self._compute_relevance(query, doc)
            if score > 0:
                scored_docs.append((score, doc))

        # 按分数排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # 去重（同一章节的知识点合并）
        seen_chapters = set()
        results = []
        for score, doc in scored_docs:
            if doc["chapter_id"] not in seen_chapters:
                seen_chapters.add(doc["chapter_id"])
                results.append({
                    "chapter_id": doc["chapter_id"],
                    "chapter_title": doc["chapter_title"],
                    "text": doc["text"],
                    "score": round(score, 1),
                })
            if len(results) >= top_k:
                break

        return results

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

        system_prompt = f"""你是Python课程的智能助教。请根据以下课程资料回答学生的问题。

## 教学信息
- 学校：{Config.SCHOOL_NAME}
- 部门：{Config.DEPARTMENT}
- 课程：{Config.COURSE_NAME}
- 教师：{Config.TEACHER_NAME}

## 课程参考资料
{context}

## 回答规则
1. **优先使用参考资料**：答案必须基于上述课程资料，不能凭空编造
2. **标注来源**：每个回答要点后面标注来自哪个章节，格式为「（来源：第X章《章节名》）」
3. **诚实限制**：如果参考资料中没有明确答案，请明确告诉学生"课程资料中未覆盖此内容，建议向老师咨询"
4. **教学风格**：用通俗易懂的语言讲解，适当使用代码示例或类比辅助理解
5. **鼓励思考**：回答完基础知识后，可以追问一个相关的思考题帮助学生加深理解
6. **格式规范**：使用清晰的层级结构（标题、要点、代码块），便于学生阅读"""

        return system_prompt, sources


# 全局单例
rag = RAGEngine()


def get_rag_context_for_chapter(chapter_id):
    """获取某个章节的完整RAG上下文（用于章节讲解）"""
    ch_text = get_chapter_text(chapter_id)
    results = rag.search(chapter_id.replace("ch", ""))
    return {"chapter_text": ch_text, "related_topics": results[:5]}
