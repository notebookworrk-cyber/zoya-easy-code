"""AI provider plugin system.

The Zoya CLI supports multiple AI providers through a lightweight plugin
interface. Each provider implements :class:`AIProvider` and registers itself
with :func:`register_provider`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AIResponse:
    content: str
    model: str = ""
    provider: str = ""
    usage: dict[str, int] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base for every AI provider plugin."""

    name: str = ""
    """Short identifier used in config (e.g. ``"openai"``)."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIResponse: ...

    @abstractmethod
    def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIResponse: ...

    def explain_code(self, code: str, context: str = "") -> AIResponse:
        prompt = f"Explain this code:\n\n```\n{code}\n```\n\n{context}"
        return self.complete(prompt, temperature=0.1)

    def debug_error(self, error_msg: str, code: str = "") -> AIResponse:
        prompt = f"I encountered this error:\n\n{error_msg}\n\n"
        if code:
            prompt += f"In code:\n\n```\n{code}\n```\n\n"
        prompt += "Please diagnose and suggest fixes."
        return self.complete(prompt, temperature=0.1)

    def review_code(self, code: str) -> AIResponse:
        prompt = f"Review this code for bugs, issues, and improvements:\n\n```\n{code}\n```"
        return self.complete(prompt, temperature=0.1)

    def optimize_code(self, code: str) -> AIResponse:
        prompt = f"Suggest performance optimizations for this code:\n\n```\n{code}\n```"
        return self.complete(prompt, temperature=0.1)

    def generate_code(self, specification: str) -> AIResponse:
        prompt = f"Write code based on this specification:\n\n{specification}"
        return self.complete(prompt, temperature=0.3, max_tokens=4096)

    def generate_docs(self, code: str) -> AIResponse:
        prompt = f"Generate documentation for this code:\n\n```\n{code}\n```"
        return self.complete(prompt, temperature=0.2, max_tokens=4096)

    def generate_tests(self, code: str) -> AIResponse:
        prompt = f"Write comprehensive tests for this code:\n\n```\n{code}\n```"
        return self.complete(prompt, temperature=0.3, max_tokens=4096)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.name:
            register_provider(cls.name, cls)


_providers: dict[str, type[AIProvider]] = {}


def register_provider(name: str, provider_cls: type[AIProvider]) -> None:
    _providers[name] = provider_cls


def get_provider(name: str, config: Any = None) -> AIProvider:
    cls = _providers.get(name)
    if cls is None:
        raise ValueError(f"Unknown AI provider `{name}`. Available: {list(_providers)}")
    return cls(config=config)


def list_providers() -> list[str]:
    return list(_providers)


from zoya_cli.ai.providers.mock import MockAIProvider
from zoya_cli.ai.providers.openai_compat import OpenAICompatProvider
