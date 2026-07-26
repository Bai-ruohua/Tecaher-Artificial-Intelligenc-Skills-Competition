# -*- coding: utf-8 -*-
"""启动脚本 - 从 src/ 引入 Flask 应用并启动"""
import os, sys

# 将 src/ 加入 Python 路径
_src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
