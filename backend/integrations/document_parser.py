from pathlib import Path


class DocumentParser:
    SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}

    def parse(self, file_path: str, file_type: str) -> str:
        if file_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {file_type}")

        parsers = {
            "txt": self._parse_txt,
            "md": self._parse_txt,
            "pdf": self._parse_pdf,
            "docx": self._parse_docx,
        }
        return parsers[file_type](file_path)

    def _parse_txt(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")

    def _parse_pdf(self, file_path: str) -> str:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _parse_docx(self, file_path: str) -> str:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
