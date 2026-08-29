import os

import torch
from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name: str):
        # 重排是主要耗时，用满 CPU 核数并行推理
        torch.set_num_threads(max(1, os.cpu_count() or 4))
        self.model = CrossEncoder(model_name)

    async def rerank(
        self, query: str, passages: list[dict], top_k: int = 5
    ) -> list[dict]:
        if not passages:
            return []

        pairs = [(query, p["text"]) for p in passages]
        scores = self.model.predict(pairs)

        for passage, score in zip(passages, scores):
            passage["rerank_score"] = float(score)

        ranked = sorted(passages, key=lambda x: x["rerank_score"], reverse=True)
        return ranked[:top_k]
