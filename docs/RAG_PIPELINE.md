# RAG Pipeline — Technical Deep Dive

## Overview

Trace's RAG (Retrieval-Augmented Generation) pipeline is a multi-stage system designed for maximum accuracy and transparency. Each stage is modular, independently testable, and has graceful fallback behavior.

## Stage 1: Ingestion

```
Upload → Parse → Chunk → Embed → Index
```

### Multi-Format Parsing

| Format | Parser | Notes |
|---|---|---|
| PDF | PyPDF2 | Extracts text page by page |
| DOCX | python-docx | Reads paragraph text |
| TXT | Native | UTF-8 with error replacement |
| Markdown | markdown + BeautifulSoup | Strips formatting, keeps text |
| HTML | BeautifulSoup | Removes script/style/nav/footer |
| CSV | Custom | Lines prefixed with "Row N:" |
| JSON | json module | Pretty-printed for embedding |

### Chunking Strategy

We use **recursive character text splitting** with the following separator priority:

1. `\n\n` (paragraph breaks)
2. `\n` (line breaks)
3. `. ` (sentence endings)
4. `! `, `? ` (other sentence endings)
5. `, ` (clause boundaries)
6. ` ` (word boundaries — last resort)

Default chunk size: 512 characters with 64-character overlap.

**Why recursive?** Support documents (product manuals, FAQs, troubleshooting guides) are structured in paragraphs and lists. Recursive splitting with paragraph-first priority preserves document structure better than fixed-size or sentence-only splitting.

### Semantic Chunking (Optional)

When enabled, Trace uses sentence embeddings to detect topic boundaries:
1. Embed each sentence with all-MiniLM-L6-v2
2. Compute cosine similarity between adjacent sentences
3. Find low-similarity boundaries (below 30th percentile)
4. Split at these boundaries (min 128 chars, max 768 chars)

---

## Stage 2: Embedding

We use **sentence-transformers/all-MiniLM-L6-v2**:
- **Dimension**: 384
- **Size**: ~80 MB
- **Speed**: ~10K sentences/second on CPU
- **Normalization**: L2-normalized for cosine similarity
- **Cost**: Free (local, no API calls)

The model is loaded once as a singleton (`EmbeddingProvider`) and reused across all requests.

---

## Stage 3: Hybrid Retrieval

### Dense Retrieval (ChromaDB)

Query → embed with sentence-transformer → cosine similarity search in ChromaDB → top K results

### Sparse Retrieval (TF-IDF)

TF-IDF vectorizer with:
- 5000 max features
- English stop words
- 1-2 character n-grams
- Sublinear term frequency scaling

Built from ALL indexed chunks at query time (rebuilds when new documents are added).

### Score Fusion

```
combined_score = 0.6 × dense_score + 0.4 × sparse_score
```

**Why 60/40 weighting?** Dense retrieval captures semantic meaning better (typos, synonyms, paraphrases), while sparse retrieval excels at keyword precision (product names, IDs, error codes). Support queries often include both natural language AND specific terms.

---

## Stage 4: Reranking

### Primary: Cross-Encoder

Model: `cross-encoder/ms-marco-MiniLM-L-4-v2`

Unlike bi-encoders (which produce independent embeddings), cross-encoders process query-document pairs together through a transformer, producing a much more accurate relevance score.

**Trade-off**: Slower (50-100 pairs/second on CPU) but top-K reranking keeps it manageable (10 items → 10 forward passes).

### Fallback: TF-IDF Reranking

If the cross-encoder fails to load (memory constraints, missing PyTorch), we rerank using direct TF-IDF cosine similarity as a second-pass scorer.

---

## Stage 5: Confidence Scoring

Multi-factor confidence produces a single 0-100% score with a label (high/medium/low):

```
overall = 0.35 × relevance_score + 0.25 × semantic_similarity + 0.20 × source_quality + 0.20 × support_ratio
```

### Factors

1. **Relevance Score (35%)** — Mean of top-5 reranker scores, normalized to [0, 1]
2. **Semantic Similarity (25%)** — Relevance × support ratio (penalizes few supporting chunks)
3. **Source Quality (20%)** — 50% source diversity + 50% consistency (low variance = high quality)
4. **Support Ratio (20%)** — How many of the top K chunks have meaningful scores

### Thresholds

| Label | Range | Behavior |
|---|---|---|
| High | ≥ 0.75 | Return answer with full confidence |
| Medium | 0.45 - 0.74 | Return answer with "I'm not entirely sure" caveat |
| Low | < 0.45 | Return "I couldn't find reliable information" + suggest sources |

---

## Stage 6: Generation

### Prompt Engineering

The generation prompt enforces strict rules:
1. **Answer ONLY from provided context** — no external knowledge
2. **Cite sources** — `[Source 1]`, `[Source 2]` after every factual claim
3. **Honest uncertainty** — "I couldn't find information about that" if context is insufficient
4. **Concise formatting** — Bullet points for lists, markdown for structure

### LLM Providers

| Provider | Model | Free Tier | Priority |
|---|---|---|---|
| Google Gemini | gemini-2.0-flash | 60 req/min | Primary |
| Groq | llama-3.3-70b-versatile | 30 req/min, no credit card | Fallback |

### Fallback Mode

If NO API keys are configured, Trace runs in **offline mode** and returns extractive answers — directly showing the most relevant chunks. This means the system works completely without any external API calls.

---

## Stage 7: Post-Processing

1. **PII Redaction** — Regex-based detection of phone numbers, emails, Aadhaar, PAN, credit cards, passwords
2. **Content Moderation** (input side) — Keyword-based toxicity detection before processing
3. **Confidence Attachment** — Score object added to response metadata
4. **History Storage** — Message saved to SQLite with full metadata (sources, confidence, processing time)
