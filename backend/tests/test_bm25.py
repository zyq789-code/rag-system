import pytest
from services.bm25 import tokenize, get_bm25, clear


@pytest.fixture(autouse=True)
def _clear_cache():
    clear()
    yield


def test_tokenize_chinese_words():
    tokens = tokenize("人工智能知识库问答系统")
    assert "人工智能" in tokens
    assert "知识库" in tokens
    assert "RAG" in tokenize("RAG 检索增强生成")


def test_tokenize_removes_stopwords():
    assert "的" not in tokenize("这是知识库的文档")


@pytest.mark.asyncio
async def test_get_bm25_empty_corpus_returns_none():
    class FakeVS:
        texts_revision = 1

        async def get_all_texts(self):
            return []

    texts, bm25_index = await get_bm25(FakeVS())
    assert texts == []
    assert bm25_index is None


@pytest.mark.asyncio
async def test_get_bm25_rebuilds_on_revision_change():
    class FakeVS:
        def __init__(self, revision):
            self.texts_revision = revision

        async def get_all_texts(self):
            return [
                {"id": "1", "text": "RAG 是检索增强生成技术，用于知识库问答。", "metadata": {}},
                {"id": "2", "text": "向量数据库存储文档的语义向量。", "metadata": {}},
                {"id": "3", "text": "欢迎来到系统，这里是操作说明文档。", "metadata": {}},
            ]

    vs = FakeVS(1)
    _, bm25_1 = await get_bm25(vs)
    # 版本号不变：命中缓存，返回同一索引对象
    _, bm25_2 = await get_bm25(vs)
    assert bm25_1 is bm25_2
    # 版本号变化：重建索引
    vs.texts_revision = 2
    _, bm25_3 = await get_bm25(vs)
    assert bm25_3 is not None and bm25_3 is not bm25_1

    scores = bm25_3.get_scores(tokenize("检索增强生成"))
    assert scores[0] > scores[1]
