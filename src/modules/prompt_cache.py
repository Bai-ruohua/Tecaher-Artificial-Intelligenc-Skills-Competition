# -*- coding: utf-8 -*-
"""
Prompt 缓存系统：对相同章节 + 相同功能的 AI 生成结果进行缓存
降低 API 调用次数，节省 token，提升响应速度
"""
import hashlib
import json

# 缓存有效期：7天（秒）
CACHE_TTL = 7 * 24 * 3600


def _cache_key(course_id, chapter_id, func_type, extra_hash=""):
    """生成缓存唯一键"""
    raw = f"{course_id}|{chapter_id}|{func_type}|{extra_hash}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cache(course_id, chapter_id, func_type, extra_hash=""):
    """获取缓存，未命中返回 None"""
    from database import get_db
    key = _cache_key(course_id, chapter_id, func_type, extra_hash)
    conn = get_db()
    row = conn.execute(
        "SELECT result FROM prompt_cache WHERE cache_key=? AND course_id=? AND expires_at > datetime('now')",
        (key, course_id)
    ).fetchone()
    if row:
        return row["result"]
    return None


def set_cache(course_id, chapter_id, func_type, result, extra_hash=""):
    """写入缓存"""
    from database import get_db
    key = _cache_key(course_id, chapter_id, func_type, extra_hash)
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO prompt_cache (cache_key, course_id, chapter_id, func_type, result, expires_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now', ?))",
        (key, course_id, chapter_id, func_type, result, f"+{CACHE_TTL} seconds")
    )
    conn.commit()


def clear_cache(course_id=None, chapter_id=None, func_type=None):
    """清除缓存（可按条件过滤）"""
    from database import get_db
    conn = get_db()
    where = []
    params = []
    if course_id:
        where.append("course_id=?")
        params.append(course_id)
    if chapter_id:
        where.append("chapter_id=?")
        params.append(chapter_id)
    if func_type:
        where.append("func_type=?")
        params.append(func_type)

    sql = "DELETE FROM prompt_cache"
    if where:
        sql += " WHERE " + " AND ".join(where)
    conn.execute(sql, params)
    conn.commit()


def get_cache_stats(course_id=None):
    """获取缓存统计"""
    from database import get_db
    conn = get_db()
    if course_id:
        total = conn.execute("SELECT COUNT(*) FROM prompt_cache WHERE course_id=?", (course_id,)).fetchone()[0]
        hits = conn.execute("SELECT COUNT(*) FROM prompt_cache WHERE course_id=? AND expires_at > datetime('now')", (course_id,)).fetchone()[0]
    else:
        total = conn.execute("SELECT COUNT(*) FROM prompt_cache").fetchone()[0]
        hits = conn.execute("SELECT COUNT(*) FROM prompt_cache WHERE expires_at > datetime('now')").fetchone()[0]
    return {"total": total, "valid": hits, "expired": total - hits}
