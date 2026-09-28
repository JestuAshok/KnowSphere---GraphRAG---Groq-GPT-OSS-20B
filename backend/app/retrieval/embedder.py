"""
FAISS-based vector store with sentence-transformers embeddings.
Provides: add_documents, search_similar, save/load index.
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.config import get_settings

import os

# Set Hugging Face offline-friendly defaults to prevent 40s connection timeouts
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

# Lazy imports — loaded on-demand when vector operations are requested
_ML_AVAILABLE = True
np = None

settings = get_settings()

MODEL_NAME = "all-MiniLM-L6-v2"
DIMENSION = 384  # all-MiniLM-L6-v2 output dim

_model: Optional[Any] = None
_index: Optional[Any] = None
_metadata: List[Dict[str, Any]] = []  # parallel list to FAISS index


def _get_model():
    global _model
    if not _ML_AVAILABLE:
        raise RuntimeError("sentence-transformers and faiss are not installed. Run: pip install sentence-transformers faiss-cpu")
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Try local cache first to avoid hanging on HuggingFace Hub network checks
        try:
            _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(MODEL_NAME)
    return _model


def warmup_embedder():
    """Preload model and index into memory at startup to eliminate cold-start latency."""
    try:
        load_index()
        _get_model()
        # Warm up tensor inference with a tiny dummy embedding
        embed_texts(["warmup"])
    except Exception as e:
        print(f"[Embedder] Warmup note: {e}")



def _index_path() -> Path:
    return Path(settings.faiss_index_path)


def _meta_path() -> Path:
    return _index_path() / "metadata.json"


def _faiss_path() -> Path:
    return _index_path() / "index.faiss"


def load_index():
    """Load FAISS index + metadata from disk if they exist."""
    global _index, _metadata
    if not _ML_AVAILABLE:
        return  # Skip silently if ML packages not installed
    import faiss
    faiss_file = _faiss_path()
    meta_file = _meta_path()
    if faiss_file.exists() and meta_file.exists():
        _index = faiss.read_index(str(faiss_file))
        with open(meta_file, "r", encoding="utf-8") as f:
            _metadata = json.load(f)
    else:
        _index = faiss.IndexFlatIP(DIMENSION)
        _metadata = []


def save_index():
    """Persist FAISS index + metadata to disk."""
    global _index, _metadata
    if not _ML_AVAILABLE:
        return
    import faiss
    _index_path().mkdir(parents=True, exist_ok=True)
    if _index is not None:
        faiss.write_index(_index, str(_faiss_path()))
    with open(_meta_path(), "w", encoding="utf-8") as f:
        json.dump(_metadata, f)


def embed_texts(texts: List[str]):
    import numpy as np
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.astype(np.float32)


def add_documents(chunks: List[Dict[str, Any]]):
    """
    Add document chunks to the FAISS index.
    Each chunk: {"text": str, "doc_id": str, "doc_name": str, "chunk_idx": int}
    """
    global _index, _metadata
    if _index is None:
        load_index()

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    _index.add(embeddings)
    _metadata.extend(chunks)
    save_index()


def search_similar(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for top-k similar chunks. Returns list of chunk dicts with 'score'.
    """
    global _index, _metadata
    if _index is None:
        load_index()
    if _index.ntotal == 0:
        return []

    q_emb = embed_texts([query])
    k = min(k, _index.ntotal)
    scores, indices = _index.search(q_emb, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_metadata):
            continue
        chunk = dict(_metadata[idx])
        chunk["score"] = float(score)
        results.append(chunk)
    return results


def get_index_size() -> int:
    global _index
    if _index is None:
        load_index()
    return _index.ntotal if _index else 0
