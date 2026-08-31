"""
RAG 链服务
整合查询改写、检索、重排序、生成等环节
使用 Anthropic Claude 作为 LLM
"""

import time
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from app.config import get_settings
from app.models.schemas import ChatResponse, SourceChunk
from app.services.vector_store import VectorStoreService
from app.services.reranker import RerankerService

settings = get_settings()

# ===== Prompt 模板 =====

QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_template(
    """你是一个查询改写专家。用户的原始问题可能不够精确或完整，请生成 {num} 个改写后的查询，
以便更全面地检索相关文档。

原始问题：{question}

要求：
1. 保持原始问题的核心意图
2. 从不同角度和表述方式改写
3. 使查询更适合向量检索（语义搜索）
4. 每个查询独立一行

改写后的查询："""
)

RAG_PROMPT = ChatPromptTemplate.from_template(
    """你是一个企业知识库问答助手。请根据提供的参考资料回答用户的问题。

要求：
1. 只基于提供的参考资料回答，不要编造信息
2. 如果参考资料中没有相关信息，请明确说明
3. 在回答中适当引用来源，格式为 [来源: 文件名]
4. 回答要准确、完整、有条理

参考资料：
{context}

用户问题：{question}

请回答："""
)


def _extract_text(content) -> str:
    """从 Anthropic 响应中提取纯文本（兼容 content block 列表）"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # 优先取 type=text 的 block，没有则取所有含 text 的 block
        texts = [block.get("text", "") for block in content
                 if isinstance(block, dict) and block.get("type") == "text"]
        if not texts:
            texts = [block.get("text", "") for block in content
                     if isinstance(block, dict) and "text" in block]
        return "\n".join(t for t in texts if t)
    return str(content)


class RAGChain:
    """RAG 链：整合检索增强生成的完整流程"""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.reranker = RerankerService()
        self.llm = ChatAnthropic(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            anthropic_api_url=settings.ANTHROPIC_BASE_URL,
        )

    async def chat(
        self,
        question: str,
        top_k: int = None,
        use_rerank: bool = None,
        use_rewrite: bool = None,
    ) -> ChatResponse:
        """
        执行 RAG 问答流程

        Args:
            question: 用户问题
            top_k: 检索文档数量
            use_rerank: 是否启用重排序
            use_rewrite: 是否启用查询改写

        Returns:
            ChatResponse 包含回答、来源等信息
        """
        start_time = time.time()
        rewritten_queries = None
        k = top_k or settings.RETRIEVER_TOP_K
        should_rerank = use_rerank if use_rerank is not None else settings.USE_RERANKER
        should_rewrite = use_rewrite if use_rewrite is not None else settings.USE_QUERY_REWRITE

        # ===== Step 1: 查询改写 =====
        queries = [question]
        if should_rewrite:
            rewritten_queries = await self._rewrite_query(question)
            queries.extend(rewritten_queries)

        # ===== Step 2: 多查询检索 =====
        all_docs = await self._multi_query_retrieve(queries, top_k=k)

        # ===== Step 3: 去重 =====
        unique_docs = self._deduplicate_docs(all_docs)

        # ===== Step 4: 重排序 =====
        if should_rerank and unique_docs:
            try:
                reranked_docs = self.reranker.rerank(
                    query=question,
                    documents=unique_docs,
                    top_n=settings.RERANK_TOP_N,
                )
            except Exception:
                # 重排序失败时回退到原始排序
                reranked_docs = unique_docs[: settings.RERANK_TOP_N]
        else:
            reranked_docs = unique_docs[: settings.RERANK_TOP_N]

        # ===== Step 5: 生成回答 =====
        context = self._build_context(reranked_docs)
        answer = await self._generate_answer(question, context)

        # ===== Step 6: 构建来源信息 =====
        sources = self._build_sources(reranked_docs)

        processing_time = time.time() - start_time

        return ChatResponse(
            answer=answer,
            sources=sources,
            rewritten_queries=rewritten_queries,
            processing_time=round(processing_time, 2),
        )

    async def _rewrite_query(self, question: str) -> list[str]:
        """改写查询"""
        try:
            chain = QUERY_REWRITE_PROMPT | self.llm
            response = await asyncio.to_thread(
                chain.invoke,
                {"question": question, "num": settings.QUERY_REWRITE_NUM},
            )
            # 解析改写结果
            raw = _extract_text(response.content)
            queries = [
                q.strip()
                for q in raw.strip().split("\n")
                if q.strip() and q.strip() != question
            ]
            return queries[: settings.QUERY_REWRITE_NUM]
        except Exception:
            return []

    async def _multi_query_retrieve(
        self, queries: list[str], top_k: int
    ) -> list[tuple[Document, float]]:
        """多查询检索"""
        all_docs = []
        for query in queries:
            docs = await asyncio.to_thread(
                self.vector_store.similarity_search, query=query, top_k=top_k
            )
            all_docs.extend(docs)
        return all_docs

    def _deduplicate_docs(
        self, docs: list[tuple[Document, float]]
    ) -> list[tuple[Document, float]]:
        """基于 chunk_id 去重，保留最高分"""
        seen = {}
        for doc, score in docs:
            chunk_id = doc.metadata.get("chunk_id", "")
            if chunk_id not in seen or score > seen[chunk_id][1]:
                seen[chunk_id] = (doc, score)
        # 按分数降序排列
        return sorted(seen.values(), key=lambda x: x[1], reverse=True)

    def _build_context(self, docs: list[tuple[Document, float]]) -> str:
        """构建上下文文本"""
        context_parts = []
        for i, (doc, score) in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            page = doc.metadata.get("page", "")
            page_info = f" (第{page}页)" if page else ""
            context_parts.append(
                f"[文档{i}] 来源: {source}{page_info}\n{doc.page_content}"
            )
        return "\n\n".join(context_parts)

    async def _generate_answer(self, question: str, context: str) -> str:
        """生成回答"""
        chain = RAG_PROMPT | self.llm
        response = await asyncio.to_thread(
            chain.invoke, {"question": question, "context": context}
        )
        return _extract_text(response.content)

    def _build_sources(self, docs: list[tuple[Document, float]]) -> list[SourceChunk]:
        """构建来源信息"""
        sources = []
        for doc, score in docs:
            sources.append(
                SourceChunk(
                    content=doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content,
                    source=doc.metadata.get("source", "未知"),
                    page=doc.metadata.get("page"),
                    score=round(score, 4),
                    chunk_id=doc.metadata.get("chunk_id", ""),
                )
            )
        return sources
