"""OpenAI-compatible AI provider (works with OpenAI, Ollama, LiteLLM, etc.)."""

from __future__ import annotations

import json
from typing import Any

from zoya_cli.ai import AIProvider, AIResponse


class OpenAICompatProvider(AIProvider):
    name = "openai"

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._api_key: str = ""
        self._api_base: str = "https://api.openai.com/v1"
        self._model: str = "gpt-4o-mini"
        if config is not None:
            self._api_key = config.get("ai.api_key", "")
            self._api_base = config.get("ai.api_base", "https://api.openai.com/v1")
            self._model = config.get("ai.model", "gpt-4o-mini")

    def _request(self, payload: dict) -> dict:
        import urllib.request
        import urllib.error

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"}
        req = urllib.request.Request(
            f"{self._api_base}/chat/completions",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIResponse:
        if not self._api_key:
            return AIResponse(
                content="No API key configured. Run `zoya config set ai.api_key <key>`.",
                provider="openai",
            )
        payload = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        data = self._request(payload)
        choice = data["choices"][0]
        return AIResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider="openai",
            usage=data.get("usage", {}),
        )

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AIResponse:
        messages = [{"role": "user", "content": prompt}]
        return self.chat(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
