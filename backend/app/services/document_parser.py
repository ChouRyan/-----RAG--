"""
文档解析服务
支持 PDF、DOCX、TXT、Markdown 格式的文档解析和分块
"""

import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import get_settings

settings = get_settings()


class DocumentParser:
    """文档解析器：负责将不同格式的文档解析为统一的文本块"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )

    def parse_file(self, file_path: Path) -> list[Document]:
        """
        解析文件并返回 LangChain Document 列表

        Args:
            file_path: 文件路径

        Returns:
            解析后的文档块列表
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            raw_docs = self._parse_pdf(file_path)
        elif suffix == ".docx":
            raw_docs = self._parse_docx(file_path)
        elif suffix == ".txt":
            raw_docs = self._parse_txt(file_path)
        elif suffix == ".md":
            raw_docs = self._parse_txt(file_path)  # Markdown 按纯文本解析
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

        # 分块处理
        chunks = self.text_splitter.split_documents(raw_docs)

        # 为每个 chunk 添加唯一 ID 和来源信息
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = str(uuid.uuid4())
            chunk.metadata["source"] = file_path.name
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
            chunk.metadata["created_at"] = datetime.now().isoformat()

        return chunks

    def _parse_pdf(self, file_path: Path) -> list[Document]:
        """解析 PDF 文件"""
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(str(file_path))
        docs = loader.load()

        for doc in docs:
            doc.metadata["file_type"] = "pdf"

        return docs

    def _parse_docx(self, file_path: Path) -> list[Document]:
        """解析 DOCX 文件"""
        from langchain_community.document_loaders import Docx2txtLoader

        loader = Docx2txtLoader(str(file_path))
        docs = loader.load()

        for doc in docs:
            doc.metadata["file_type"] = "docx"

        return docs

    def _parse_txt(self, file_path: Path) -> list[Document]:
        """解析 TXT / Markdown 文件"""
        content = file_path.read_text(encoding="utf-8")
        suffix = file_path.suffix.lower().lstrip(".")
        doc = Document(
            page_content=content,
            metadata={"file_type": suffix, "page": 1}
        )
        return [doc]

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """计算文件 MD5 哈希值，用于去重"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
