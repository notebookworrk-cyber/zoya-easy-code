import math
import re
from collections import Counter
from typing import List, Dict, Set


class EmbeddingError(Exception):
    pass


def simple_tokenize(text: str) -> List[str]:
    if not isinstance(text, str):
        raise EmbeddingError("Input must be a string")
    return re.findall(r"[a-z]+", text.lower())


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        raise EmbeddingError("Vectors must have the same dimension")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class TFIDFVectorizer:
    def __init__(self):
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._fitted = False

    def fit(self, documents: List[str]) -> None:
        if not documents:
            raise EmbeddingError("Must provide at least one document for fitting")
        vocab_set: Set[str] = set()
        doc_count = len(documents)
        df: Dict[str, int] = {}
        for doc in documents:
            tokens = simple_tokenize(doc)
            unique = set(tokens)
            vocab_set.update(unique)
            for token in unique:
                df[token] = df.get(token, 0) + 1
        self._vocab = {token: idx for idx, token in enumerate(sorted(vocab_set))}
        self._idf = {
            token: math.log((doc_count + 1) / (freq + 1)) + 1
            for token, freq in df.items()
        }
        self._fitted = True

    def transform(self, text: str) -> List[float]:
        if not self._fitted:
            raise EmbeddingError("Vectorizer has not been fitted yet")
        tokens = simple_tokenize(text)
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1
        vec = [0.0] * len(self._vocab)
        for token, count in tf.items():
            if token in self._vocab:
                idx = self._vocab[token]
                tf_val = count / max_tf
                vec[idx] = tf_val * self._idf.get(token, 1.0)
        return vec

    def vocabulary_size(self) -> int:
        if not self._fitted:
            return 0
        return len(self._vocab)


class TextEmbedding:
    def __init__(self, dimension: int = 128):
        if dimension < 1:
            raise EmbeddingError("Dimension must be positive")
        self._dimension = dimension
        self._vectorizer = TFIDFVectorizer()
        self._fitted = False

    def _pad_or_truncate(self, vec: List[float]) -> List[float]:
        if len(vec) >= self._dimension:
            return vec[:self._dimension]
        return vec + [0.0] * (self._dimension - len(vec))

    def fit(self, texts: List[str]) -> None:
        self._vectorizer.fit(texts)
        self._fitted = True

    def embed(self, text: str) -> List[float]:
        if not self._fitted:
            raise EmbeddingError("Embedding model has not been fitted yet")
        raw = self._vectorizer.transform(text)
        return self._pad_or_truncate(raw)

    def similarity(self, a: str, b: str) -> float:
        if not self._fitted:
            raise EmbeddingError("Embedding model has not been fitted yet")
        vec_a = self.embed(a)
        vec_b = self.embed(b)
        return cosine_similarity(vec_a, vec_b)

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]
