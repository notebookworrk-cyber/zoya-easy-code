"""Mock AI provider for offline development and testing."""

from __future__ import annotations

from typing import Any

from zoya_cli.ai import AIProvider, AIResponse


class MockAIProvider(AIProvider):
    name = "mock"

    def __init__(self, config: Any = None) -> None:
        self._config = config

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIResponse:
        last = messages[-1]["content"] if messages else ""
        return AIResponse(
            content=f'[mock reply] You said: "{last[:80]}{"..." if len(last) > 80 else ""}"',
            model=model or "mock-1",
            provider="mock",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIResponse:
        return AIResponse(
            content=f'[mock completion based on: "{prompt[:80]}{"..." if len(prompt) > 80 else ""}"]',
            model=model or "mock-1",
            provider="mock",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )
