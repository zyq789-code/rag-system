"""中文 RAG 检索基准（离线、自包含、可复现）。

量化两项内容，用于求职项目展示：
1. 检索质量：legacy BM25（空格分词，优化前） vs jieba BM25（优化后）
   指标：hit@1 / hit@3 / hit@5 / MRR
2. 检索延迟：逐查询重建索引（优化前） vs 索引缓存复用（优化后）
   指标：不同语料规模下稳态单次查询耗时、冷启动建索引耗时

运行（无需外部服务）：
    cd backend
    venv\\Scripts\\python.exe -X utf8 scripts\\benchmark_retrieval.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rank_bm25 import BM25Okapi
from services.bm25 import tokenize  # 当前实现：jieba 分词


# ---------- 合成中文语料（模拟知识库分块后的文档） ----------
TOPICS = [
    ("rag", "RAG 检索增强生成通过向量检索和关键词检索结合的方式从知识库召回相关内容，然后交给大语言模型生成答案"),
    ("distributed_tx", "分布式事务通过两阶段提交、本地消息表和最终一致性等方案来保证跨服务数据的一致性"),
    ("mq", "消息队列通过异步解耦和削峰填谷来缓解高并发场景下的系统压力，并保证最终一致性"),
    ("cache", "缓存雪崩可以通过过期时间加随机值、多级缓存和限流降级等策略来避免大面积缓存同时失效"),
    ("gateway", "微服务网关通过令牌桶算法对请求进行限流，并做统一的鉴权、路由和灰度发布"),
    ("index", "数据库索引通过 B 树结构减少磁盘 IO 扫描次数，从而大幅提升查询性能"),
    ("redis_persist", "Redis 通过 RDB 快照和 AOF 日志两种持久化机制来防止进程重启后数据丢失"),
    ("resume", "简历筛选算法对候选人的技能关键词、工作年限和项目经验进行加权打分，并输出排序结果"),
]

CORPUS = [{"id": k, "text": t} for k, t in TOPICS]

EVAL_QUESTIONS = [
    ("什么是检索增强生成？", "rag"),
    ("分布式事务如何保证一致性？", "distributed_tx"),
    ("消息队列能解决什么问题？", "mq"),
    ("缓存雪崩如何避免？", "cache"),
    ("网关怎么实现限流？", "gateway"),
    ("为什么加索引查询就快了？", "index"),
    ("Redis 重启会丢数据吗？", "redis_persist"),
    ("简历筛选是怎么打分的？", "resume"),
]

# 旧实现：纯空格分词（中文整句变成一个 token）
def legacy_tokenize(text: str) -> list[str]:
    return text.split()


def _bm25_retrieve(bm25, tokenized_query, corpus, top_k):
    """返回按分数排序的命中文档 id 列表（分数为 0 的视为未命中，不参与排序）。"""
    scores = bm25.get_scores(tokenized_query)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [corpus[i]["id"] for i in ranked if scores[i] > 0][:top_k]


def evaluate(corpus, questions, tokenizer_fn, max_k=5):
    """返回 hit@1/3/5 与 MRR。"""
    tokenized_corpus = [tokenizer_fn(d["text"]) for d in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    hits = [0, 0, 0]
    mrr = 0.0
    for query, expected in questions:
        retrieved = _bm25_retrieve(bm25, tokenizer_fn(query), corpus, max_k)
        for i, k in enumerate((1, 3, 5)):
            if expected in retrieved[:k]:
                hits[i] += 1
        if expected in retrieved:
            mrr += 1.0 / (retrieved.index(expected) + 1)
    n = len(questions)
    return [h / n * 100 for h in hits], mrr / n * 100


def build_corpus(n):
    """生成 n 个分块：循环主题句，模拟不同规模的语料。"""
    out, i = [], 0
    while len(out) < n:
        for k, text in TOPICS:
            if len(out) >= n:
                break
            out.append({"id": f"{k}_{i}", "text": text})
            i += 1
    return out


def measure_latency(sizes=(1000, 10000, 50000)):
    """对比逐查询重建（旧）与缓存复用（新）的稳态单次查询耗时。"""
    queries = [tokenize(q) for q, _ in EVAL_QUESTIONS]
    legacy_queries = [legacy_tokenize(q) for q, _ in EVAL_QUESTIONS]

    # 预热 jieba（字典加载只发生一次，不计入稳态测量）
    tokenize("预热")
    tokenize("预热")

    def _score_all(bm25, tqs):
        for tq in tqs:
            bm25.get_scores(tq)

    rows = []
    for n in sizes:
        corpus = build_corpus(n)
        texts = [d["text"] for d in corpus]

        # 旧实现：每次查询都要「空格分词全量语料 + 重建索引」，另加打分
        t0 = time.perf_counter()
        legacy_bm25 = BM25Okapi([legacy_tokenize(t) for t in texts])
        legacy_build_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        _score_all(legacy_bm25, legacy_queries)
        legacy_score_ms = (time.perf_counter() - t0) / len(legacy_queries) * 1000

        # 新冷启动：jieba 分词 + 建索引（仅在文档变更时发生一次）
        t0 = time.perf_counter()
        bm25 = BM25Okapi([tokenize(t) for t in texts])
        jieba_cold_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        _score_all(bm25, queries)
        score_ms = (time.perf_counter() - t0) / len(queries) * 1000

        legacy_per_query = legacy_build_ms + legacy_score_ms  # 旧：每查询都重建
        new_per_query = score_ms  # 新：索引已缓存，稳态只打分
        rows.append(
            (n, legacy_per_query, new_per_query, legacy_per_query / new_per_query, jieba_cold_ms)
        )
    return rows


def main():
    print("=" * 68)
    print("RAG 检索基准 · 中文 BM25：legacy(空格分词) vs jieba(优化后)")
    print("=" * 68)

    print("\n[1] 检索质量  hit@k / MRR（语料 8 篇、问答对 8 组）")
    legacy_hits, legacy_mrr = evaluate(CORPUS, EVAL_QUESTIONS, legacy_tokenize)
    new_hits, new_mrr = evaluate(CORPUS, EVAL_QUESTIONS, tokenize)
    print(f"{'':12}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'MRR':>10}")
    print(f"{'legacy':<12}{legacy_hits[0]:>7.1f}%{legacy_hits[1]:>7.1f}%{legacy_hits[2]:>7.1f}%{legacy_mrr:>9.1f}%")
    print(f"{'jieba':<12}{new_hits[0]:>7.1f}%{new_hits[1]:>7.1f}%{new_hits[2]:>7.1f}%{new_mrr:>9.1f}%")

    print("\n[2] 检索延迟（稳态单次查询）")
    print(f"{'语料分块':>10}{'旧·每查询重建':>14}{'新·缓存复用':>14}{'加速比':>10}{'新·冷启动(仅变更时)':>18}")
    for n, legacy, new, speedup, cold in measure_latency():
        print(f"{n:>8}{legacy:>13.1f}ms{new:>13.2f}ms{int(speedup):>9}x{cold:>17.1f}ms")

    print("\n说明：旧实现每次查询都全量拉取向量库并重建 BM25 索引（空格分词后中文检索基本失效）；")
    print("      新实现 jieba 分词，索引仅在文档变更时重建一次，稳态查询只做打分（另省去每次查询")
    print("      的 ChromaDB 全量网络拉取，本离线基准未计入该网络开销，真实收益更高）。")
    print("      以上为合成演示语料；对真实知识库的评测请运行 scripts/evaluate_rag.py。")


if __name__ == "__main__":
    main()
