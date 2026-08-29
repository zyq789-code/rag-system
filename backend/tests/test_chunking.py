from services.chunking import Chunker


def test_chunk_short_text():
    chunker = Chunker(chunk_size=512, chunk_overlap=64)
    chunks = chunker.chunk("Hello world.")
    assert len(chunks) == 1
    assert chunks[0] == "Hello world."


def test_chunk_long_text():
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    text = "This is a sentence.\n" * 50
    chunks = chunker.chunk(text)
    assert len(chunks) > 1


def test_chunk_with_metadata():
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunker.chunk_with_metadata(text, {"document_id": "doc1"})
    assert all("document_id" in c["metadata"] for c in chunks)
    assert all("chunk_index" in c["metadata"] for c in chunks)
    assert all("token_count" in c["metadata"] for c in chunks)


def test_chunk_preserves_all_content():
    """无论怎么切，原始内容不应丢失。"""
    chunker = Chunker(chunk_size=80, chunk_overlap=20)
    text = "第一段第一行。\n第一段第二行。\n\n第二段第一行。\n\n第三段第一行。\n第三段第二行。"
    chunks = chunker.chunk(text)
    joined = "\n".join(chunks)
    for fragment in ("第一段第一行", "第一段第二行", "第二段第一行", "第三段第一行", "第三段第二行"):
        assert fragment in joined


def test_chunk_keeps_code_block_together():
    """代码块不应被拦腰切断（块尺寸能容纳时保持原子）。"""
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    text = "前文内容。\n```\ncode line one\ncode line two\ncode line three\n```\n后文内容。"
    chunks = chunker.chunk(text)
    code_chunks = [c for c in chunks if "code line one" in c]
    assert len(code_chunks) == 1
    assert "code line two" in code_chunks[0]
    assert "code line three" in code_chunks[0]


def test_chunk_keeps_table_together():
    """表格（| 行）不应被拆散。"""
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    text = "表头说明\n| A | B |\n| 1 | 2 |\n| 3 | 4 |\n表格后说明"
    chunks = chunker.chunk(text)
    table_chunks = [c for c in chunks if "| A |" in c]
    assert len(table_chunks) == 1
    assert "| 1 |" in table_chunks[0]
    assert "| 3 |" in table_chunks[0]


def test_chunk_heading_is_split_point():
    """标题（#）应作为天然切分点，两个章节不应混在同一块。"""
    chunker = Chunker(chunk_size=40, chunk_overlap=10)
    text = (
        "# 第一章标题\n" + "第一章内容行需要一些字数。\n" * 6
        + "# 第二章标题\n" + "第二章内容行也要一些字数。\n" * 6
    )
    chunks = chunker.chunk(text)
    c1 = [c for c in chunks if "第一章标题" in c]
    c2 = [c for c in chunks if "第二章标题" in c]
    assert c1 and c2
    # 第二章标题所在的块不应包含第一章标题
    assert "第一章标题" not in c2[0]


def test_chunk_short_chunk_merged():
    """过短块应被并入前一块。"""
    chunker = Chunker(chunk_size=200, chunk_overlap=20)
    # 用长内容 + 尾部一行短内容，确保尾部短块被合并
    text = "这是主要段落内容。" * 50 + "\n" + "尾部小尾巴。"
    chunks = chunker.chunk(text)
    # 尾部短内容不应单独成块（合并进前一块）
    assert not any("尾部小尾巴" in c and len(c) < 10 for c in chunks)
