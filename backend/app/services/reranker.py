"""
重排序服务
对检索结果进行二次排序，提高相关性
支持 Cross-Encoder 和 LLM-based 两种重排序方式
"""

from langchain_core.documents import Document
from app.config import get_settings

settings = get_settings()


class RerankerService:
    """重排序服务：对初始检索结果进行精排"""

    def __init__(self):
        self._cross_encoder = None

    @property
    def cross_encoder(self):
        """延迟加载 Cross-Encoder 模型"""
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                self._cross_encoder = CrossEncoder(
                    settings.RERANK_MODEL,
                    max_length=512,
                    device="cpu",
                )
            except ImportError:
                raise ImportError(
                    "请安装 sentence-transformers: pip install sentence-transformers"
                )
        return self._cross_encoder

    def rerank(
        self, query: str, documents: list[tuple[Document, float]], top_n: int = None
    ) -> list[tuple[Document, float]]:
        """
        对文档进行重排序

        Args:
            query: 查询文本
            documents: (Document, score) 元组列表
            top_n: 返回前 N 个结果

        Returns:
            重排序后的 (Document, score) 元组列表
        """
        if not documents:
            return []

        n = top_n or settings.RERANK_TOP_N

        # 准备 query-doc 对
        pairs = [(query, doc.page_content) for doc, _ in documents]

        # 使用 Cross-Encoder 计算相关性分数
        scores = self.cross_encoder.predict(pairs)

        # 组合并排序
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # 返回 top_n 结果
        results = []
        for (doc, _), rerank_score in scored_docs[:n]:
            doc.metadata["rerank_score"] = float(rerank_score)
            results.append((doc, float(rerank_score)))

        return results

    def rerank_with_llm(
        self, query: str, documents: list[tuple[Document, float]], top_n: int = None
    ) -> list[tuple[Document, float]]:
        """
        使用 LLM 进行重排序（备选方案，不需要额外模型）
        通过让 LLM 评估文档与查询的相关性来排序

        Args:
            query: 查询文本
            documents: (Document, score) 元组列表
            top_n: 返回前 N 个结果

        Returns:
            重排序后的 (Document, score) 元组列表
        """
        from langchain_anthropic import ChatAnthropic
        from langchain_core.prompts import ChatPromptTemplate

        n = top_n or settings.RERANK_TOP_N

        # 构建评估 prompt
        docs_text = ""
        for i, (doc, _) in enumerate(documents):
            docs_text += f"\n--- 文档 {i + 1} ---\n{doc.page_content[:300]}\n"

        prompt = ChatPromptTemplate.from_template(
            """你是一个文档相关性评估专家。请评估以下文档与查询的相关性。

查询：{query}

文档列表：
{documents}

请为每个文档打分（0-10），返回 JSON 格式：
{{"scores": [score1, score2, ...]}}

只返回 JSON，不要其他内容。"""
        )

        llm = ChatAnthropic(
            model=settings.LLM_MODEL,
            temperature=0,
            max_tokens=1024,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            anthropic_api_url=settings.ANTHROPIC_BASE_URL,
        )

        chain = prompt | llm
        response = chain.invoke({"query": query, "documents": docs_text})

        # 解析分数
        import json
        raw_text = response.content if isinstance(response.content, str) else \
            "".join(b.get("text", "") for b in response.content if isinstance(b, dict) and b.get("type") == "text")
        try:
            scores = json.loads(raw_text)["scores"]
        except (json.JSONDecodeError, KeyError):
            # 解析失败，返回原始排序
            return documents[:n]

        # 组合并排序
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for (doc, _), llm_score in scored_docs[:n]:
            doc.metadata["rerank_score"] = float(llm_score)
            results.append((doc, float(llm_score)))

        return results
