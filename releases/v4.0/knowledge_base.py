# -*- coding: utf-8 -*-
"""
课程体系数据层 V3.0
- 运行时章节/模块一律从数据库 course_chapters 读取（课程无关化）
- SEED_PYTHON_CHAPTERS 仅作为"示例课程(Python)"的种子常量，首次运行时写入 DB
"""
from config import Config
import database


# ===== 种子：Python 12章（含 module模块映射 + 图谱关系）=====
# module：用于雷达维度聚合（5维）；relations：用于知识图谱（prerequisites/leads_to）

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


SEED_PYTHON_CHAPTERS = [
    {
        "id": "ch01", "title": "第1章 Python入门与环境搭建", "level": "入门",
        "keywords": ["Python简介", "安装Python", "IDE", "PyCharm", "VS Code", "pip", "Hello World", "解释器", "交互模式"],
        "objectives": ["了解Python语言的发展历史和应用领域", "掌握Python开发环境的安装与配置", "能够编写并运行第一个Python程序", "理解Python解释器的基本工作原理"],
        "key_points": ["Python安装与环境变量配置", "pip包管理工具", "print函数基本使用", "交互模式（REPL）"],
        "difficulties": ["环境变量PATH配置", "pip源更换为国内源"],
        "practice_questions": [{"q": "Python的创始人是谁？", "a": "Guido van Rossum（吉多·范罗苏姆）"}, {"q": "pip install 命令的作用是什么？", "a": "安装Python第三方包/库"}],
        "code_examples": ['print("Hello, World!")', 'import sys; print(sys.version)'],
    },
    {
        "id": "ch02", "title": "第2章 变量与基本数据类型", "level": "入门",
        "keywords": ["变量", "数据类型", "int", "float", "str", "bool", "type", "类型转换", "input", "格式化输出"],
        "objectives": ["掌握Python变量的命名规则和赋值方式", "熟练使用int、float、str、bool四种基本数据类型", "掌握类型转换和格式化输出"],
        "key_points": ["变量命名规范（字母/下划线开头）", "type()查看类型", "int()/float()/str()类型转换", "f-string格式化"],
        "difficulties": ["float精度问题", "str和int/float的转换陷阱"],
        "practice_questions": [{"q": "name = input('请输入姓名')的返回值是什么类型？", "a": "字符串（str）类型"}, {"q": "如何将一个字符串'3.14'转为浮点数？", "a": "float('3.14')"}],
        "code_examples": ['name = input("请输入姓名：")\nprint(f"你好，{name}！")', 'num = int(input("请输入数字："))\nprint(f"{num}的平方是{num**2}")'],
    },
    {
        "id": "ch03", "title": "第3章 运算符与表达式", "level": "入门",
        "keywords": ["算术运算符", "比较运算符", "逻辑运算符", "赋值运算符", "优先级", "表达式"],
        "objectives": ["掌握Python各类运算符的使用方法", "理解运算符优先级规则", "能编写复杂的表达式"],
        "key_points": ["算术：+ - * / // % **", "比较：== != > < >= <=", "逻辑：and or not", "优先级从高到低"],
        "difficulties": ["//整除与/普通除法的区别", "and/or短路逻辑", "is与==的区别"],
        "practice_questions": [{"q": "7 // 2 的结果是多少？", "a": "3（整除，向下取整）"}, {"q": "3 > 2 and 1/0 会报错吗？", "a": "会报错，因为and两边都会评估（Python中无短路优化区别）"}],
        "code_examples": ['a, b = 10, 3\nprint(f"和={a+b}, 差={a-b}, 积={a*b}, 商={a/b:.2f}")'],
    },
    {
        "id": "ch04", "title": "第4章 条件判断与分支结构", "level": "入门",
        "keywords": ["if", "elif", "else", "条件判断", "分支", "嵌套", "三元表达式", "match-case"],
        "objectives": ["掌握if-elif-else多分支结构", "理解程序流程控制的概念", "能编写包含多重条件判断的程序"],
        "key_points": ["if单分支", "if-else双分支", "if-elif-else多分支", "条件嵌套", "三元表达式 x if cond else y"],
        "difficulties": ["缩进规范（Tab vs 空格）", "多个条件的组合逻辑", "elif vs 多个if的区别"],
        "practice_questions": [{"q": "elif和else if有什么区别？", "a": "Python中没有else if关键字，统一用elif"}],
        "code_examples": ['score = int(input("请输入成绩："))\nif score >= 90:\n    grade = "A"\nelif score >= 80:\n    grade = "B"\nelif score >= 70:\n    grade = "C"\nelif score >= 60:\n    grade = "D"\nelse:\n    grade = "F"\nprint(f"等级：{grade}")'],
    },
    {
        "id": "ch05", "title": "第5章 循环结构", "level": "基础",
        "keywords": ["for", "while", "range", "循环", "break", "continue", "else", "迭代"],
        "objectives": ["掌握for和while两种循环结构", "理解break和continue的区别", "能使用循环解决实际问题"],
        "key_points": ["for...in迭代", "range()生成序列", "while条件循环", "break退出循环", "continue跳过当次", "for-else/while-else"],
        "difficulties": ["while死循环的避免", "嵌套循环的执行顺序", "for-else的特殊语义"],
        "practice_questions": [{"q": "range(1, 10, 2)产生的序列是什么？", "a": "[1, 3, 5, 7, 9]"}, {"q": "break和continue的区别是什么？", "a": "break直接退出整个循环，continue跳过本次迭代继续下一次"}],
        "code_examples": ['# 打印九九乘法表\nfor i in range(1, 10):\n    for j in range(1, i+1):\n        print(f"{j}x{i}={i*j}", end="\\t")\n    print()'],
    },
    {
        "id": "ch06", "title": "第6章 字符串与正则表达式", "level": "基础",
        "keywords": ["字符串", "索引", "切片", "方法", "format", "join", "split", "re模块", "正则"],
        "objectives": ["掌握字符串的常用操作方法", "理解字符串的不可变性", "掌握正则表达式的基本用法"],
        "key_points": ["索引从0开始", "切片[start:end:step]", "常用方法：upper/lower/strip/split/join/find/replace", "f-string格式化", "re.match/search/findall/sub"],
        "difficulties": ["正则表达式的贪婪匹配", "中文与Unicode处理", "字符串拼接的性能"],
        "practice_questions": [{"q": "s = 'abcde'; s[1:4]的结果是什么？", "a": "'bcd'"}, {"q": "如何判断一个字符串是否是纯数字？", "a": "s.isdigit()"}],
        "code_examples": ['import re\nemail = "test@example.com"\nif re.match(r"^[\\w.-]+@[\\w.-]+\\.\\w+$", email):\n    print("合法邮箱")'],
    },
    {
        "id": "ch07", "title": "第7章 列表与元组", "level": "基础",
        "keywords": ["list", "tuple", "列表", "元组", "切片", "方法", "列表推导式", "不可变"],
        "objectives": ["掌握列表的增删改查操作", "理解列表与元组的区别和应用场景", "熟练使用列表推导式"],
        "key_points": ["列表增删：append/insert/extend/remove/pop", "列表排序：sort/sorted", "元组不可变特性", "列表推导式 [expr for x in iterable if cond]", "zip/enumerate"],
        "difficulties": ["浅拷贝与深拷贝的区别", "可变对象作为默认参数的陷阱", "列表推导式的可读性"],
        "practice_questions": [{"q": "list和tuple的主要区别是什么？", "a": "list可变（可增删改），tuple不可变（创建后不能修改）"}],
        "code_examples": ['# 列表推导式：生成1-10的平方\nsquares = [x**2 for x in range(1, 11)]\nprint(squares)'],
    },
    {
        "id": "ch08", "title": "第8章 字典与集合", "level": "基础",
        "keywords": ["dict", "set", "字典", "集合", "键值对", "哈希", "去重", "交集", "并集"],
        "objectives": ["掌握字典的键值对操作", "理解集合的去重和集合运算", "能选择合适的数据结构解决问题"],
        "key_points": ["字典创建和访问", "dict.get()安全访问", "keys/values/items迭代", "集合的特点：无序不重复", "集合运算：交集&、并集|、差集-"],
        "difficulties": ["dict的键必须是不可变类型", "嵌套字典的访问", "字典的遍历效率"],
        "practice_questions": [{"q": "d = {}; d[[1,2,3]] = 'value' 会报什么错误？", "a": "TypeError，因为list是可变类型不能作为字典的键"}],
        "code_examples": ['students = {"张三": 85, "李四": 92}\nfor name, score in students.items():\n    print(f"{name}: {score}分")'],
    },
    {
        "id": "ch09", "title": "第9章 函数与模块", "level": "进阶",
        "keywords": ["def", "函数", "参数", "return", "lambda", "模块", "import", "作用域", "装饰器"],
        "objectives": ["掌握函数的定义与调用", "理解位置参数、默认参数、关键字参数的区别", "了解模块化和代码复用思想"],
        "key_points": ["def定义函数", "参数类型：位置/默认/可变/关键字", "return返回值", "全局变量与局部变量", "lambda匿名函数", "import模块导入", "__name__ == '__main__'"],
        "difficulties": ["可变默认参数陷阱", "global与nonlocal关键字", "递归的理解与调试", "装饰器的执行顺序"],
        "practice_questions": [{"q": "lambda x, y: x + y 的含义是什么？", "a": "一个匿名函数，接收两个参数x和y，返回它们的和"}],
        "code_examples": ['def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        print(a, end=" ")\n        a, b = b, a + b\nfibonacci(10)'],
    },
    {
        "id": "ch10", "title": "第10章 文件操作与异常处理", "level": "进阶",
        "keywords": ["open", "文件读写", "with", "路径", "try", "except", "finally", "异常", "raise"],
        "objectives": ["掌握文件的读写操作", "熟练使用with语句管理资源", "理解异常处理机制"],
        "key_points": ["open('file', 'r/w/a')", "read/readline/readlines", "with自动关闭", "try-except-else-finally", "常见异常类型：ValueError/TypeError/FileNotFoundError"],
        "difficulties": ["相对路径与绝对路径", "文件编码问题（中文乱码）", "自定义异常的使用场景"],
        "practice_questions": [{"q": "with open('test.txt', 'r', encoding='utf-8') as f 的作用是什么？", "a": "以只读模式打开文件，指定UTF-8编码，并在代码块结束后自动关闭文件"}],
        "code_examples": ['try:\n    with open("data.txt", "r", encoding="utf-8") as f:\n        content = f.read()\n        print(content)\nexcept FileNotFoundError:\n    print("文件不存在")'],
    },
    {
        "id": "ch11", "title": "第11章 面向对象编程（OOP）", "level": "进阶",
        "keywords": ["class", "对象", "继承", "多态", "封装", "__init__", "self", "属性", "方法", "super"],
        "objectives": ["理解面向对象的核心概念：封装、继承、多态", "掌握类的定义和对象的创建", "了解Python中的特殊方法（魔术方法）"],
        "key_points": ["class定义类", "__init__初始化", "self指代实例", "继承和super()", "私有属性_/_ _", "静态方法@staticmethod", "类方法@classmethod", "魔术方法__str__/__repr__/__len__"],
        "difficulties": ["self的本质和作用", "多继承的MRO（方法解析顺序）", "类变量与实例变量的区别", "property装饰器"],
        "practice_questions": [{"q": "class Dog(Animal)中Dog的父类是什么？", "a": "Animal"}, {"q": "self参数代表什么？", "a": "self代表类的实例对象本身"}],
        "code_examples": ['class Student:\n    def __init__(self, name, score):\n        self.name = name\n        self.score = score\n\n    def show(self):\n        return f"{self.name} - {self.score}分"\n\ns1 = Student("张三", 90)\nprint(s1.show())'],
    },
    {
        "id": "ch12", "title": "第12章 综合项目实战", "level": "综合",
        "keywords": ["项目", "综合", "实战", "爬虫", "GUI", "数据分析", "系统设计", "调试"],
        "objectives": ["综合运用所学知识完成完整项目", "掌握基本的软件开发流程", "培养代码调试和问题解决能力"],
        "key_points": ["需求分析→设计→编码→测试→部署", "requests库网页爬虫", "tkinter简单GUI", "CSV/JSON数据处理", "项目结构组织"],
        "difficulties": ["项目架构设计", "异常和边界条件的处理", "代码可维护性"],
        "practice_questions": [{"q": "综合项目开发的基本流程是什么？", "a": "需求分析→概要设计→详细设计→编码实现→测试→部署维护"}],
        "code_examples": ['import json\ndata = {"name": "Python", "version": "3.13"}\nwith open("config.json", "w", encoding="utf-8") as f:\n    json.dump(data, f, ensure_ascii=False, indent=2)'],
    },
]


def _enrich_seed(ch):
    """给种子章节补充 module / relations 字段"""
    cid = ch["id"]
    enriched = dict(ch)
    enriched["module"] = _PY_MODULE.get(cid, "")
    enriched["relations"] = _PY_RELATIONS.get(cid, {"prerequisites": [], "leads_to": []})
    return enriched


SEED_PYTHON_CHAPTERS_ENRICHED = [_enrich_seed(ch) for ch in SEED_PYTHON_CHAPTERS]


# ===== 运行时：一律从数据库读取（课程无关化）=====

def _resolve_course(course_id):
    if course_id:
        return course_id
    return database.get_first_course_id()


def get_course_chapters(course_id):
    """从 DB 读取某课程的章节列表（按 seq 排序）"""
    return database.get_course_chapters(course_id)


def get_course_chapter(course_id, chapter_id):
    """从 DB 读取单章；DB 无则回退到种子"""
    ch = database.get_course_chapter(course_id, chapter_id)
    if ch:
        return ch
    for s in SEED_PYTHON_CHAPTERS_ENRICHED:
        if s["id"] == chapter_id:
            return s
    return None


def get_chapter(chapter_id, course_id=None):
    """兼容旧调用：course_id 缺省时解析为首个课程"""
    return get_course_chapter(_resolve_course(course_id), chapter_id)


def get_all_chapters(course_id=None):
    """兼容旧调用：返回某课程的全部章节（不含代码）"""
    cid = _resolve_course(course_id)
    rows = database.get_course_chapters(cid)
    if rows:
        return [{k: v for k, v in r.items() if k not in ("id", "course_id")} for r in rows]
    return [{k: v for k, v in ch.items() if k != "code_examples"} for ch in SEED_PYTHON_CHAPTERS_ENRICHED]


def get_chapter_text(course_id, chapter_id):
    """获取章节文本表示（用于 RAG 向量化 / 讲解）"""
    ch = get_course_chapter(course_id, chapter_id)
    if not ch:
        return ""
    keywords = ch.get("keywords", [])
    objectives = ch.get("objectives", [])
    key_points = ch.get("key_points", [])
    difficulties = ch.get("difficulties", [])
    if isinstance(keywords, str):
        import json as _json
        keywords = _json.loads(keywords)
        objectives = _json.loads(ch.get("objectives", "[]"))
        key_points = _json.loads(ch.get("key_points", "[]"))
        difficulties = _json.loads(ch.get("difficulties", "[]"))
    parts = [
        f"章节：{ch['title']}",
        f"级别：{ch.get('level', '')}",
        f"关键词：{', '.join(keywords)}",
        f"教学目标：{'；'.join(objectives)}",
        f"重点内容：{'；'.join(key_points)}",
        f"难点：{'；'.join(difficulties)}",
    ]
    return "\n".join(parts)


def search_by_keyword(keyword, course_id=None):
    """按关键词搜索某课程的章节"""
    cid = _resolve_course(course_id)
    chapters = get_course_chapters(cid) or SEED_PYTHON_CHAPTERS_ENRICHED
    results = []
    kw_lower = keyword.lower()
    for ch in chapters:
        text = " ".join(ch.get("keywords", [])) + " " + ch.get("title", "")
        if kw_lower in text.lower():
            results.append({
                "chapter_id": ch["id"],
                "chapter_title": ch["title"],
                "level": ch.get("level", ""),
            })
    return results


def get_course_modules(course_id):
    """返回课程去重模块列表（雷达维度）"""
    return database.get_course_modules(course_id)


def get_seed_chapter(chapter_id):
    for s in SEED_PYTHON_CHAPTERS_ENRICHED:
        if s["id"] == chapter_id:
            return s
    return None
