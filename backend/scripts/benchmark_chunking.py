"""分块参数 A/B 实验：比较不同 chunk_size/overlap 下的分块统计与检索命中率。

用法（离线，需已缓存 embedding 模型）：
    cd backend
    venv\\Scripts\\python.exe -X utf8 scripts\\benchmark_chunking.py

输出：每个参数组合的「分块统计 + 向量检索 hit@1/3/5 + MRR」。
注意：对较短语料（如 interview_kb 每篇 1 块）参数差异不明显；对比长文档更有意义。
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.embedding import EmbeddingService
from services.chunking import Chunker

# 要对比的参数组合：(chunk_size, chunk_overlap)
PARAM_SETS = [(256, 32), (512, 64), (768, 96)]


def load_docs(root: Path) -> list[dict]:
    docs = []
    for p in sorted(root.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        if text.strip():
            docs.append({"id": str(p.relative_to(root)), "text": text})
    return docs


def load_questions() -> list[dict]:
    qpath = Path(__file__).resolve().parents[1] / "scripts" / "eval_questions.json"
    return json.loads(qpath.read_text(encoding="utf-8"))["questions"]


def is_hit(chunk: dict, expected: dict) -> bool:
    if "filename" in expected:
        if expected["filename"] in chunk["doc_id"]:
            return True
    if "keyword" in expected:
        if expected["keyword"] in chunk["text"]:
            return True
    return False


def _norm(v: list[float]) -> np.ndarray:
    arr = np.asarray(v, dtype=np.float32)
    n = np.linalg.norm(arr)
    return arr / (n + 1e-9)


def evaluate(emb: EmbeddingService, chunks: list[dict], questions: list[dict]) -> tuple[dict, float]:
    """向量检索 top5 的 hit@1/3/5 与 MRR（隔离分块影响，不含 BM25/重排）。"""
    vectors = [_norm(v) for v in emb.embed_texts_sync([c["text"] for c in chunks])]
    hits = {1: 0, 3: 0, 5: 0}
    mrr = 0.0
    for q in questions:
        qv = _norm(emb.embed_query_sync(q["question"]))
        sims = [float(np.dot(qv, v)) for v in vectors]
        ranked = sorted(range(len(chunks)), key=lambda i: sims[i], reverse=True)[:5]
        pos = next(
            (r for r, idx in enumerate(ranked, 1) if is_hit(chunks[idx], q["expected"])),
            None,
        )
        if pos:
            for k in (1, 3, 5):
                if pos <= k:
                    hits[k] += 1
            mrr += 1.0 / pos
    n = len(questions)
    return {k: v / n * 100 for k, v in hits.items()}, mrr / n * 100


def main() -> None:
    docs_root = Path(__file__).resolve().parents[1] / "data" / "interview_kb"
    docs = load_docs(docs_root)
    questions = load_questions()
    if not docs or not questions:
        print("未找到语料或评测问题集，请先准备 data/interview_kb 与 scripts/eval_questions.json")
        sys.exit(1)

    emb = EmbeddingService("BAAI/bge-small-zh-v1.5")
    print(f"语料：{len(docs)} 篇文档，{len(questions)} 个评测问题\n")
    print(f"{'参数':>10}{'块数':>6}{'平均tok':>8}{'最小':>6}{'最大':>6}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'MRR':>8}")
    print("-" * 70)

    for size, overlap in PARAM_SETS:
        chunker = Chunker(chunk_size=size, chunk_overlap=overlap)
        chunks = []
        for doc in docs:
            for c in chunker.chunk(doc["text"]):
                chunks.append({"doc_id": doc["id"], "text": c})
        tokens = [chunker._count_tokens(c["text"]) for c in chunks]
        hits, mrr = evaluate(emb, chunks, questions)
        avg = sum(tokens) / len(tokens) if tokens else 0
        print(
            f"{str(size)+'/'+str(overlap):>10}{len(chunks):>6}{avg:>8.0f}"
            f"{min(tokens) if tokens else 0:>6}{max(tokens) if tokens else 0:>6}"
            f"{hits[1]:>7.1f}%{hits[3]:>7.1f}%{hits[5]:>7.1f}%{mrr:>7.1f}%"
        )

    print("\n说明：块数/平均token反映切分粒度；hit@k/MRR 反映检索命中。")
    print("对当前较短语料参数差异不大属正常；换长文档（制度/技术手册）跑更看得出差异。")


if __name__ == "__main__":
    main()
