"""
Lightweight embedding generator for local CPU usage
"""

import numpy as np
from pathlib import Path
import logging
from typing import List, Optional
import hashlib

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available, using deterministic fallback embeddings")

class LocalEmbedder:
    """Lightweight embedder for local CPU usage"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_onnx: bool = False):
        self.model_name = model_name
        self.use_onnx = use_onnx and self._check_onnx_available()
        self.model = None
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        self.cache_dir = Path("./data/embeddings_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _check_onnx_available(self):
        """Check if ONNX is available"""
        try:
            import onnxruntime
            return True
        except ImportError:
            return False
            
    def load(self):
        """Load the model"""
        if self.model is None:
            try:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    logger.info(f"Loading embedding model: {self.model_name}")
                    self.model = SentenceTransformer(self.model_name)
                    self.dimension = self.model.get_sentence_embedding_dimension()
                else:
                    # Fallback mode keeps deterministic behavior to avoid unstable similarity.
                    logger.warning("Using deterministic hash-based fallback embeddings")
                    self.model = "fallback"
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
                
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
        
    def _get_cached(self, key: str) -> Optional[np.ndarray]:
        """Get cached embedding"""
        cache_file = self.cache_dir / f"{key}.npy"
        if cache_file.exists():
            return np.load(cache_file)
        return None
        
    def _cache_embedding(self, key: str, embedding: np.ndarray):
        """Cache embedding"""
        cache_file = self.cache_dir / f"{key}.npy"
        np.save(cache_file, embedding)

    def _fallback_embedding(self, text: str) -> np.ndarray:
        """Generate deterministic fallback embedding from text hash."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        bytes_needed = self.dimension * 4
        buffer = bytearray()
        counter = 0
        while len(buffer) < bytes_needed:
            block = hashlib.sha256(digest + counter.to_bytes(4, "big")).digest()
            buffer.extend(block)
            counter += 1

        values = np.frombuffer(bytes(buffer[:bytes_needed]), dtype=np.uint32).astype(np.float32)
        normalized = (values / np.float32(2**32)) * 2.0 - 1.0
        norm = np.linalg.norm(normalized)
        if norm == 0:
            return np.zeros(self.dimension, dtype=np.float32)
        return (normalized / norm).astype(np.float32)
        
    def embed(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Generate embedding for single text"""
        if use_cache:
            cache_key = self._get_cache_key(text)
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
                
        if self.model is None:
            self.load()
            
        if SENTENCE_TRANSFORMERS_AVAILABLE and self.model != "fallback":
            embedding = self.model.encode(text)
        else:
            embedding = self._fallback_embedding(text)
            
        if use_cache:
            self._cache_embedding(cache_key, embedding)
            
        return embedding
        
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for batch of texts"""
        if self.model is None:
            self.load()
            
        if SENTENCE_TRANSFORMERS_AVAILABLE and self.model != "fallback":
            return self.model.encode(texts, batch_size=batch_size)
        else:
            return np.array([self._fallback_embedding(text) for text in texts])
            
    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = self.embed(text1)
        emb2 = self.embed(text2)
        
        # Cosine similarity
        dot = np.dot(emb1, emb2)
        norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)
        
        if norm == 0:
            return 0
        return float(dot / norm)
