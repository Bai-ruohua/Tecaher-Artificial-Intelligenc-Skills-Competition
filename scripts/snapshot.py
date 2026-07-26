import os, shutil, glob

BASE = r"C:\Users\Administrator\WorkBuddy\Tecaher-Artificial-Intelligenc-Skills-Competition"
DST = os.path.join(BASE, "releases", "v4.0")

# 快照：复制整个 src/ tree + 静态/模板/文档
src_items = [
    "src",          # 所有 Python 源码
    "templates",    # HTML 模板
    "static",       # CSS/JS
    "docs",         # 文档
]

root_files = [
    "run.py", "requirements.txt", ".env",
    "CHANGELOG.md", "overview.md",
    "项目实施梳理报告.md",
]

# 清理旧目标
if os.path.exists(DST):
    shutil.rmtree(DST)
os.makedirs(DST)

for item in src_items:
    s = os.path.join(BASE, item)
    if os.path.isdir(s):
        shutil.copytree(s, os.path.join(DST, item), dirs_exist_ok=True)

for f in root_files:
    fp = os.path.join(BASE, f)
    if os.path.exists(fp):
        shutil.copy2(fp, os.path.join(DST, f))

print("v4.0 snapshot ->", DST)
total = sum(len(files) for _, _, files in os.walk(DST))
print("total files:", total)
