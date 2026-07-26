# -*- coding: utf-8 -*-
"""
全局配置
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置"""
    # 平台版本（每次重大升级递增，展示于页脚与 /api/version）
    PLATFORM_VERSION = "4.0"
    PLATFORM_NAME = "AI智能教学平台"

    SECRET_KEY = os.environ.get("SECRET_KEY", "teacher-ai-competition-2026")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_DIR = os.path.join(DATA_DIR, "db")
    DB_PATH = os.path.join(DB_DIR, "ai_platform.db")
    KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
    VECTOR_DIR = os.path.join(DATA_DIR, "vectors")
    VIDEO_DIR = os.path.join(BASE_DIR, "static", "videos")

    # DeepSeek API
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL_CHAT = os.environ.get("DEEPSEEK_MODEL_CHAT", "deepseek-chat")
    DEEPSEEK_MODEL_REASONER = os.environ.get("DEEPSEEK_MODEL_REASONER", "deepseek-reasoner")

    # 模型替代（当DeepSeek不可用时）
    ALTERNATE_API_KEY = os.environ.get("ALTERNATE_API_KEY", "")
    ALTERNATE_BASE_URL = os.environ.get("ALTERNATE_BASE_URL", "")
    ALTERNATE_MODEL = os.environ.get("ALTERNATE_MODEL", "")

    # D-ID API（数字人备选方案）
    DID_API_KEY = os.environ.get("DID_API_KEY", "")
    DID_API_URL = "https://api.d-id.com/talks"

    # TTS配置（本地GPT-SoVITS服务地址，如部署）
    TTS_SERVICE_URL = os.environ.get("TTS_SERVICE_URL", "")

    # RAG配置
    CHROMA_PERSIST_DIR = os.path.join(DATA_DIR, "chroma_db")
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    RAG_TOP_K = 5
    RAG_SIMILARITY_THRESHOLD = 0.4

    # 课程信息
    COURSE_NAME = "Python程序设计"
    COURSE_CHAPTER_COUNT = 12
    SCHOOL_NAME = "宜宾工业职业技术学院"
    DEPARTMENT = "数字经济学院"
    TEACHER_NAME = "朱景峰"

    # 学生端配置
    QUIZ_QUESTIONS_PER_ROUND = 5
    MAX_WRONG_BOOK_SIZE = 50
    DIGITAL_HUMAN_CACHE_ENABLED = True
    DIGITAL_HUMAN_CACHE_DIR = os.path.join(DATA_DIR, "digital_human_cache")
