"""Zoya AI Platform — agent, LLM, tool, memory, embedding, and RAG subsystem.

Provides a unified interface for building AI agents with pluggable LLM
providers, a registry of built-in tools, conversational and semantic memory,
text embeddings, and retrieval-augmented generation (RAG) indexing.
"""

from __future__ import annotations

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# LLM providers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
from .agent import (
    Agent,
    AgentConfig,
    AgentError,
    PlanningAgent,
    create_agent,
)

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
from .embeddings import (
    EmbeddingError,
    TextEmbedding,
    TFIDFVectorizer,
    cosine_similarity,
    simple_tokenize,
)
from .llm import (
    AnthropicProvider,
    ChatMessage,
    LLMError,
    LLMProvider,
    LLMResponse,
    MockProvider,
    OpenAIProvider,
    create_provider,
)

# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------
from .memory import (
    AgentMemory,
    ConversationMemory,
    MemoryError,
    MemoryItem,
    SemanticMemory,
)

# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------
from .rag import (
    Document,
    DocumentChunker,
    RAGError,
    RAGIndex,
    RAGRetriever,
)

# ---------------------------------------------------------------------------
# Tool system
# ---------------------------------------------------------------------------
from .tools import (
    Calculator,
    FileReadTool,
    FileWriteTool,
    PythonExecuteTool,
    ShellTool,
    Tool,
    ToolError,
    ToolRegistry,
    WebSearchTool,
    tool,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
__all__ = [
    # LLM
    "LLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "MockProvider",
    "create_provider",
    "ChatMessage",
    "LLMResponse",
    "LLMError",
    # Tools
    "Tool",
    "ToolRegistry",
    "Calculator",
    "WebSearchTool",
    "FileReadTool",
    "FileWriteTool",
    "PythonExecuteTool",
    "ShellTool",
    "tool",
    "ToolError",
    # Memory
    "ConversationMemory",
    "SemanticMemory",
    "AgentMemory",
    "MemoryItem",
    "MemoryError",
    # Embeddings
    "cosine_similarity",
    "TFIDFVectorizer",
    "TextEmbedding",
    "simple_tokenize",
    "EmbeddingError",
    # Agent
    "Agent",
    "PlanningAgent",
    "AgentConfig",
    "create_agent",
    "AgentError",
    # RAG
    "Document",
    "DocumentChunker",
    "RAGIndex",
    "RAGRetriever",
    "RAGError",
]
