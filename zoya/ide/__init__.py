"""Zoya AI-Assisted IDE module.

Provides AI-powered code completion, generation, review, refactoring,
debugging, and documentation generation for the Zoya programming language.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from zoya.ide.completion import (
    CompletionContext,
    CompletionItem,
    CompletionEngine,
    ZOYA_KEYWORDS,
    ZOYA_BUILTINS,
    ZOYA_SNIPPETS,
    STRING_METHODS,
    LIST_METHODS,
    DICT_METHODS,
)
from zoya.ide.generation import (
    GenerationConfig,
    CodeGenerator,
    CodeTemplate,
)
from zoya.ide.review import (
    REVIEW_RULES,
    ReviewIssue,
    ReviewResult,
    CodeReviewer,
)
from zoya.ide.refactor import (
    RefactoringOperation,
    RefactoringSuggestion,
    RefactoringEngine,
    get_available_refactorings,
)
from zoya.ide.debug import (
    DebugContext,
    DebugAnalysis,
    BugPattern,
    COMMON_BUG_PATTERNS,
    DebugAssistant,
)
from zoya.ide.docs import (
    DocConfig,
    DocSection,
    ApiReference,
    DocGenerator,
    parse_doc_comments,
    _extract_functions,
    _extract_classes,
    _extract_enums,
    _extract_interfaces,
    _format_fn_signature,
    _escape_html,
)

__version__ = "0.1.0"

__all__ = [
    "IDEAssistant",
    "create_ide_assistant",
    "CompletionContext",
    "CompletionItem",
    "CompletionEngine",
    "ZOYA_KEYWORDS",
    "ZOYA_BUILTINS",
    "ZOYA_SNIPPETS",
    "STRING_METHODS",
    "LIST_METHODS",
    "DICT_METHODS",
    "GenerationConfig",
    "CodeGenerator",
    "CodeTemplate",
    "REVIEW_RULES",
    "ReviewIssue",
    "ReviewResult",
    "CodeReviewer",
    "RefactoringOperation",
    "RefactoringSuggestion",
    "RefactoringEngine",
    "get_available_refactorings",
    "DebugContext",
    "DebugAnalysis",
    "BugPattern",
    "COMMON_BUG_PATTERNS",
    "DebugAssistant",
    "DocConfig",
    "DocSection",
    "ApiReference",
    "DocGenerator",
    "parse_doc_comments",
    "_extract_functions",
    "_extract_classes",
    "_extract_enums",
    "_extract_interfaces",
    "_format_fn_signature",
    "_escape_html",
]


class IDEAssistant:
    """Main IDE assistant combining all AI-powered tools."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._completion: Optional[CompletionEngine] = None
        self._generator: Optional[CodeGenerator] = None
        self._reviewer: Optional[CodeReviewer] = None
        self._refactor: Optional[RefactoringEngine] = None
        self._debug: Optional[DebugAssistant] = None
        self._docs: Optional[DocGenerator] = None

    @property
    def completion(self) -> CompletionEngine:
        if self._completion is None:
            provider = self._config.get("provider")
            self._completion = CompletionEngine(provider=provider)
        return self._completion

    @property
    def generator(self) -> CodeGenerator:
        if self._generator is None:
            cfg = GenerationConfig()
            provider = self._config.get("provider")
            if provider is not None:
                cfg.provider = provider
            if "temperature" in self._config:
                cfg.temperature = self._config["temperature"]
            if "style" in self._config:
                cfg.style = self._config["style"]
            self._generator = CodeGenerator(config=cfg)
        return self._generator

    @property
    def reviewer(self) -> CodeReviewer:
        if self._reviewer is None:
            provider = self._config.get("provider")
            self._reviewer = CodeReviewer(provider=provider)
        return self._reviewer

    @property
    def refactor(self) -> RefactoringEngine:
        if self._refactor is None:
            self._refactor = RefactoringEngine()
        return self._refactor

    @property
    def debug(self) -> DebugAssistant:
        if self._debug is None:
            provider = self._config.get("provider")
            self._debug = DebugAssistant(provider=provider)
        return self._debug

    @property
    def docs(self) -> DocGenerator:
        if self._docs is None:
            cfg = DocConfig()
            doc_config = self._config.get("docs", {})
            if isinstance(doc_config, dict):
                if "include_private" in doc_config:
                    cfg.include_private = doc_config["include_private"]
                if "format" in doc_config:
                    cfg.format = doc_config["format"]
                if "include_source" in doc_config:
                    cfg.include_source = doc_config["include_source"]
                if "ai_enhance" in doc_config:
                    cfg.ai_enhance = doc_config["ai_enhance"]
            provider = self._config.get("provider")
            self._docs = DocGenerator(config=cfg, provider=provider)
        return self._docs


def create_ide_assistant(config: Optional[Dict[str, Any]] = None) -> IDEAssistant:
    """Create a fully initialized IDEAssistant with default or custom configuration.

    Args:
        config: Optional dictionary with configuration keys:
            - provider: An LLMProvider instance to use across engines
            - temperature: Code generation temperature (default: 0.3)
            - style: Code generation style ("standard", "compact", "verbose")
            - docs: Dict of DocConfig options (include_private, format, etc.)

    Returns:
        A configured IDEAssistant instance with all engines ready.
    """
    return IDEAssistant(config=config)
