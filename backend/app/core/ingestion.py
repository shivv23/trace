import os
import io
import uuid
import hashlib
from pathlib import Path
from typing import BinaryIO
from datetime import datetime

from app.config import settings
from app.models.db import upsert_document


def parse_text(content: str, filename: str) -> str:
    return content


def parse_markdown(content: str, filename: str) -> str:
    try:
        import markdown
        html = markdown.markdown(content)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n')
    except ImportError:
        return content


def parse_pdf(filepath: str) -> str:
    try:
        import PyPDF2
        text = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return '\n'.join(text)
    except ImportError:
        raise RuntimeError("PyPDF2 not installed")


def parse_docx(filepath: str) -> str:
    try:
        import docx
        doc = docx.Document(filepath)
        return '\n'.join([p.text for p in doc.paragraphs if p.text])
    except ImportError:
        raise RuntimeError("python-docx not installed")


def parse_html(content: str, filename: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        return soup.get_text(separator='\n')
    except ImportError:
        return content


def parse_csv(content: str, filename: str) -> str:
    lines = content.split('\n')
    return '\n'.join([f"Row {i}: {line}" for i, line in enumerate(lines) if line.strip()])


def parse_json(content: str, filename: str) -> str:
    import json
    try:
        data = json.loads(content)
        return json.dumps(data, indent=2)
    except json.JSONDecodeError:
        return content


PARSERS = {
    '.txt': parse_text,
    '.md': parse_markdown,
    '.pdf': parse_pdf,
    '.docx': parse_docx,
    '.html': parse_html,
    '.htm': parse_html,
    '.csv': parse_csv,
    '.json': parse_json,
}


def extract_text(filepath: str, original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower()
    parser = PARSERS.get(ext)

    if not parser:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext in ('.pdf', '.docx'):
        return parser(filepath)
    else:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return parser(content, original_filename)


def process_upload(file: BinaryIO, filename: str) -> tuple[str, str, int, str, str]:
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")

    peek = file.read(1)
    file.seek(0)
    if isinstance(file, io.BufferedReader):
        try:
            fileno = file.fileno()
            file_size = os.fstat(fileno).st_size
        except (OSError, io.UnsupportedOperation):
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
    else:
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise ValueError(f"File size ({file_size} bytes) exceeds maximum of {max_bytes} bytes")

    doc_id = str(uuid.uuid4())
    dest = settings.UPLOAD_DIR / f"{doc_id}{ext}"
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    content = file.read()
    size_bytes = len(content)
    file_hash = hashlib.sha256(content).hexdigest()

    with open(dest, 'wb') as f:
        f.write(content)

    return doc_id, str(dest), size_bytes, ext, file_hash


def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    return hasher.hexdigest()
