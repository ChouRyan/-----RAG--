"""
应用配置模块
集中管理所有配置项，支持环境变量覆盖
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # ===== 应用基础配置 =====
    APP_NAME: str = "企业知识库 RAG 系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ===== 路径配置 =====
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma"

    # ===== 文档处理配置 =====
    CHUNK_SIZE: int = 500  # 文本分块大小（字符数）
    CHUNK_OVERLAP: int = 50  # 分块重叠字符数
    MAX_FILE_SIZE_MB: int = 50  # 最大上传文件大小 (MB)
    SUPPORTED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md"]

    # ===== Embedding 配置（本地 HuggingFace 模型） =====
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"

    # ===== LLM 配置 =====
    LLM_MODEL: str = "mimo-v2.5-pro"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048

    # ===== 检索配置 =====
    RETRIEVER_TOP_K: int = 10  # 初始检索返回文档数
    RERANK_TOP_N: int = 5  # 重排序后保留文档数
    SIMILARITY_THRESHOLD: float = 0.5  # 相似度阈值

    # ===== Reranker 配置 =====
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"
    USE_RERANKER: bool = True

    # ===== 查询改写配置 =====
    USE_QUERY_REWRITE: bool = True
    QUERY_REWRITE_NUM: int = 3  # 改写查询数量

    # ===== API Keys =====
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    settings = Settings()
    # 确保目录存在
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return settings
