import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from app.config import settings


_embedding_model = None
_index_cache: dict[str, tuple] = {}


def _get_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def _load_index(index_dir: str) -> tuple:
    if index_dir not in _index_cache:
        index_path = os.path.join(index_dir, "index.faiss")
        chunks_path = os.path.join(index_dir, "chunks.json")

        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"FAISS 索引文件不存在: {index_path}\n"
                f"请先运行: python -m app.rag.build_index"
            )

        index = faiss.read_index(index_path)
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        _index_cache[index_dir] = (index, chunks)

    return _index_cache[index_dir]


def search(query: str, index_dir: str, top_k: int = 5) -> list[dict]:
    """在 FAISS 知识库中检索与 query 最相似的 top_k 条知识"""
    model = _get_model()
    index, chunks = _load_index(index_dir)

    query_vec = model.encode([query], normalize_embeddings=True).astype(np.float32)

    actual_k = min(top_k, len(chunks))
    scores, indices = index.search(query_vec, actual_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and idx < len(chunks):
            results.append({
                "title": chunks[idx]["title"],
                "content": chunks[idx]["content"],
                "score": round(float(score), 4),
            })

    return results
