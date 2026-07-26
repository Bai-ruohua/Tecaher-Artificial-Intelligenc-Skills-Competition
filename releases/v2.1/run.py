# -*- coding: utf-8 -*-
"""启动脚本 - 解决 __main__ 模块名导致的路由问题"""
import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
