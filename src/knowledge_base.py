# -*- coding: utf-8 -*-
"""
课程体系数据层 V4.3
- 运行时章节/模块一律从数据库 course_chapters 读取
- 预置多个高职课程模板，新建课程时可选择
"""
from config import Config
import database


# ===== 种子模板：Python 12章 =====
_PY_MODULE = {
    "ch01": "基础语法", "ch02": "基础语法", "ch03": "基础语法",
    "ch04": "控制流", "ch05": "控制流",
    "ch06": "数据结构", "ch07": "数据结构", "ch08": "数据结构",
    "ch09": "函数模块", "ch10": "函数模块",
    "ch11": "面向对象", "ch12": "面向对象",
}

_PY_RELATIONS = {
    "ch01": {"prerequisites": [], "leads_to": ["ch02", "ch04"]},
    "ch02": {"prerequisites": ["ch01"], "leads_to": ["ch03", "ch04", "ch06"]},
    "ch03": {"prerequisites": ["ch02"], "leads_to": ["ch04", "ch05"]},
    "ch04": {"prerequisites": ["ch01", "ch02"], "leads_to": ["ch05", "ch06", "ch09"]},
    "ch05": {"prerequisites": ["ch04"], "leads_to": ["ch06", "ch10"]},
    "ch06": {"prerequisites": ["ch01", "ch02", "ch04"], "leads_to": ["ch07", "ch08"]},
    "ch07": {"prerequisites": ["ch06"], "leads_to": ["ch08"]},
    "ch08": {"prerequisites": ["ch06", "ch07"], "leads_to": ["ch09", "ch10"]},
    "ch09": {"prerequisites": ["ch06"], "leads_to": ["ch10", "ch11"]},
    "ch10": {"prerequisites": ["ch06", "ch09"], "leads_to": ["ch11", "ch12"]},
    "ch11": {"prerequisites": ["ch09", "ch10"], "leads_to": ["ch12"]},
    "ch12": {"prerequisites": ["ch09", "ch10", "ch11"], "leads_to": []},
}

SEED_PYTHON_CHAPTERS = [
    {"id": "ch01", "seq": 1,  "title": "第1章 Python入门与环境搭建",       "level": "入门", "module": "基础语法"},
    {"id": "ch02", "seq": 2,  "title": "第2章 变量与数据类型",             "level": "入门", "module": "基础语法"},
    {"id": "ch03", "seq": 3,  "title": "第3章 输入输出与格式化",           "level": "入门", "module": "基础语法"},
    {"id": "ch04", "seq": 4,  "title": "第4章 条件判断",                   "level": "基础", "module": "控制流"},
    {"id": "ch05", "seq": 5,  "title": "第5章 循环结构",                   "level": "基础", "module": "控制流"},
    {"id": "ch06", "seq": 6,  "title": "第6章 字符串与列表",               "level": "基础", "module": "数据结构"},
    {"id": "ch07", "seq": 7,  "title": "第7章 元组与字典",                 "level": "基础", "module": "数据结构"},
    {"id": "ch08", "seq": 8,  "title": "第8章 集合与高级数据结构",         "level": "进阶", "module": "数据结构"},
    {"id": "ch09", "seq": 9,  "title": "第9章 函数定义与调用",             "level": "进阶", "module": "函数模块"},
    {"id": "ch10", "seq": 10, "title": "第10章 模块与包管理",              "level": "进阶", "module": "函数模块"},
    {"id": "ch11", "seq": 11, "title": "第11章 类与对象",                  "level": "综合", "module": "面向对象"},
    {"id": "ch12", "seq": 12, "title": "第12章 继承、多态与综合项目",      "level": "综合", "module": "面向对象"},
]


# ===== 种子模板：数据库原理与应用（8章）=====
DB_MODULE = {
    "db01": "基础理论", "db02": "基础理论",
    "db03": "SQL语言", "db04": "SQL语言", "db05": "SQL语言",
    "db06": "设计与优化", "db07": "设计与优化",
    "db08": "新技术",
}

SEED_DATABASE_CHAPTERS = [
    {"id": "db01", "seq": 1, "title": "数据库系统概述",           "level": "入门", "module": "基础理论"},
    {"id": "db02", "seq": 2, "title": "关系数据库模型",           "level": "入门", "module": "基础理论"},
    {"id": "db03", "seq": 3, "title": "SQL语言基础",              "level": "基础", "module": "SQL语言"},
    {"id": "db04", "seq": 4, "title": "数据查询与连接",           "level": "基础", "module": "SQL语言"},
    {"id": "db05", "seq": 5, "title": "数据操纵与控制",           "level": "基础", "module": "SQL语言"},
    {"id": "db06", "seq": 6, "title": "关系数据库设计理论",       "level": "进阶", "module": "设计与优化"},
    {"id": "db07", "seq": 7, "title": "数据库设计案例",           "level": "进阶", "module": "设计与优化"},
    {"id": "db08", "seq": 8, "title": "数据库新技术与发展",       "level": "综合", "module": "新技术"},
]

SEED_DATABASE_ENRICHED = [
    {"id": "db01", "title": "数据库系统概述", "level": "入门", "module": "基础理论",
     "keywords": ["数据库","DBMS","数据模型","三级模式"], "objectives": ["理解数据库的基本概念", "掌握数据模型的分类", "了解数据库管理系统功能"],
     "key_points": ["数据库与文件系统的区别", "三级模式两级映像", "数据独立性"], "difficulties": ["三级模式结构理解", "数据抽象过程"],
     "relations": {"prerequisites": [], "leads_to": ["db02"]}, "practice_questions": [{"q": "数据库的三级模式结构是什么？", "a": "外模式、概念模式、内模式"}], "code_examples": []},
    {"id": "db02", "title": "关系数据库模型", "level": "入门", "module": "基础理论",
     "keywords": ["关系","元组","属性","键","完整性"], "objectives": ["理解关系模型的基本概念", "掌握关系完整性约束"],
     "key_points": ["关系数据结构", "实体完整性/参照完整性/用户定义完整性", "候选键/主键/外键"], "difficulties": ["参照完整性约束", "关系代数运算"],
     "relations": {"prerequisites": ["db01"], "leads_to": ["db03"]}, "practice_questions": [{"q": "主键和外键的作用分别是什么？", "a": "主键唯一标识记录，外键建立表间联系"}], "code_examples": []},
    {"id": "db03", "title": "SQL语言基础", "level": "基础", "module": "SQL语言",
     "keywords": ["SQL","DDL","DML","CREATE","INSERT"], "objectives": ["掌握SQL数据定义语言", "掌握SQL数据操纵语言"],
     "key_points": ["CREATE TABLE建表", "INSERT插入数据", "数据类型与约束"], "difficulties": ["约束条件的设置", "表间关联建立"],
     "relations": {"prerequisites": ["db02"], "leads_to": ["db04"]}, "practice_questions": [{"q": "写出创建学生表的SQL语句", "a": "CREATE TABLE Student(...)"}], "code_examples": ["CREATE TABLE Student (id INT PRIMARY KEY, name VARCHAR(50))"]},
    {"id": "db04", "title": "数据查询与连接", "level": "基础", "module": "SQL语言",
     "keywords": ["SELECT","JOIN","WHERE","GROUP BY"], "objectives": ["掌握SELECT查询语句", "掌握多表连接查询"],
     "key_points": ["SELECT语法结构", "INNER/LEFT/RIGHT JOIN", "聚合函数与分组"], "difficulties": ["多表连接逻辑", "子查询嵌套"],
     "relations": {"prerequisites": ["db03"], "leads_to": ["db05"]}, "practice_questions": [{"q": "INNER JOIN和LEFT JOIN的区别？", "a": "INNER只返回匹配行，LEFT返回左表所有行"}], "code_examples": ["SELECT s.name, sc.score FROM Student s JOIN Score sc ON s.id=sc.student_id"]},
    {"id": "db05", "title": "数据操纵与控制", "level": "基础", "module": "SQL语言",
     "keywords": ["UPDATE","DELETE","事务","权限"], "objectives": ["掌握数据更新操作", "理解事务管理"],
     "key_points": ["UPDATE/DELETE使用", "事务ACID特性", "COMMIT/ROLLBACK"], "difficulties": ["事务隔离级别", "并发控制"],
     "relations": {"prerequisites": ["db04"], "leads_to": ["db06"]}, "practice_questions": [{"q": "事务的ACID特性是什么？", "a": "原子性、一致性、隔离性、持久性"}], "code_examples": ["BEGIN TRANSACTION; UPDATE ...; COMMIT;"]},
    {"id": "db06", "title": "关系数据库设计理论", "level": "进阶", "module": "设计与优化",
     "keywords": ["范式","函数依赖","ER图","规范化"], "objectives": ["理解函数依赖概念", "掌握ER图设计方法"],
     "key_points": ["1NF/2NF/3NF/BCNF", "函数依赖与传递依赖", "ER图转关系模式"], "difficulties": ["范式分解", "多值依赖"],
     "relations": {"prerequisites": ["db02"], "leads_to": ["db07"]}, "practice_questions": [{"q": "第三范式的定义是什么？", "a": "满足2NF且无传递函数依赖"}], "code_examples": []},
    {"id": "db07", "title": "数据库设计案例", "level": "进阶", "module": "设计与优化",
     "keywords": ["需求分析","概念设计","逻辑设计","物理设计"], "objectives": ["掌握数据库设计完整流程", "能独立完成小型系统数据库设计"],
     "key_points": ["设计六步骤", "需求分析方法", "物理设计考虑"], "difficulties": ["需求分析到概念模型的转换", "索引策略选择"],
     "relations": {"prerequisites": ["db06"], "leads_to": ["db08"]}, "practice_questions": [{"q": "数据库设计分为哪几个阶段？", "a": "需求分析、概念设计、逻辑设计、物理设计、实施、运维"}], "code_examples": []},
    {"id": "db08", "title": "数据库新技术与发展", "level": "综合", "module": "新技术",
     "keywords": ["NoSQL","大数据","分布式","云数据库"], "objectives": ["了解NoSQL数据库", "了解大数据技术栈"],
     "key_points": ["NoSQL四大类型", "Hadoop生态系统", "云数据库服务"], "difficulties": ["CAP定理理解", "HBASE与关系数据库对比"],
     "relations": {"prerequisites": ["db07"], "leads_to": []}, "practice_questions": [{"q": "NoSQL数据库的四大类型？", "a": "键值、文档、列族、图"}], "code_examples": []},
]


# ===== 种子模板：网页设计与制作（8章）=====
WEB_MODULE = {
    "web01": "HTML基础", "web02": "HTML基础",
    "web03": "CSS样式", "web04": "CSS样式",
    "web05": "布局技术", "web06": "布局技术",
    "web07": "JavaScript", "web08": "综合实战",
}

SEED_WEB_CHAPTERS = [
    {"id": "web01", "seq": 1, "title": "HTML5基础",               "level": "入门", "module": "HTML基础"},
    {"id": "web02", "seq": 2, "title": "HTML标签与表单",          "level": "入门", "module": "HTML基础"},
    {"id": "web03", "seq": 3, "title": "CSS基础与选择器",         "level": "基础", "module": "CSS样式"},
    {"id": "web04", "seq": 4, "title": "CSS盒模型与样式",         "level": "基础", "module": "CSS样式"},
    {"id": "web05", "seq": 5, "title": "Flex弹性布局",            "level": "基础", "module": "布局技术"},
    {"id": "web06", "seq": 6, "title": "Grid网格布局",            "level": "进阶", "module": "布局技术"},
    {"id": "web07", "seq": 7, "title": "JavaScript基础",           "level": "进阶", "module": "JavaScript"},
    {"id": "web08", "seq": 8, "title": "综合项目：企业官网",       "level": "综合", "module": "综合实战"},
]

SEED_WEB_ENRICHED = [
    {"id": "web01", "title": "HTML5基础", "level": "入门", "module": "HTML基础",
     "keywords": ["HTML","标签","文档结构","H5"], "objectives": ["掌握HTML文档基本结构", "了解HTML5新特性"],
     "key_points": ["HTML文档结构", "常用块级/行内标签", "HTML5语义化标签"], "difficulties": ["语义化标签的选择", "浏览器兼容性"],
     "relations": {"prerequisites": [], "leads_to": ["web02"]}, "practice_questions": [{"q": "HTML5新增了哪些语义化标签？", "a": "header, nav, article, section, footer等"}], "code_examples": ["<!DOCTYPE html><html><head><meta charset='UTF-8'><title>示例</title></head><body></body></html>"]},
    {"id": "web02", "title": "HTML标签与表单", "level": "入门", "module": "HTML基础",
     "keywords": ["表单","input","验证","提交"], "objectives": ["掌握常用表单元素", "了解表单验证"],
     "key_points": ["form/input/select/textarea", "输入类型(type)", "表单验证属性"], "difficulties": ["表单数据提交方式", "HTML5表单验证"],
     "relations": {"prerequisites": ["web01"], "leads_to": ["web03"]}, "practice_questions": [{"q": "GET和POST提交方式的区别？", "a": "GET数据在URL中，POST在请求体中"}], "code_examples": ["<form method='POST'><input type='text' name='username' required></form>"]},
    {"id": "web03", "title": "CSS基础与选择器", "level": "基础", "module": "CSS样式",
     "keywords": ["CSS","选择器","样式","层叠"], "objectives": ["掌握CSS基本语法", "熟练使用各类选择器"],
     "key_points": ["CSS引入方式", "基本/组合/伪类选择器", "层叠与优先级"], "difficulties": ["选择器优先级计算", "伪类使用场景"],
     "relations": {"prerequisites": ["web01"], "leads_to": ["web04"]}, "practice_questions": [{"q": "CSS选择器的优先级如何计算？", "a": "!important > 行内 > ID > 类/伪类 > 标签 > 通配"}], "code_examples": [".container .item:hover { color: red; }"]},
    {"id": "web04", "title": "CSS盒模型与样式", "level": "基础", "module": "CSS样式",
     "keywords": ["盒模型","边距","边框","背景"], "objectives": ["理解CSS盒模型", "掌握常用样式属性"],
     "key_points": ["content/padding/border/margin", "标准盒模型与IE盒模型", "背景与渐变"], "difficulties": ["外边距折叠", "box-sizing应用"],
     "relations": {"prerequisites": ["web03"], "leads_to": ["web05"]}, "practice_questions": [{"q": "box-sizing: border-box的作用？", "a": "让width包含padding和border"}], "code_examples": ["* { box-sizing: border-box; }"]},
    {"id": "web05", "title": "Flex弹性布局", "level": "基础", "module": "布局技术",
     "keywords": ["Flex","弹性盒","主轴","对齐"], "objectives": ["掌握Flex布局核心概念", "能完成常见页面布局"],
     "key_points": ["flex-direction", "justify-content/align-items", "flex-wrap"], "difficulties": ["主轴与交叉轴方向理解", "Flex项目属性"],
     "relations": {"prerequisites": ["web04"], "leads_to": ["web06"]}, "practice_questions": [{"q": "Flex容器justify-content: center的作用？", "a": "主轴方向居中对齐"}], "code_examples": [".container { display: flex; justify-content: center; }"]},
    {"id": "web06", "title": "Grid网格布局", "level": "进阶", "module": "布局技术",
     "keywords": ["Grid","网格","行列","区域"], "objectives": ["掌握Grid布局基础", "理解Grid与Flex的区别"],
     "key_points": ["grid-template-columns/rows", "grid-area", "响应式Grid"], "difficulties": ["Grid行列命名", "Grid/Flex适用场景"],
     "relations": {"prerequisites": ["web05"], "leads_to": ["web07"]}, "practice_questions": [{"q": "Grid和Flex布局各自适用于什么场景？", "a": "Grid适合二维布局，Flex适合一维布局"}], "code_examples": [".grid { display: grid; grid-template-columns: repeat(3, 1fr); }"]},
    {"id": "web07", "title": "JavaScript基础", "level": "进阶", "module": "JavaScript",
     "keywords": ["JavaScript","变量","函数","DOM"], "objectives": ["掌握JavaScript基本语法", "能操作DOM元素"],
     "key_points": ["变量声明(let/const)", "函数与箭头函数", "DOM操作与事件"], "difficulties": ["异步编程基础", "事件冒泡与捕获"],
     "relations": {"prerequisites": ["web04"], "leads_to": ["web08"]}, "practice_questions": [{"q": "let和const的区别？", "a": "let可重新赋值，const不可重新赋值"}], "code_examples": ["document.getElementById('btn').addEventListener('click', ()=>alert('Hello'))"]},
    {"id": "web08", "title": "综合项目：企业官网", "level": "综合", "module": "综合实战",
     "keywords": ["项目实战","响应式","部署"], "objectives": ["综合运用HTML/CSS/JS完成项目", "掌握响应式设计"],
     "key_points": ["页面结构规划", "响应式媒体查询", "GitHub Pages部署"], "difficulties": ["移动端适配", "跨浏览器兼容"],
     "relations": {"prerequisites": ["web07"], "leads_to": []}, "practice_questions": [{"q": "响应式设计的核心思路？", "a": "使用弹性布局+媒体查询+相对单位"}], "code_examples": ["@media (max-width: 768px) { ... }"]},
]


# ===== 课程模板注册表 =====
# 新建课程时可选模板
COURSE_TEMPLATES = [
    {
        "name": "Python程序设计",
        "description": "12章完整Python编程课程，覆盖基础语法到面向对象",
        "chapters": SEED_PYTHON_CHAPTERS,
        "enriched": None,  # 使用已有SEED_PYTHON_CHAPTERS_ENRICHED
    },
    {
        "name": "数据库原理与应用",
        "description": "8章数据库课程，从关系模型到SQL到NoSQL",
        "chapters": SEED_DATABASE_CHAPTERS,
        "enriched": SEED_DATABASE_ENRICHED,
    },
    {
        "name": "网页设计与制作",
        "description": "8章前端开发课程，HTML+CSS+JS+综合项目",
        "chapters": SEED_WEB_CHAPTERS,
        "enriched": SEED_WEB_ENRICHED,
    },
]


def seed_course_template(course_id, template_name):
    """将指定模板的章节数据写入数据库"""
    for tmpl in COURSE_TEMPLATES:
        if tmpl["name"] == template_name:
            for ch in tmpl["chapters"]:
                enriched = None
                if tmpl["enriched"]:
                    for e in tmpl["enriched"]:
                        if e["id"] == ch["id"]:
                            enriched = e
                            break
                if enriched:
                    database.create_course_chapter(
                        course_id=course_id,
                        chapter_id=ch["id"],
                        seq=ch["seq"],
                        title=ch["title"],
                        level=ch["level"],
                        module=ch["module"],
                        keywords=enriched.get("keywords", []),
                        objectives=enriched.get("objectives", []),
                        key_points=enriched.get("key_points", []),
                        difficulties=enriched.get("difficulties", []),
                        meta_json={"relations": enriched.get("relations", {}),
                                   "practice_questions": enriched.get("practice_questions", []),
                                   "code_examples": enriched.get("code_examples", [])},
                    )
                else:
                    database.create_course_chapter(
                        course_id=course_id,
                        chapter_id=ch["id"],
                        seq=ch["seq"],
                        title=ch["title"],
                        level=ch["level"],
                        module=ch["module"],
                    )
            return True
    return False


# ===== 运行时函数 =====

def get_course_chapters(course_id):
    return database.get_course_chapters(course_id)


def get_course_chapter(course_id, chapter_id):
    return database.get_course_chapter(course_id, chapter_id)


def get_chapter(course_id, chapter_id):
    return database.get_course_chapter(course_id, chapter_id)


def get_all_chapters(course_id=None):
    return database.get_course_chapters(course_id)


def get_chapter_text(course_id, chapter_id):
    ch = database.get_course_chapter(course_id, chapter_id)
    if not ch:
        return ""
    texts = [f"# {ch['title']}", f"级别：{ch['level']}", f"模块：{ch['module']}"]
    for k in ("objectives", "key_points", "difficulties"):
        if ch.get(k):
            texts.append(f"\n## {k}\n" + "\n".join(f"- {i}" for i in ch[k]))
    return "\n".join(texts)


def search_by_keyword(keyword, course_id=None):
    results = []
    chapters = database.get_course_chapters(course_id) if course_id else []
    for ch in chapters:
        score = 0
        if keyword in ch["title"]:
            score += 10
        for field in ("keywords", "objectives", "key_points", "difficulties"):
            vals = ch.get(field, [])
            if isinstance(vals, str):
                try:
                    import json
                    vals = json.loads(vals)
                except:
                    vals = []
            for v in vals:
                if keyword in v:
                    score += 3
        if score > 0:
            results.append({"chapter_id": ch["chapter_id"], "title": ch["title"],
                          "score": score, "module": ch.get("module", "")})
    results.sort(key=lambda x: -x["score"])
    return results


def get_course_modules(course_id):
    return database.get_course_modules(course_id)


def get_seed_chapter(chapter_id):
    """获取Python模板的某章种子数据（兼容旧调用）"""
    for ch in SEED_PYTHON_CHAPTERS:
        if ch["id"] == chapter_id:
            return ch
    return None
