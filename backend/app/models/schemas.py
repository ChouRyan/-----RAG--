"""
数据模型定义
定义 API 请求/响应的 Pydantic 模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ===== 枚举类型 =====

class DocStatus(str, Enum):
    """文档处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===== 请求模型 =====

class ChatRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="检索文档数量")
    use_rerank: Optional[bool] = Field(None, description="是否启用重排序")
    use_rewrite: Optional[bool] = Field(None, description="是否启用查询改写")
    session_id: Optional[str] = Field(None, description="会话ID，用于多轮对话")


class DocumentFilter(BaseModel):
    """文档过滤条件"""
    keyword: Optional[str] = None
    status: Optional[DocStatus] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ===== 响应模型 =====

class SourceChunk(BaseModel):
    """引用来源片段"""
    content: str = Field(..., description="文本内容")
    source: str = Field(..., description="来源文件名")
    page: Optional[int] = Field(None, description="页码")
    score: float = Field(..., description="相关性分数")
    chunk_id: str = Field(..., description="分块ID")


class ChatResponse(BaseModel):
    """问答响应"""
    answer: str = Field(..., description="回答内容")
    sources: list[SourceChunk] = Field(default_factory=list, description="引用来源")
    rewritten_queries: Optional[list[str]] = Field(None, description="改写后的查询")
    processing_time: float = Field(..., description="处理耗时(秒)")
    session_id: Optional[str] = Field(None, description="会话ID")


class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str
    filename: str
    file_size: int
    file_type: str
    chunk_count: int
    status: DocStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None


class UploadResponse(BaseModel):
    """上传响应"""
    doc_id: str
    filename: str
    chunk_count: int
    message: str


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    documents: list[DocumentInfo]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    doc_count: int
    chunk_count: int


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    code: Optional[str] = None
