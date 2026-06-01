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
