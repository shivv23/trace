import sys
import tempfile
import os
sys.path.insert(0, 'backend')

from app.core.ingestion import extract_text, parse_text, parse_markdown, parse_csv, parse_html


def test_parse_text():
    content = "Hello world"
    result = parse_text(content, "test.txt")
    assert result == "Hello world"


def test_parse_markdown():
    content = "# Title\n\nThis is **bold** text."
    result = parse_markdown(content, "test.md")
    assert "Title" in result
    assert "bold" in result


def test_parse_csv():
    content = "name,age\nAlice,30\nBob,25"
    result = parse_csv(content, "test.csv")
    assert "Row 0" in result
    assert "Alice" in result
    assert "Row 1" in result
    assert "Bob" in result


def test_parse_html():
    content = "<html><body><h1>Title</h1><p>Paragraph</p><script>alert('x')</script></body></html>"
    result = parse_html(content, "test.html")
    assert "Title" in result
    assert "Paragraph" in result
    assert "script" not in result
    assert "alert" not in result


def test_extract_text_txt():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Hello world")
        fpath = f.name
    try:
        result = extract_text(fpath, "test.txt")
        assert result == "Hello world"
    finally:
        os.unlink(fpath)
