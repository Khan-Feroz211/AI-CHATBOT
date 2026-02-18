import numpy as np

from src.ml.local.embedder import LocalEmbedder


def test_fallback_embeddings_are_deterministic():
    embedder = LocalEmbedder()
    embedder.model = "fallback"

    text = "Karachi wholesale rate list"
    emb1 = embedder.embed(text, use_cache=False)
    emb2 = embedder.embed(text, use_cache=False)

    assert emb1.shape == emb2.shape
    assert np.allclose(emb1, emb2)
