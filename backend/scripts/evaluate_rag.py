"""在线 RAG 检索评测：对真实 ChromaDB 语料计算 hit@k / MRR。

前置条件：
    docker-compose up -d postgres redis chromadb    # 已启动基础设施
    Celery Worker 已运行且目标文档已入库（status=completed）

用法：
    cd backend
    venv\\Scripts\\activate
    venv\\Scripts\\python.exe -X utf8 scripts\\evaluate_rag.py [评测问题.json]

评测问题文件格式（json）：
{
    "questions": [
        {"question": "什么是检索增强生成？", "expected": {"filename": "rag_intro.pdf"}},
        {"question": "分布式事务怎么保证一致性？", "expected": {"keyword": "分布式事务"}}
    ]
}

命中判定（二选一，任一命中即算该问题召回成功）：
    expected.filename  结果 metadata.filename 与之相等
    expected.keyword   结果文本包含该关键词

输出：逐条明细 + 汇总 hit@1 / hit@3 / hit@5 / MRR，明细同时写入 eval_results.csv。
"""

import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loguru import logger
from core.config import get_settings
from core.dependencies import get_llm_provider, get_embedding_service, get_vector_store, get_reranker
from services.rag_service import RAGService


def _is_hit(result: dict, expected: dict) -> bool:
    if "filename" in expected:
        if result.get("metadata", {}).get("filename") == expected["filename"]:
            return True
    if "keyword" in expected:
        if expected["keyword"] in result.get("text", ""):
            return True
    return False


async def _run_eval(questions_path: str):
    settings = get_settings()
    rag = RAGService(
        llm=get_llm_provider(),
        embedding=get_embedding_service(),
        vector_store=get_vector_store(),
        reranker=get_reranker(),
        settings=settings,
    )

    data = json.loads(Path(questions_path).read_text(encoding="utf-8"))
    questions = data["questions"]
    top_n = settings.top_k_rerank
    logger.info(f"评测 {len(questions)} 个问题，检索 Top-{top_n}（重排后）")

    detail_rows = []
    total = len(questions)
    hit_1 = hit_3 = hit_5 = 0
    mrr_sum = 0.0

    for idx, item in enumerate(questions, 1):
        question = item["question"]
        expected = item["expected"]
        results = await rag.search(question)

        # 命中位置（1-based；未命中为 None）
        match_pos = next(
            (pos for pos, r in enumerate(results, 1) if _is_hit(r, expected)),
            None,
        )
        if match_pos:
            if match_pos <= 1:
                hit_1 += 1
            if match_pos <= 3:
                hit_3 += 1
            if match_pos <= 5:
                hit_5 += 1
            mrr_sum += 1.0 / match_pos

        top_filenames = [r.get("metadata", {}).get("filename", "?") for r in results]
        detail_rows.append({
            "question": question,
            "hit_pos": match_pos or "-",
            "hit@1": "✓" if match_pos == 1 else "",
            "hit@3": "✓" if match_pos and match_pos <= 3 else "",
            "hit@5": "✓" if match_pos and match_pos <= 5 else "",
            "top_sources": " | ".join(top_filenames),
        })
        logger.info(f"[{idx}/{total}] {question} -> hit@{match_pos if match_pos else '无'}")

    # 汇总
    print("\n" + "=" * 64)
    print(f"RAG 检索评测报告（{total} 个问题，Top-{top_n}）")
    print("=" * 64)
    print(f"{'':10}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'MRR':>10}")
    print(f"{'':10}{hit_1/total*100:>7.1f}%{hit_3/total*100:>7.1f}%{hit_5/total*100:>7.1f}%{mrr_sum/total*100:>9.1f}%")
    print("=" * 64)

    # 明细写 CSV
    out_csv = Path(__file__).resolve().parents[1] / "eval_results.csv"
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(detail_rows[0].keys()) if detail_rows else [])
        writer.writeheader()
        writer.writerows(detail_rows)
    print(f"逐条明细已写入 {out_csv}")

    # 退出码：hit@1 过低视为失败，便于 CI 集成
    return 0 if hit_1 / total >= 0.6 else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(asyncio.run(_run_eval(sys.argv[1])))


if __name__ == "__main__":
    main()
