"""结构化感知的文本分块器。

相对旧版（按行贪心 + 字符估算 overlap）的改进：
1. overlap 用 tiktoken 精确数 token，不再用「4 字符≈1 token」的字符估算
2. 保留段落边界：先按结构单元（段落/标题/代码块/表格）切分，再贪心累积，
   不再把 \\n\\n 压成 \\n 导致段落结构丢失
3. 标题（H1-H6）作为天然切分点；代码块、表格作为原子单元，不拦腰切断
4. 块级质量校验：过滤近空块、合并过短块、标记过长块
5. 参数可调，配合 scripts/benchmark_chunking.py 做 A/B 实验选参
"""

import logging
import re

import tiktoken

# 块级质量校验阈值（token）
MIN_CHUNK_TOKENS = 50
MAX_CHUNK_TOKENS = 1024

logger = logging.getLogger(__name__)


class Chunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def _tail_tokens(self, text: str, n: int) -> str:
        """取文本末尾 n 个 token 对应的文本（精确按 token，而非字符估算）。"""
        tokens = self._enc.encode(text)
        if not tokens or n <= 0:
            return ""
        return self._enc.decode(tokens[-n:])

    @staticmethod
    def _is_heading(line: str) -> bool:
        return bool(re.match(r"^#{1,6}\s+\S", line))

    @staticmethod
    def _is_table_line(line: str) -> bool:
        return "|" in line and line.strip().startswith("|")

    def _split_structural_units(self, text: str) -> list[str]:
        """按文档结构切分为原子单元：代码块 / 表格 / 标题 / 段落。

        - 代码块（``` 围栏）整体为一个单元，内部不切
        - 连续表格行（| 开头）整体为一个单元，不拆散
        - 标题（# 开头）为独立单元，作为后续切分点
        - 段落：空行（\\n\\n）作为段落边界
        """
        lines = text.split("\n")
        units: list[str] = []
        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()
            # 代码块
            if stripped.startswith("```"):
                buf = [line]
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    buf.append(lines[i])
                    i += 1
                if i < n:  # 闭合围栏
                    buf.append(lines[i])
                    i += 1
                units.append("\n".join(buf))
                continue
            # 表格块：连续含 | 的行
            if self._is_table_line(line):
                buf = [line]
                i += 1
                while i < n and self._is_table_line(lines[i]):
                    buf.append(lines[i])
                    i += 1
                units.append("\n".join(buf))
                continue
            # 标题：独立单元
            if self._is_heading(line):
                units.append(line)
                i += 1
                continue
            # 普通段落：累积到下一个结构边界
            buf = [line]
            i += 1
            while i < n:
                nxt = lines[i]
                nst = nxt.strip()
                if (
                    nst == ""
                    or self._is_heading(nxt)
                    or nst.startswith("```")
                    or self._is_table_line(nxt)
                ):
                    break
                buf.append(nxt)
                i += 1
            units.append("\n".join(buf))
        return [u for u in units if u.strip()]

    def chunk(self, text: str) -> list[str]:
        """结构化分块：标题作切分点，代码块/表格作原子单元，overlap 精确按 token。"""
        if not text.strip():
            return []
        if self._count_tokens(text) <= self.chunk_size:
            return self._cleanup([text])

        units = self._split_structural_units(text)
        chunks: list[str] = []
        current = ""

        for unit in units:
            unit_tokens = self._count_tokens(unit)
            # 单个单元就超大（超长段落/长代码块）→ 内部按行切
            if unit_tokens > self.chunk_size:
                if current.strip():
                    chunks.append(current.strip())
                current = ""
                chunks.extend(p for p in self._split_oversized_unit(unit) if p.strip())
                continue
            # 标题且当前块已有内容 → 标题开启新块（标题是强边界，不跨标题带 overlap）
            if self._is_heading(unit) and current.strip():
                chunks.append(current.strip())
                current = ""
            # 超限 → 提交当前块，末尾 overlap 个 token 作为下块前缀
            if current and self._count_tokens(current) + unit_tokens > self.chunk_size:
                chunks.append(current.strip())
                current = self._tail_tokens(current, self.chunk_overlap)
            current = (current + "\n" + unit) if current else unit

        if current.strip():
            chunks.append(current.strip())
        return self._cleanup(chunks)

    def _split_oversized_unit(self, unit: str) -> list[str]:
        """超大单元（超长段落/代码块）按行切，overlap 同样精确按 token。"""
        lines = unit.split("\n")
        parts: list[str] = []
        current = ""
        for line in lines:
            if current and self._count_tokens(current) + self._count_tokens(line) > self.chunk_size:
                parts.append(current.strip())
                current = self._tail_tokens(current, self.chunk_overlap)
            current = (current + "\n" + line) if current else line
        if current.strip():
            parts.append(current.strip())
        return parts

    def _cleanup(self, chunks: list[str]) -> list[str]:
        """块级质量校验：过滤近空块、合并过短块、标记过长块。"""
        if not chunks:
            return []
        result: list[str] = []
        for c in chunks:
            tokens = self._count_tokens(c)
            if tokens == 0:
                continue
            # 过短块：并入前一块（合并后不超上限）
            if tokens < MIN_CHUNK_TOKENS and result:
                merged = result[-1] + "\n" + c
                if self._count_tokens(merged) <= self.chunk_size:
                    result[-1] = merged
                    continue
            # 过长块：打日志标记（可能是解析失败/异常内容）
            if tokens > MAX_CHUNK_TOKENS:
                logger.warning("chunk too long: %s tokens (>%s)", tokens, MAX_CHUNK_TOKENS)
            result.append(c)
        return result

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
