import pytest
from unittest.mock import AsyncMock, MagicMock
from services.document_service import DocumentService


def test_allowed_file_types():
    service = DocumentService(
        session=AsyncMock(), parser=MagicMock(),
        chunker=MagicMock(), embedding_service=AsyncMock(), vector_store=AsyncMock(),
    )
    assert service._is_allowed("report.pdf") is True
    assert service._is_allowed("notes.txt") is True
    assert service._is_allowed("data.csv") is False
    assert service._is_allowed("image.png") is False


def test_get_file_type():
    service = DocumentService(
        session=AsyncMock(), parser=MagicMock(),
        chunker=MagicMock(), embedding_service=AsyncMock(), vector_store=AsyncMock(),
    )
    assert service._get_file_type("report.pdf") == "pdf"
    assert service._get_file_type("notes.docx") == "docx"
    assert service._get_file_type("readme.md") == "md"
