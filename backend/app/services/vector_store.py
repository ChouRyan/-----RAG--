"""
向量存储服务
基于 Chroma 实现文档的向量存储和检索
使用本地 HuggingFace Embedding 模型
"""

import uuid
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.config import get_settings

settings = get_settings()


class VectorStoreService:
    """向量存储服务：管理 Chroma 向量数据库"""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self._vector_store = None
        self._chroma_client = None

    @property
    def chroma_client(self) -> chromadb.PersistentClient:
        """获取 Chroma 客户端单例"""
        if self._chroma_client is None:
            self._chroma_client = chromadb.PersistentClient(
                path=str(settings.CHROMA_DIR)
            )
        return self._chroma_client

    @property
    def vector_store(self) -> Chroma:
        """获取向量存储单例"""
        if self._vector_store is None:
            self._vector_store = Chroma(
                client=self.chroma_client,
                collection_name="knowledge_base",
                embedding_function=self.embeddings,
            )
        return self._vector_store

    def add_documents(self, documents: list[Document]) -> list[str]:
        """
        将文档添加到向量存储

        Args:
            documents: LangChain Document 列表

        Returns:
            文档 ID 列表
        """
        ids = [doc.metadata.get("chunk_id", str(uuid.uuid4())) for doc in documents]
        self.vector_store.add_documents(documents=documents, ids=ids)
        return ids

    def delete_by_source(self, source: str) -> int:
        """
        根据来源文件名删除所有相关文档

        Args:
            source: 来源文件名

        Returns:
            删除的文档数量
        """
        collection = self.chroma_client.get_collection("knowledge_base")
        results = collection.get(where={"source": source})
        if results["ids"]:
            collection.delete(ids=results["ids"])
        return len(results["ids"])

    def similarity_search(
        self, query: str, top_k: int = None, filter_dict: dict = None
    ) -> list[tuple[Document, float]]:
        """
        相似度检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            (Document, score) 元组列表
        """
        k = top_k or settings.RETRIEVER_TOP_K
        results = self.vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter=filter_dict,
        )
        return results

    def get_retriever(self, top_k: int = None, filter_dict: dict = None):
        """获取 LangChain Retriever 对象"""
        k = top_k or settings.RETRIEVER_TOP_K
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )

    def get_collection_stats(self) -> dict:
        """获取向量存储统计信息"""
        try:
            collection = self.chroma_client.get_collection("knowledge_base")
            count = collection.count()

            all_data = collection.get(include=["metadatas"])
            sources = set()
            for meta in all_data["metadatas"]:
                if meta and "source" in meta:
                    sources.add(meta["source"])

            return {
                "total_chunks": count,
                "total_documents": len(sources),
                "sources": list(sources),
            }
        except Exception:
            return {"total_chunks": 0, "total_documents": 0, "sources": []}

    def clear_all(self):
        """清空所有数据"""
        try:
            self.chroma_client.delete_collection("knowledge_base")
        except Exception:
            pass
        self._vector_store = None
