import sys
sys.path.insert(0, 'backend')

from app.core.chunking import recursive_character_split, chunk_text


def test_recursive_split_basic():
    text = "Hello world. This is a test.\n\n" + "A" * 200 + "\n\nAnd a third one."
    chunks = recursive_character_split(text, chunk_size=100, chunk_overlap=10)
    assert len(chunks) >= 2
    assert all(c["content"] for c in chunks)
    assert all(c["chunk_index"] == i for i, c in enumerate(chunks))


def test_recursive_split_empty():
    chunks = recursive_character_split("", chunk_size=100, chunk_overlap=10)
    assert chunks == []


def test_recursive_split_short():
    text = "Short text."
    chunks = recursive_character_split(text, chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 1
    assert chunks[0]["content"] == "Short text."


def test_recursive_split_no_overlap():
    text = "A " * 1000
    chunks = recursive_character_split(text, chunk_size=100, chunk_overlap=0)
    assert len(chunks) > 5
    for c in chunks:
        assert len(c["content"]) <= 100 + 50


def test_chunk_text_recursive():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    chunks = chunk_text(text, strategy="recursive", chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 1


def test_chunk_text_semantic_fallback_to_recursive():
    text = "Hello world. This is a test. Multiple sentences here."
    chunks = chunk_text(text, strategy="semantic", chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 1



def test_chunk_text_semantic_with_embedding():
    import numpy as np
    def dummy_embed(texts):
        rng = np.random.RandomState(42)
        return rng.rand(len(texts), 384)
    text = "Hello world. This is a test. Multiple sentences here."
    chunks = chunk_text(text, strategy="semantic", embedding_fn=dummy_embed,
                        chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 1
    assert all(c["start_char"] >= 0 for c in chunks)
    assert all(c["end_char"] >= c["start_char"] for c in chunks)
