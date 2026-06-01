import pytest
from integrations.document_parser import DocumentParser


def test_document_parser_txt(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello world. This is a test document.", encoding="utf-8")
    parser = DocumentParser()
    text = parser.parse(str(test_file), "txt")
    assert text == "Hello world. This is a test document."


def test_document_parser_md(tmp_path):
    test_file = tmp_path / "test.md"
    test_file.write_text("# Title\n\nSome content here.", encoding="utf-8")
    parser = DocumentParser()
    text = parser.parse(str(test_file), "md")
    assert "# Title" in text
    assert "Some content here." in text


def test_document_parser_unsupported(tmp_path):
    test_file = tmp_path / "test.xyz"
    test_file.write_text("data", encoding="utf-8")
    parser = DocumentParser()
    with pytest.raises(ValueError, match="Unsupported file type"):
        parser.parse(str(test_file), "xyz")
