# -*- coding: utf-8 -*-
"""V3 回归测试：课程无关化 + 双课程隔离"""
import json, sys, os

# 将 src/ 加入 Python 路径
_src = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
if _src not in sys.path:
    sys.path.insert(0, _src)

import app as appmod
from database import (
    get_all_teachers, create_course, create_course_chapter, save_course_document,
    create_student_account, enroll_student, save_student_attempt,
    get_course_chapters, get_course_modules, get_first_course_id,
)
from modules.knowledge_store import retrieve
from modules.data_sync import compute_radar_data, compute_ranking, sync_student_data, compute_gantt_data
from auth import do_login

results = []
def check(name, cond, extra=""):
    results.append((name, cond, extra))
    print(("PASS " if cond else "FAIL ") + name + ("  " + extra if extra else ""))

# 1) 创建第二门课程（高等数学）并写入章节 + 知识库文档
admin = get_all_teachers()[0]
gao_cid = create_course(admin["id"], "高等数学（示例）", "2026春", "演示：任意课程通用")
chk_gao = [
    ("ch01", "第1章 函数与极限", "基础概念"),
    ("ch02", "第2章 导数与微分", "微积分"),
    ("ch03", "第3章 积分", "微积分"),
    ("ch04", "第4章 线性代数基础", "线性代数"),
]
for i, (cid, title, mod) in enumerate(chk_gao):
    create_course_chapter(gao_cid, cid, title, seq=i, level="基础", module=mod)
save_course_document(gao_cid, "导数是描述函数变化率的极限，定义为 f'(x)=lim_{h->0}(f(x+h)-f(x))/h。", "高数讲义.pdf", "ch02")
check("创建第二门课程(高数)", bool(gao_cid))

# 2) 章节按课程隔离
py_chs = get_course_chapters(get_first_course_id())
gao_chs = get_course_chapters(gao_cid)
check("Python课程有12章", len(py_chs) == 12, f"got {len(py_chs)}")
check("高数课程有4章", len(gao_chs) == 4, f"got {len(gao_chs)}")
check("高数模块维度独立", get_course_modules(gao_cid) == ["基础概念", "微积分", "线性代数"], str(get_course_modules(gao_cid)))

# 3) RAG 检索按课程隔离
gao_hits = retrieve(gao_cid, "导数")
py_hits = retrieve(get_first_course_id(), "导数")
gao_text = " ".join(h["text"] for h in gao_hits)
check("高数RAG命中高数资料", "导数" in gao_text and len(gao_hits) > 0, f"hits={len(gao_hits)}")
py_only_python = all("导数" not in h["text"] for h in py_hits) or any("导数" in h["text"] for h in py_hits)
# Python 课程对"导数"不应返回高数切片内容
py_has_gao_doc = any("f'(x)=lim" in h["text"] for h in py_hits)
check("Python课程不串高数文档", not py_has_gao_doc)

# 4) 排名按课程隔离
# 建一个学生并只在高数答题
sid = create_student_account("2026999001", "测试生", hash_pw := __import__("auth").hash_password("123456"), "测试班")
enroll_student(sid, gao_cid)
save_student_attempt(sid, "ch02", "choice", 1, "B", 1, 100, 100, "ok", course_id=gao_cid)
sync_student_data(sid, course_id=gao_cid)
rank_gao = compute_ranking(course_id=gao_cid)
rank_py = compute_ranking(course_id=get_first_course_id())
check("高数排名含该生", any(r["student_id"] == sid for r in rank_gao), f"n={len(rank_gao)}")
# Python 课程排名不应包含只在高数答题的学生（除非他也 enrolled in python，这里没有）
check("Python排名不含高数生", not any(r["student_id"] == sid for r in rank_py), f"n={len(rank_py)}")

# 5) 雷达按课程模块聚合
radar_gao = compute_radar_data(sid, course_id=gao_cid)
radar_dims = [r["dimension"] for r in radar_gao]
check("高数雷达用高数模块", set(radar_dims) == {"基础概念", "微积分", "线性代数"}, str(radar_dims))
check("高数雷达微积分有分", any(r["dimension"] == "微积分" and r["score"] > 0 for r in radar_gao))

# 6) 甘特按课程章节
gantt_gao = compute_gantt_data(sid, course_id=gao_cid)
check("高数甘特4章", len(gantt_gao) == 4, f"got {len(gantt_gao)}")

# 7) HTTP 层：版本号 + 登录 + 当前课程章节
client = appmod.app.test_client()
rv = client.get("/api/version")
check("HTTP /api/version=3.0", rv.get_json().get("platform_version") == "3.0", rv.get_data(as_text=True)[:60])
lr = client.post("/api/auth/login", json={"username": "admin", "password": "admin123", "role": "teacher"})
check("HTTP 教师登录", lr.get_json().get("success") is True, str(lr.get_json().get("data", {}).get("redirect")))
cc = client.get("/api/course/chapters")
js = cc.get_json()
check("HTTP 当前课程章节(12)", js.get("success") and len(js.get("chapters", [])) == 12, f"got {len(js.get('chapters',[]))}")

print("\n==== 总结 ====")
fails = [n for n, c, _ in results if not c]
print(f"通过 {sum(1 for _,c,_ in results if c)}/{len(results)}")
if fails:
    print("失败项:", fails)
else:
    print("全部通过 ✅")
