import traceback, sys, os
# 将 src/ 加入 Python 路径
_src = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
if _src not in sys.path:
    sys.path.insert(0, _src)

try:
    import app
    print("IMPORT_OK platform_version=", app.Config.PLATFORM_VERSION)
    from database import get_first_course_id, get_course_chapters, count_course_documents
    cid = get_first_course_id()
    print("first_course_id=", cid)
    if cid:
        chs = get_course_chapters(cid)
        print("seeded_chapters=", len(chs))
        print("first_chapter=", chs[0]["chapter_id"], chs[0]["title"], "module=", chs[0]["module"])
        print("modules=", sorted(set(c["module"] for c in chs)))
    # 验证课程无关化的关键函数存在
    from knowledge_base import get_course_chapters, get_course_modules
    from modules.knowledge_store import retrieve, ingest_document
    from modules.student_agents import student_qa, generate_quiz_questions
    from modules.knowledge_graph import generate_graph_data
    print("FUNC_OK")
except Exception:
    traceback.print_exc()
