import asyncio
from collections.abc import AsyncIterator

from integrations.llm.base import LLMProvider
from integrations.embedding import EmbeddingService
from integrations.vector_store import VectorStore
from integrations.reranker import Reranker
from schemas.chat import SourceCitation
from core.config import Settings
from services.bm25 import get_bm25, tokenize

SYSTEM_PROMPT = """你是一个智能知识库问答助手。根据提供的文档内容回答用户问题。

规则：
1. 只根据提供的上下文内容回答，不要编造信息
2. 如果上下文没有相关信息，明确告知用户
3. 引用来源时标注文件名
4. 回答简洁准确，使用中文"""

class RAGService:
    def __init__(
        self,
        llm: LLMProvider,
        embedding: EmbeddingService,
        vector_store: VectorStore,
        reranker: Reranker,
        settings: Settings,
    ):
        self.llm = llm
        self.embedding = embedding
        self.vector_store = vector_store
        self.reranker = reranker
        self.settings = settings

    def _rrf_merge(self, results: list[list[dict]], k: int = 60) -> list[dict]:
        """Reciprocal Rank Fusion 融合多个搜索结果"""
        scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}
        for rank_list in results:
            for rank, doc in enumerate(rank_list):
                doc_id = doc["id"]
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc
        ranked = sorted(doc_map.keys(), key=lambda did: scores[did], reverse=True)
        return [doc_map[did] for did in ranked]

    async def _vector_search(self, query: str, kb_id: str | None) -> list[dict]:
        query_vector = await self.embedding.embed_query(query)
        where_filter = None
        if kb_id:
            where_filter = {"knowledge_base_id": kb_id}
        results = await self.vector_store.query(
            query_embedding=query_vector,
            n_results=self.settings.top_k_vector,
            where=where_filter,
        )
        passages = []
        for i in range(len(results["ids"])):
            passages.append({
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "score": max(0, 1 - results["distances"][i]),
            })
        return passages

    async def _bm25_search(self, query: str, kb_id: str | None) -> list[dict]:
        """BM25 关键词检索（jieba 中文分词 + 索引缓存）"""
        texts, bm25 = await get_bm25(self.vector_store)
        if not texts or bm25 is None:
            return []

        tokenized_query = tokenize(query)
        if not tokenized_query:
            return []

        scores = bm25.get_scores(tokenized_query)
        top_n = min(self.settings.top_k_bm25, len(scores))

        # 按 BM25 得分取 top
        indexed = sorted(
            [(i, scores[i]) for i in range(len(scores))],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        passages = []
        for idx, score in indexed:
            t = texts[idx]
            if kb_id:
                meta_kb = t.get("metadata", {}).get("knowledge_base_id")
                if meta_kb and meta_kb != kb_id:
                    continue
            passages.append({
                "id": t["id"],
                "text": t["text"],
                "metadata": t.get("metadata", {}),
                "score": float(score),
            })
        return passages

    async def search(self, query: str, kb_id: str | None = None) -> list[dict]:
        # 1. 混合检索：向量 + BM25 并行
        vector_results, bm25_results = await asyncio.gather(
            self._vector_search(query, kb_id),
            self._bm25_search(query, kb_id),
        )
        vector_results = [r for r in vector_results if r["score"] >= 0.3]

        all_results = [vector_results, bm25_results]
        if not any(r for r in all_results):
            return []

        # 2. RRF 融合
        fused = self._rrf_merge(all_results)

        # 3. 去重
        seen = set()
        deduped = []
        for doc in fused:
            text = doc["text"][:100]
            if text not in seen:
                seen.add(text)
                deduped.append(doc)

        # 4. Cross-Encoder 重排
        reranked = await self.reranker.rerank(query, deduped, top_k=self.settings.top_k_rerank)
        return reranked

    def _build_prompt(self, question: str, contexts: list[dict]) -> str:
        if not contexts:
            context_text = "没有找到相关文档。"
        else:
            context_parts = []
            for i, ctx in enumerate(contexts, 1):
                filename = ctx.get("metadata", {}).get("filename", "未知")
                context_parts.append(
                    f"[来源 {i}: {filename}]\n{ctx['text']}"
                )
            context_text = "\n\n".join(context_parts)

        return f"""参考文档内容：
{context_text}

用户问题：{question}

请根据参考文档内容回答问题。如果文档中没有相关信息，请告知用户。回答时引用来源文件名。"""

    async def chat(self, question: str, kb_id: str | None = None) -> tuple[str, list[SourceCitation]]:
        contexts = await self.search(question, kb_id)
        prompt = self._build_prompt(question, contexts)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.llm.chat(messages, temperature=0.1)

        citations = [
            SourceCitation(
                filename=ctx.get("metadata", {}).get("filename", "未知"),
                chunk_text=ctx["text"][:200],
                score=ctx.get("rerank_score", ctx.get("score", 0)),
            )
            for ctx in contexts
        ]

        return response, citations

    async def chat_stream(
        self, question: str, kb_id: str | None = None, history: list[dict] | None = None
    ) -> AsyncIterator[tuple[str, list[SourceCitation] | None]]:
        contexts = await self.search(question, kb_id)

        citations = [
            SourceCitation(
                filename=ctx.get("metadata", {}).get("filename", "未知"),
                chunk_text=ctx["text"][:200],
                score=ctx.get("rerank_score", ctx.get("score", 0)),
            )
            for ctx in contexts
        ]
        yield ("__sources__", citations)

        prompt = self._build_prompt(question, contexts)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": prompt})

        async for token in self.llm.chat_stream(messages, temperature=0.1):
            yield (token, None)
