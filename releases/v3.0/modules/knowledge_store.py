# -*- coding: utf-8 -*-
"""
知识库存储层 V3.0
负责按课程隔离的文档上传、切片、检索与删除。
依赖：database（course_documents 表）
支持格式：.txt .md .pdf .docx（后两者在缺失解析库时给出友好提示）
"""
import os
import re
from database import (
    save_course_document, get_course_documents, count_course_documents,
    delete_course_documents, get_course_chapter,
)
from knowledge_base import get_course_chapters


CHUNK_SIZE = 600          # 每个切片字符数
CHUNK_OVERLAP = 80        # 切片重叠字符数


def _read_text_file(path):
    """读取纯文本类文件（txt/md 等）"""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise RuntimeError("未安装 PDF 解析库（pip install pypdf）")
    reader = PdfReader(path)
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    return text


def _read_docx(path):
    try:
        import docx
    except ImportError:
        raise RuntimeError("未安装 Word 解析库（pip install python-docx）")
    doc = docx.Document(path)
    return "\n".join((p.text or "") for p in doc.paragraphs)


def _read_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md", ".csv", ".json", ".py", ".text"):
        return _read_text_file(path)
    if ext == ".pdf":
        return _read_pdf(path)
    if ext in (".docx", ".doc"):
        return _read_docx(path)
    # 兜底：按文本读
    return _read_text_file(path)


def _chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """把文本切成带重叠的片段"""
    text = re.sub(r"\s+\n", "\n", text).strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def ingest_document(course_id, file_path, chapter_id=""):
    """
    上传并切片一个文档到某课程知识库。
    返回：{"saved": int, "source_file": str}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    raw = _read_file(file_path)
    chunks = _chunk_text(raw)
    source = os.path.basename(file_path)
    saved = 0
    for c in chunks:
        # 尝试把切片归属到最相关的章节（按关键词命中），否则留空
        target_ch = chapter_id or _infer_chapter(course_id, c)
        save_course_document(course_id, c, source, target_ch)
        saved += 1
    return {"saved": saved, "source_file": source}


def _infer_chapter(course_id, text):
    """根据关键词命中把切片归入最相关章节（弱启发，命中不到返回空）"""
    chapters = get_course_chapters(course_id)
    if not chapters:
        return ""
    text_lower = text.lower()
    best, best_score = "", 0
    for ch in chapters:
        kws = ch.get("keywords", [])
        if isinstance(kws, str):
            import json as _json
            kws = _json.loads(kws)
        score = sum(1 for k in kws if k and k.lower() in text_lower)
        if score > best_score:
            best_score, best = score, ch["chapter_id"]
    return best if best_score > 0 else ""


def get_documents(course_id, limit=200):
    return get_course_documents(course_id, limit)


def count_documents(course_id):
    return count_course_documents(course_id)


def delete_documents(course_id):
    delete_course_documents(course_id)


def retrieve(course_id, query, top_k=5):
    """
    在指定课程范围内做轻量相关性检索（章节文本 + 上传文档切片）。
    返回按相关度降序的文档块列表。
    """
    docs = []

    # 1) 章节结构化知识
    chapters = get_course_chapters(course_id)
    for ch in chapters:
        cid = ch["chapter_id"]
        title = ch.get("title", "")
        keywords = ch.get("keywords", [])
        if isinstance(keywords, str):
            import json as _json
            keywords = _json.loads(keywords)
        key_points = ch.get("key_points", [])
        if isinstance(key_points, str):
            import json as _json
            key_points = _json.loads(key_points)
        difficulties = ch.get("difficulties", [])
        if isinstance(difficulties, str):
            import json as _json
            difficulties = _json.loads(difficulties)
        docs.append({
            "chapter_id": cid, "chapter_title": title, "level": ch.get("level", ""),
            "text": f"【{title}】关键词：{', '.join(keywords)}；重点：{', '.join(key_points)}；难点：{', '.join(difficulties)}",
            "keywords": keywords,
        })

    # 2) 上传文档切片
    for d in get_course_documents(course_id, limit=500):
        docs.append({
            "chapter_id": d.get("chapter_id") or "",
            "chapter_title": d.get("source_file") or "课程资料",
            "level": "",
            "text": d["chunk_text"],
            "keywords": [],
        })

    scored = []
    for doc in docs:
        s = _relevance(query, doc)
        if s > 0:
            scored.append((s, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen = set()
    results = []
    for score, doc in scored:
        key = doc["chapter_id"] or doc["text"][:40]
        if key not in seen:
            seen.add(key)
            results.append({
                "chapter_id": doc["chapter_id"],
                "chapter_title": doc["chapter_title"],
                "text": doc["text"],
                "score": round(score, 1),
            })
        if len(results) >= top_k:
            break
    return results


def _relevance(query, doc):
    """轻量相关性评分（关键词重叠 + 子串匹配）"""
    query_lower = query.lower()
    text_lower = doc.get("text", "").lower()
    score = 0.0
    for kw in doc.get("keywords", []):
        if kw.lower() in query_lower or query_lower in kw.lower():
            score += 5.0
    for word in query_lower.split():
        if word and word in text_lower:
            score += 2.0
    for i in range(len(query_lower)):
        for j in range(i + 2, min(i + 20, len(query_lower) + 1)):
            sub = query_lower[i:j]
            if sub in text_lower:
                score += len(sub) * 0.3
    if doc.get("chapter_title", "").lower() in query_lower:
        score += 3.0
    return score
