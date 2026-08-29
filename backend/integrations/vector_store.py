import time

import chromadb

# 文本缓存 TTL（秒）：入库/删除会显式失效，这里是兜底外部变更（如 Celery 独立进程写入）
TEXT_CACHE_TTL = 30


class VectorStore:
    def __init__(self, host: str, port: int):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
        self._texts_cache: list[dict] | None = None
        self._texts_cache_ts: float = 0.0
        self._texts_revision = 0

    @property
    def texts_revision(self) -> int:
        """语料版本号：内容变化（增删/缓存过期）时递增，供 BM25 索引缓存失效。"""
        return self._texts_revision

    def _invalidate_texts_cache(self) -> None:
        self._texts_cache = None
        self._texts_cache_ts = 0.0
        self._texts_revision += 1

    async def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self._add_sync(ids, documents, embeddings, metadatas)

    def _add_sync(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        self._invalidate_texts_cache()

    async def query(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    async def delete_by_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})
        self._invalidate_texts_cache()

    async def get_all_texts(self) -> list[dict]:
        now = time.time()
        if self._texts_cache is None or now - self._texts_cache_ts > TEXT_CACHE_TTL:
            results = self.collection.get(include=["documents", "metadatas"])
            self._texts_cache = [
                {"id": id_, "text": doc, "metadata": meta}
                for id_, doc, meta in zip(
                    results["ids"], results["documents"], results["metadatas"]
                )
            ]
            self._texts_cache_ts = now
            self._texts_revision += 1
        return self._texts_cache
