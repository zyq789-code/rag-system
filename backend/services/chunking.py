import tiktoken


class Chunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def chunk(self, text: str) -> list[str]:
        if self._count_tokens(text) <= self.chunk_size:
            return [text]

        sentences = text.replace("\n\n", "\n").split("\n")
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                overlap_text = current_chunk[-self.chunk_overlap * 4:] if self.chunk_overlap else ""
                current_chunk = overlap_text + sentence
                current_tokens = self._count_tokens(current_chunk)
            else:
                current_chunk += ("\n" if current_chunk else "") + sentence
                current_tokens += sentence_tokens

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def chunk_with_metadata(self, text: str, base_metadata: dict) -> list[dict]:
        chunks = self.chunk(text)
        return [
            {
                "text": chunk,
                "metadata": {
                    **base_metadata,
                    "chunk_index": i,
                    "token_count": self._count_tokens(chunk),
                },
            }
            for i, chunk in enumerate(chunks)
        ]
