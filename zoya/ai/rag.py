"""Retrieval-augmented generation pipeline for context-aware AI responses."""

from __future__ import annotations

import uuid
from typing import Any, TypedDict

from .embeddings import TextEmbedding, cosine_similarity


class Document(TypedDict, total=False):
    text: str
    metadata: dict[str, Any]
    id: str


class RAGError(Exception):
    pass


class DocumentChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size < 1:
            raise RAGError("chunk_size must be positive")
        if overlap < 0:
            raise RAGError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise RAGError("overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_into_sentences(self, text: str) -> list[str]:
        sentences: list[str] = []
        current: list[str] = []
        for char in text:
            current.append(char)
            if char in ".!?\n" and len("".join(current).strip()) > 0:
                sentence = "".join(current).strip()
                if sentence:
                    sentences.append(sentence)
                current = []
        remaining = "".join(current).strip()
        if remaining:
            sentences.append(remaining)
        return sentences

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Document]:
        if not isinstance(text, str) or not text.strip():
            return []

        meta = dict(metadata) if metadata else {}
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks: list[Document] = []
        current_chunk: list[str] = []
        current_size = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_size + sentence_len > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(Document(text=chunk_text, metadata=dict(meta), id=str(uuid.uuid4())))

                overlap_sentences: list[str] = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    s_len = len(s)
                    if overlap_size + s_len > self.overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_size += s_len
                current_chunk = list(overlap_sentences)
                current_size = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_len

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Document(text=chunk_text, metadata=dict(meta), id=str(uuid.uuid4())))

        return chunks

    def chunk_documents(self, docs: list[tuple[str, dict[str, Any]]]) -> list[Document]:
        all_chunks: list[Document] = []
        for text, metadata in docs:
            all_chunks.extend(self.chunk(text, metadata))
        return all_chunks


class RAGIndex:
    def __init__(self, embedding_model: TextEmbedding | None = None) -> None:
        self._embedding_model = embedding_model or TextEmbedding()
        self._documents: dict[str, Document] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._all_texts: list[str] = []

    def add_document(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        if not isinstance(text, str) or not text.strip():
            raise RAGError("Document text must be a non-empty string")

        doc_id = str(uuid.uuid4())
        doc = Document(text=text, metadata=dict(metadata) if metadata else {}, id=doc_id)

        self._all_texts.append(text)

        if not self._embedding_model._fitted:
            self._embedding_model.fit(self._all_texts)

        embedding = self._embedding_model.embed(text)

        self._documents[doc_id] = doc
        self._embeddings[doc_id] = embedding
        return doc_id

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        for doc in docs:
            text = doc.get("text", "")
            if not isinstance(text, str) or not text.strip():
                continue
            doc_id = doc.get("id", str(uuid.uuid4()))
            if doc_id in self._documents:
                doc_id = str(uuid.uuid4())
            resolved = Document(text=text, metadata=dict(doc.get("metadata", {})), id=doc_id)
            self._all_texts.append(text)
            self._documents[doc_id] = resolved

        if not self._embedding_model._fitted:
            self._embedding_model.fit(self._all_texts)
        else:
            new_texts = [doc.get("text", "") for doc in docs if doc.get("text")]
            if new_texts:
                self._embedding_model.fit(self._all_texts)

        for doc_id, doc in list(self._documents.items()):
            if doc_id not in self._embeddings:
                self._embeddings[doc_id] = self._embedding_model.embed(doc.get("text", ""))

    def search(self, query: str, k: int = 5) -> list[tuple[Document, float]]:
        if not self._documents:
            return []
        if not isinstance(query, str) or not query.strip():
            raise RAGError("Query must be a non-empty string")
        if k < 1:
            raise RAGError("k must be positive")

        if not self._embedding_model._fitted:
            return []

        query_embedding = self._embedding_model.embed(query)

        scored: list[tuple[str, float]] = []
        for doc_id, doc_embedding in self._embeddings.items():
            score = cosine_similarity(query_embedding, doc_embedding)
            scored.append((doc_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_k = scored[:k]

        results: list[tuple[Document, float]] = []
        for doc_id, score in top_k:
            if doc_id in self._documents:
                results.append((self._documents[doc_id], score))

        return results

    def remove(self, doc_id: str) -> None:
        if doc_id in self._documents:
            removed_text = self._documents[doc_id].get("text", "")
            del self._documents[doc_id]
            self._embeddings.pop(doc_id, None)

            if removed_text in self._all_texts:
                self._all_texts.remove(removed_text)

                if self._embedding_model._fitted and self._all_texts:
                    self._embedding_model.fit(self._all_texts)
                    self._rebuild_embeddings()

    def clear(self) -> None:
        self._documents.clear()
        self._embeddings.clear()
        self._all_texts.clear()

    def count(self) -> int:
        return len(self._documents)

    def _rebuild_embeddings(self) -> None:
        self._embeddings.clear()
        for doc_id, doc in self._documents.items():
            self._embeddings[doc_id] = self._embedding_model.embed(doc.get("text", ""))


class RAGRetriever:
    def __init__(self, index: RAGIndex, system_prompt: str | None = None) -> None:
        if not isinstance(index, RAGIndex):
            raise RAGError("index must be a RAGIndex instance")
        self._index = index
        self._system_prompt = system_prompt or (
            "You are a helpful assistant with access to the following context documents. "
            "Use them to answer the user's question accurately."
        )

    def format_context(self, docs: list[tuple[Document, float]]) -> str:
        if not docs:
            return "No relevant documents found."

        parts: list[str] = ["Retrieved context:"]
        for i, (doc, score) in enumerate(docs, 1):
            source = doc.get("metadata", {}).get("source", "unknown")
            parts.append(f"[{i}] (relevance: {score:.4f}, source: {source})")
            parts.append(doc.get("text", ""))
            parts.append("")

        return "\n".join(parts)

    def query(self, query: str, k: int = 5) -> str:
        docs = self._index.search(query, k=k)
        context = self.format_context(docs)
        return f"{self._system_prompt}\n\n{context}\nUser question: {query}"

    def query_with_sources(self, query: str, k: int = 5) -> tuple[str, list[Document]]:
        results = self._index.search(query, k=k)
        context = self.format_context(results)

        sources: list[Document] = [doc for doc, _ in results]

        prompt = f"{self._system_prompt}\n\n{context}\nUser question: {query}"
        return prompt, sources
