# -*- coding: utf-8 -*-
"""
知识图谱Agent V3.0（课程无关化）
- 节点来自该课程的 course_chapters
- 关系优先取章节 meta_json.relations，否则退化为按 seq 的顺序链
"""
import json
from knowledge_base import get_course_chapters, get_course_chapter


def _chapter_relations(ch):
    """从章节 meta_json 取图谱关系；缺省返回空"""
    meta = ch.get("meta_json", "{}")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    return meta.get("relations", {"prerequisites": [], "leads_to": []})


def _build_edges(chapters):
    """构建关系边：优先用每章 relations，缺失章节则用顺序链兜底"""
    by_id = {c["chapter_id"]: c for c in chapters}
    edges = []
    ids = [c["chapter_id"] for c in chapters]

    # 1) 显式关系
    explicit = set()
    for c in chapters:
        rel = _chapter_relations(c)
        cid = c["chapter_id"]
        for pre in rel.get("prerequisites", []):
            if pre in by_id:
                edges.append({"from": pre, "to": cid, "label": "前置知识", "dashes": False, "color": "#888780"})
                explicit.add((pre, cid))
        for nxt in rel.get("leads_to", []):
            if nxt in by_id:
                edges.append({"from": cid, "to": nxt, "label": "后续章节", "dashes": True, "color": "#378ADD"})
                explicit.add((cid, nxt))

    # 2) 顺序链兜底（仅补齐相邻未连接的）
    for i in range(len(ids) - 1):
        a, b = ids[i], ids[i + 1]
        if (a, b) not in explicit:
            edges.append({"from": a, "to": b, "label": "学习顺序", "dashes": True, "color": "#378ADD"})
    return edges


def generate_graph_data(course_id):
    """生成课程知识图谱的节点和关系数据（ECharts / vis-network 可直接用）"""
    chapters = get_course_chapters(course_id)
    if not chapters:
        return {"nodes": [], "edges": []}

    level_colors = {"入门": "#639922", "基础": "#1D9E75", "进阶": "#378ADD", "综合": "#D85A30"}
    nodes = []
    for ch in chapters:
        keywords = ch.get("keywords", [])
        if isinstance(keywords, str):
            keywords = json.loads(keywords)
        kps = ch.get("key_points", [])
        if isinstance(kps, str):
            kps = json.loads(kps)
        nodes.append({
            "id": ch["chapter_id"],
            "label": ch["title"].replace("第", "").replace("章", ""),
            "fullLabel": ch["title"],
            "level": ch.get("level", ""),
            "color": level_colors.get(ch.get("level", ""), "#888780"),
            "keywords": keywords[:5],
            "size": 40 + len(kps) * 3,
        })

    edges = _build_edges(chapters)
    return {"nodes": nodes, "edges": edges}


def get_chapter_detail_for_graph(course_id, chapter_id):
    """获取章节详情（用于图谱节点点击）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return None

    rel = _chapter_relations(ch)
    prereq_titles, lead_titles = [], []
    for pid in rel.get("prerequisites", []):
        p = get_course_chapter(course_id, pid)
        if p:
            prereq_titles.append(p["title"])
    for lid in rel.get("leads_to", []):
        l = get_course_chapter(course_id, lid)
        if l:
            lead_titles.append(l["title"])

    kps = ch.get("key_points", [])
    if isinstance(kps, str):
        kps = json.loads(kps)
    diffs = ch.get("difficulties", [])
    if isinstance(diffs, str):
        diffs = json.loads(diffs)
    code = ch.get("code_examples", [])
    if isinstance(code, str):
        code = json.loads(code)

    return {
        "chapter": ch,
        "prerequisites": prereq_titles,
        "leads_to": lead_titles,
        "key_points": kps,
        "difficulties": diffs,
        "code_examples": code[:2],
    }


def get_learning_path(course_id, chapter_id):
    """从课程首章到目标章节的推荐学习路径（BFS）"""
    chapters = get_course_chapters(course_id)
    by_id = {c["chapter_id"]: c for c in chapters}
    if chapter_id not in by_id:
        return []

    from collections import deque
    start = chapters[0]["chapter_id"] if chapters else chapter_id
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == chapter_id:
            return path
        rel = _chapter_relations(by_id[current])
        for nxt in rel.get("leads_to", []):
            if nxt in by_id and nxt not in visited:
                visited.add(nxt)
                queue.append(path + [nxt])
    return []
