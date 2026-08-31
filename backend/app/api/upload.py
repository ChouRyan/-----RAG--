"""
文档上传 API
处理文档的上传、解析、入库
"""

import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import get_settings
from app.models.schemas import UploadResponse, DocumentInfo, DocumentListResponse, DocStatus
from app.services.document_parser import DocumentParser
from app.services.vector_store import VectorStoreService

settings = get_settings()
router = APIRouter(prefix="/documents", tags=["文档管理"])

# 服务实例
parser = DocumentParser()
vector_store = VectorStoreService()

# 内存中的文档元数据存储（生产环境应使用数据库）
documents_db: dict[str, DocumentInfo] = {}


@router.post("/upload", response_model=UploadResponse, summary="上传文档")
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档到知识库

    支持格式：PDF、DOCX、TXT、Markdown
    """
    # 校验文件类型
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {suffix}，支持: {settings.SUPPORTED_EXTENSIONS}",
        )

    # 校验文件大小
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {file_size_mb:.1f}MB > {settings.MAX_FILE_SIZE_MB}MB",
        )

    # 保存文件
    doc_id = str(uuid.uuid4())
    file_path = settings.UPLOAD_DIR / f"{doc_id}{suffix}"
    file_path.write_bytes(content)

    # 创建文档记录
    doc_info = DocumentInfo(
        doc_id=doc_id,
        filename=file.filename,
        file_size=len(content),
        file_type=suffix,
        chunk_count=0,
        status=DocStatus.PROCESSING,
        created_at=datetime.now(),
    )
    documents_db[doc_id] = doc_info

    # 解析并入库
    try:
        chunks = parser.parse_file(file_path)
        vector_store.add_documents(chunks)

        # 更新状态
        doc_info.status = DocStatus.COMPLETED
        doc_info.chunk_count = len(chunks)
        doc_info.updated_at = datetime.now()

        return UploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            chunk_count=len(chunks),
            message=f"文档上传成功，共生成 {len(chunks)} 个文本块",
        )
    except Exception as e:
        doc_info.status = DocStatus.FAILED
        doc_info.error_message = str(e)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.get("/", response_model=DocumentListResponse, summary="获取文档列表")
async def list_documents(keyword: str = None, status: DocStatus = None):
    """获取所有已上传的文档列表"""
    docs = list(documents_db.values())

    # 过滤
    if keyword:
        docs = [d for d in docs if keyword.lower() in d.filename.lower()]
    if status:
        docs = [d for d in docs if d.status == status]

    # 按创建时间降序
    docs.sort(key=lambda d: d.created_at, reverse=True)

    return DocumentListResponse(total=len(docs), documents=docs)


@router.get("/{doc_id}", response_model=DocumentInfo, summary="获取文档详情")
async def get_document(doc_id: str):
    """获取指定文档的详细信息"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")
    return documents_db[doc_id]


@router.delete("/{doc_id}", summary="删除文档")
async def delete_document(doc_id: str):
    """删除指定文档及其向量数据"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc_info = documents_db[doc_id]

    # 删除向量数据
    deleted_count = vector_store.delete_by_source(doc_info.filename)

    # 删除文件
    file_path = settings.UPLOAD_DIR / f"{doc_id}{doc_info.file_type}"
    if file_path.exists():
        file_path.unlink()

    # 删除记录
    del documents_db[doc_id]

    return {"message": f"文档已删除，共移除 {deleted_count} 个向量块"}
