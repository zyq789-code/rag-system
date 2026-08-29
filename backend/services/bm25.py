"""中文友好的 BM25 检索，带索引缓存。

原实现（rag_service 内联）每次查询都全量拉取 ChromaDB 语料并按空格分词重建索引：
中文不分词导致召回差，且查询时延随语料规模线性增长。

本模块改用 jieba 中文分词，并按 VectorStore.texts_revision 缓存「分词语料 + BM25 索引」：
文档入库/删除/缓存过期都会使 revision 递增，索引自动重建。
"""

import jieba
from rank_bm25 import BM25Okapi

# 基础中英文停用词（够用即可，不过度设计）
_STOPWORDS = frozenset(
    "的 了 和 是 在 有 与 及 等 中 之 也 都 而 为 于 我 你 他 她 它 我们 你们 他们 这个 那个 这些 那些 "
    "a an the and or of to in on for with is are was were be by at as from not no".split()
)

# 模块级缓存：key = VectorStore.texts_revision，内容变化即重建
_cache: dict = {"revision": -1, "texts": [], "bm25": None}


def tokenize(text: str) -> list[str]:
    """jieba 中文分词，过滤空串与停用词。"""
    return [w for w in jieba.cut(text) if w.strip() and w.strip() not in _STOPWORDS]


def clear() -> None:
    """清空缓存（测试用）。"""
    _cache.update(revision=-1, texts=[], bm25=None)


async def get_bm25(vector_store) -> tuple[list[dict], BM25Okapi | None]:
    """返回 (texts, bm25_index)。

    texts 为当前语料（含 metadata，供知识库过滤）；空语料返回 None 索引。
    索引按 vector_store.texts_revision 缓存，内容变化时自动重建。
    """
    revision = vector_store.texts_revision
    if _cache["revision"] != revision:
        texts = await vector_store.get_all_texts()
        tokenized = [tokenize(t["text"]) for t in texts]
        _cache.update(
            revision=revision,
            texts=texts,
            bm25=BM25Okapi(tokenized) if tokenized else None,
        )
    return _cache["texts"], _cache["bm25"]
