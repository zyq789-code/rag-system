import os

import torch
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str):
        # 容器内 torch 默认可能只用 1 线程，显式用满 CPU 核加速推理
        torch.set_num_threads(max(1, os.cpu_count() or 4))
        self.model = SentenceTransformer(model_name)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.embed_texts_sync(texts)

    async def embed_query(self, query: str) -> list[float]:
        return self.embed_query_sync(query)

    def embed_texts_sync(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query_sync(self, query: str) -> list[float]:
        embedding = self.model.encode([query], normalize_embeddings=True)
        return embedding[0].tolist()
