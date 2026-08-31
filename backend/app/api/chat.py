"""
问答对话 API
处理用户的语义问答请求
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.rag_chain import RAGChain
from app.services.vector_store import VectorStoreService
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/chat", tags=["智能问答"])

# 服务实例
rag_chain = RAGChain()
vector_store = VectorStoreService()


@router.post("/", response_model=ChatResponse, summary="智能问答")
async def chat(request: ChatRequest):
    """
    基于知识库的智能问答

    流程：查询改写 → 向量检索 → 重排序 → LLM 生成
    """
    try:
        response = await rag_chain.chat(
            question=request.question,
            top_k=request.top_k,
            use_rerank=request.use_rerank,
            use_rewrite=request.use_rewrite,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """系统健康检查"""
    try:
        stats = vector_store.get_collection_stats()
        return HealthResponse(
            status="healthy",
            version=settings.APP_VERSION,
            doc_count=stats["total_documents"],
            chunk_count=stats["total_chunks"],
        )
    except Exception:
        return HealthResponse(
            status="degraded",
            version=settings.APP_VERSION,
            doc_count=0,
            chunk_count=0,
        )
