import re
import numpy as np


def recursive_character_split(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[dict]:
    separators = ["\n\n", "\n", ". ", "! ", "? ", ", ", " "]
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        if end < text_len:
            best_sep = -1
            best_sep_len = 0
            for sep in separators:
                pos = text.rfind(sep, start, end)
                if pos > best_sep:
                    best_sep = pos
                    best_sep_len = len(sep)
            if best_sep > start:
                end = best_sep + best_sep_len if best_sep + best_sep_len <= text_len else best_sep

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "content": chunk_text,
                "start_char": start,
                "end_char": end,
                "chunk_index": len(chunks),
            })

        if end >= text_len:
            break

        new_start = end - chunk_overlap
        if new_start <= start:
            new_start = end
        start = new_start

    return chunks


def semantic_chunking(text: str, embedding_fn, min_chunk_size: int = 128, max_chunk_size: int = 768) -> list[dict]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 1:
        return recursive_character_split(text, max_chunk_size, 32)

    sentence_embeddings = embedding_fn(sentences)
    similarities = []
    for i in range(1, len(sentence_embeddings)):
        sim = np.dot(sentence_embeddings[i - 1], sentence_embeddings[i]) / (
            np.linalg.norm(sentence_embeddings[i - 1]) * np.linalg.norm(sentence_embeddings[i]) + 1e-8
        )
        similarities.append(sim)

    threshold = float(np.percentile(similarities, 30)) if similarities else 0.3

    chunks = []
    current_chunk = []
    current_size = 0
    char_pos = 0

    for i, sentence in enumerate(sentences):
        start_char = text.find(sentence, char_pos)
        if start_char == -1:
            start_char = char_pos
        current_chunk.append(sentence)
        current_size += len(sentence)

        is_last = i == len(sentences) - 1
        is_break = i > 0 and similarities[i - 1] < threshold
        is_too_big = current_size >= max_chunk_size

        if (is_break and current_size >= min_chunk_size) or is_too_big or is_last:
            chunk_text = " ".join(current_chunk)
            end_char = start_char + len(chunk_text)
            chunks.append({
                "content": chunk_text,
                "start_char": start_char,
                "end_char": end_char,
                "chunk_index": len(chunks),
            })
            char_pos = end_char
            current_chunk = []
            current_size = 0

    return chunks


def chunk_text(text: str, strategy: str = "recursive", **kwargs) -> list[dict]:
    if strategy == "semantic" and "embedding_fn" in kwargs:
        return semantic_chunking(text, kwargs["embedding_fn"])
    return recursive_character_split(text, **kwargs)
