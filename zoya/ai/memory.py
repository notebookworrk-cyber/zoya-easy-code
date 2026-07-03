import json
import time
import math
from typing import Any, Dict, List, Optional, TypedDict

from zoya.ai.embeddings import TextEmbedding, cosine_similarity, simple_tokenize, EmbeddingError


class MemoryItem(TypedDict):
    role: str
    content: str
    timestamp: float
    metadata: dict


class MemoryError(Exception):
    pass


class ConversationMemory:
    def __init__(self, max_tokens: int = 0):
        self._history: List[MemoryItem] = []
        self._max_tokens = max_tokens

    def add(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        item: MemoryItem = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self._history.append(item)
        if self._max_tokens > 0 and self.count_tokens() > self._max_tokens:
            self.summarize()

    def get_history(self) -> List[MemoryItem]:
        return list(self._history)

    def get_recent(self, n: int) -> List[MemoryItem]:
        if n < 1:
            raise MemoryError("Number of recent items must be positive")
        return list(self._history[-n:])

    def clear(self) -> None:
        self._history.clear()

    def count_tokens(self) -> int:
        total_chars = sum(len(item["content"]) + len(item["role"]) for item in self._history)
        return math.ceil(total_chars / 4)

    def summarize(self, max_tokens: int = 1000) -> None:
        if len(self._history) <= 1:
            return
        target = self._max_tokens if self._max_tokens > 0 else max_tokens
        while self.count_tokens() > target and len(self._history) > 1:
            oldest = self._history.pop(0)
            char_limit = self._max_tokens * 4 if self._max_tokens > 0 else max_tokens * 4
            summary_content = oldest["content"][:char_limit]
            if len(oldest["content"]) > char_limit:
                summary_content += "..."
            self._history.insert(0, {
                "role": "system",
                "content": f"[Summary of earlier {oldest['role']} message]: {summary_content}",
                "timestamp": oldest["timestamp"],
                "metadata": {"summarized": True, "original_role": oldest["role"]},
            })
            break

    def set_max_tokens(self, limit: int) -> None:
        if limit < 0:
            raise MemoryError("Max tokens limit must be non-negative")
        self._max_tokens = limit
        if limit > 0 and self.count_tokens() > limit:
            self.summarize()


class SemanticMemory:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, dict] = {}
        self._embedder: Optional[TextEmbedding] = None

    def _ensure_embedder(self) -> TextEmbedding:
        if self._embedder is None:
            self._embedder = TextEmbedding()
            if self._data:
                self._embedder.fit(list(self._data.keys()))
            else:
                self._embedder.fit(["placeholder"])
        return self._embedder

    def store(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        if not isinstance(key, str) or not key:
            raise MemoryError("Key must be a non-empty string")
        self._data[key] = value
        self._metadata[key] = metadata or {}
        if self._embedder is not None:
            self._embedder.fit(list(self._data.keys()))

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self._data:
            return []
        if k < 1:
            raise MemoryError("k must be positive")
        embedder = self._ensure_embedder()
        query_vec = embedder.embed(query)
        scored = []
        for key in self._data:
            key_vec = embedder.embed(key)
            score = cosine_similarity(query_vec, key_vec)
            scored.append((score, key))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, key in scored[:k]:
            if score > 0:
                results.append({
                    "key": key,
                    "value": self._data[key],
                    "metadata": self._metadata.get(key, {}),
                    "score": score,
                })
        return results

    def get(self, key: str) -> Any:
        if key not in self._data:
            raise MemoryError(f"Key '{key}' not found")
        return self._data[key]

    def delete(self, key: str) -> None:
        if key not in self._data:
            raise MemoryError(f"Key '{key}' not found")
        del self._data[key]
        self._metadata.pop(key, None)

    def list(self) -> List[str]:
        return list(self._data.keys())

    def clear(self) -> None:
        self._data.clear()
        self._metadata.clear()
        self._embedder = None


class AgentMemory:
    def __init__(self):
        self.conversation = ConversationMemory()
        self.knowledge = SemanticMemory()

    def save(self, filepath: str) -> None:
        serialized = {
            "conversation": {
                "history": self.conversation.get_history(),
                "max_tokens": self.conversation._max_tokens,
            },
            "knowledge": {
                "data": self.knowledge._data,
                "metadata": self.knowledge._metadata,
            },
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False, default=str)

    def load(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            serialized = json.load(f)
        conv_data = serialized.get("conversation", {})
        self.conversation = ConversationMemory(max_tokens=conv_data.get("max_tokens", 0))
        for item in conv_data.get("history", []):
            self.conversation._history.append({
                "role": item["role"],
                "content": item["content"],
                "timestamp": item.get("timestamp", time.time()),
                "metadata": item.get("metadata", {}),
            })
        know_data = serialized.get("knowledge", {})
        self.knowledge = SemanticMemory()
        self.knowledge._data = dict(know_data.get("data", {}))
        self.knowledge._metadata = dict(know_data.get("metadata", {}))
