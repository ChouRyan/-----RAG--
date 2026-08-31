"""
FastAPI 应用入口
企业知识库 RAG 系统主服务
"""

from dotenv import load_dotenv
load_dotenv()  # 最早加载 .env，确保 HF_ENDPOINT 等环境变量生效

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.api import upload, chat

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[DIR] Upload: {settings.UPLOAD_DIR}")
    print(f"[DIR] Chroma: {settings.CHROMA_DIR}")
    yield
    print("[STOP] Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 RAG 技术的企业知识库问答系统",
    lifespan=lifespan,
)

# ===== CORS 配置 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 注册路由 =====
app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/", tags=["根路径"])
async def root():
    """API 根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "upload": "/api/documents/upload",
            "chat": "/api/chat/",
            "health": "/api/chat/health",
        },
    }
