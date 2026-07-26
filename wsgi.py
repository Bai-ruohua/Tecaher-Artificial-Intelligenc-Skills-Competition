# -*- coding: utf-8 -*-
"""
Zeabur / Gunicorn 生产环境入口
使用方式：gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from app import app as application

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
