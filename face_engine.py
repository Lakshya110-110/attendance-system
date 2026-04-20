"""
face_engine.py - Simulated face embedding + cosine similarity matching
No heavy ML required; embeddings are random 128-dim vectors stored as JSON.
In production replace generate_embedding() with a real model (DeepFace, etc.)
"""

import json
import math
import random
from typing import List, Optional

EMBEDDING_DIM = 128
SIMILARITY_THRESHOLD = 0.80  # minimum cosine similarity to accept


def generate_embedding(seed: Optional[int] = None) -> List[float]:
    """
    Simulate a 128-dim face embedding.
    Using a fixed seed produces a deterministic embedding for the same person.
    """
    rng = random.Random(seed)
    vec = [rng.gauss(0, 1) for _ in range(EMBEDDING_DIM)]
    return _normalise(vec)


def _normalise(vec: List[float]) -> List[float]:
    """L2-normalise a vector."""
    magnitude = math.sqrt(sum(x * x for x in vec))
    if magnitude == 0:
        return vec
    return [x / magnitude for x in vec]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two (already normalised) vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    # Clamp to [-1, 1] to avoid floating-point drift
    return max(-1.0, min(1.0, dot))


def embedding_to_str(embedding: List[float]) -> str:
    return json.dumps(embedding)


def str_to_embedding(s: str) -> List[float]:
    return json.loads(s)


def verify_face(stored_embedding_str: str, submitted_embedding: List[float]) -> dict:
    """
    Compare a submitted embedding against the stored one.
    Returns {'match': bool, 'score': float}
    """
    stored = str_to_embedding(stored_embedding_str)
    submitted_norm = _normalise(submitted_embedding)
    score = cosine_similarity(stored, submitted_norm)
    return {"match": score >= SIMILARITY_THRESHOLD, "score": round(score, 4)}
