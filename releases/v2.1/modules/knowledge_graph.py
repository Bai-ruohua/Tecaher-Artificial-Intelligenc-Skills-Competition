# -*- coding: utf-8 -*-
"""
知识图谱Agent
课程知识关系可视化数据生成
"""
from knowledge_base import CHAPTERS


KNOWLEDGE_RELATIONS = {
    "ch01": {"prerequisites": [], "leads_to": ["ch02", "ch04"]},
    "ch02": {"prerequisites": ["ch01"], "leads_to": ["ch03", "ch04", "ch06"]},
    "ch03": {"prerequisites": ["ch02"], "leads_to": ["ch04", "ch05"]},
    "ch04": {"prerequisites": ["ch01", "ch02", "ch03"], "leads_to": ["ch05"]},
    "ch05": {"prerequisites": ["ch03", "ch04"], "leads_to": ["ch07", "ch08", "ch10"]},
    "ch06": {"prerequisites": ["ch02"], "leads_to": ["ch07", "ch10"]},
    "ch07": {"prerequisites": ["ch05", "ch06"], "leads_to": ["ch08", "ch12"]},
    "ch08": {"prerequisites": ["ch05", "ch07"], "leads_to": ["ch12"]},
    "ch09": {"prerequisites": ["ch07", "ch08"], "leads_to": ["ch11", "ch12"]},
    "ch10": {"prerequisites": ["ch05", "ch06"], "leads_to": ["ch12"]},
    "ch11": {"prerequisites": ["ch09"], "leads_to": ["ch12"]},
    "ch12": {"prerequisites": ["ch07", "ch08", "ch09", "ch10", "ch11"], "leads_to": []},
}


def generate_graph_data():
    """
    生成知识图谱的节点和关系数据
    返回 ECharts / vis-network 可直接使用的格式
    """
    nodes = []
    edges = []
    node_ids = set()

    # 级别对应的颜色
    level_colors = {
        "入门": "#639922",
        "基础": "#1D9E75",
        "进阶": "#378ADD",
        "综合": "#D85A30",
    }

    for ch in CHAPTERS:
        cid = ch["id"]
        node_ids.add(cid)

        color = level_colors.get(ch["level"], "#888780")

        nodes.append({
            "id": cid,
            "label": ch["title"].replace("第", "").replace("章", ""),
            "fullLabel": ch["title"],
            "level": ch["level"],
            "color": color,
            "keywords": ch["keywords"][:5],
            "size": 40 + len(ch["key_points"]) * 3,
        })

    # 生成关系边
    for cid, rel in KNOWLEDGE_RELATIONS.items():
        for prereq in rel["prerequisites"]:
            if prereq in node_ids:
                edges.append({
                    "from": prereq,
                    "to": cid,
                    "label": "前置知识",
                    "dashes": False,
                    "color": "#888780",
                })
        for leads in rel["leads_to"]:
            if leads in node_ids:
                edges.append({
                    "from": cid,
                    "to": leads,
                    "label": "后续章节",
                    "dashes": True,
                    "color": "#378ADD",
                })

    return {"nodes": nodes, "edges": edges}


def get_chapter_detail_for_graph(chapter_id):
    """获取章节详情（用于图谱节点点击）"""
    from knowledge_base import get_chapter

    ch = get_chapter(chapter_id)
    if not ch:
        return None

    rel = KNOWLEDGE_RELATIONS.get(chapter_id, {"prerequisites": [], "leads_to": []})

    prereq_titles = []
    for pid in rel["prerequisites"]:
        pch = get_chapter(pid)
        if pch:
            prereq_titles.append(pch["title"])

    lead_titles = []
    for lid in rel["leads_to"]:
        lch = get_chapter(lid)
        if lch:
            lead_titles.append(lch["title"])

    return {
        "chapter": ch,
        "prerequisites": prereq_titles,
        "leads_to": lead_titles,
        "key_points": ch["key_points"],
        "difficulties": ch["difficulties"],
        "code_examples": ch["code_examples"][:2],
    }


def get_learning_path(chapter_id):
    """获取从入门的推荐学习路径"""
    # BFS找到从第1章到目标章节的路径
    from collections import deque

    if chapter_id not in KNOWLEDGE_RELATIONS:
        return []

    queue = deque([["ch01"]])
    visited = {"ch01"}

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == chapter_id:
            return path

        for next_ch in KNOWLEDGE_RELATIONS.get(current, {}).get("leads_to", []):
            if next_ch not in visited:
                visited.add(next_ch)
                queue.append(path + [next_ch])

    return []
