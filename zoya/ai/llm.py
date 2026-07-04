"""LLM Provider Abstraction for the Zoya AI Platform.

Provides a provider-agnostic interface for interacting with various LLM APIs
including OpenAI, Anthropic, and a mock provider for testing.
"""

import os
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TypedDict


class LLMError(Exception):
    """Base exception for LLM operations."""

    pass


class ChatMessage(TypedDict):
    role: str
    content: str


class LLMResponse(TypedDict):
    content: str
    usage: dict
    model: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: list[ChatMessage], **kwargs) -> LLMResponse: ...

    @abstractmethod
    def stream(self, messages: list[ChatMessage], **kwargs) -> Iterator[str]: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...


class MockProvider(LLMProvider):
    """Mock provider for testing with configurable canned responses.

    The `responses` dict maps substring patterns (matched against the last
    user message) to reply strings. If no pattern matches, a generic
    response is returned.
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        model: str = "mock-model",
    ):
        self.responses = responses or {}
        self.model = model

    def chat(self, messages: list[ChatMessage], **kwargs) -> LLMResponse:
        last_content = messages[-1]["content"] if messages else ""
        content = None
        for pattern, response in self.responses.items():
            if pattern in last_content:
                content = response
                break
        if content is None:
            content = f"Mock response to: {last_content[:50]}..."
        return LLMResponse(
            content=content,
            usage={
                "prompt_tokens": self.count_tokens(last_content),
                "completion_tokens": self.count_tokens(content),
                "total_tokens": self.count_tokens(last_content)
                + self.count_tokens(content),
            },
            model=self.model,
        )

    def stream(self, messages: list[ChatMessage], **kwargs) -> Iterator[str]:
        response = self.chat(messages, **kwargs)
        for word in response["content"].split():
            yield word + " "

    def count_tokens(self, text: str) -> int:
        return len(text.split()) + len(text) // 4


class OpenAIProvider(LLMProvider):
    """OpenAI API provider.

    Configurable via api_key, model (default "gpt-4o"), temperature,
    and max_tokens. Falls back to the OPENAI_API_KEY environment variable
    if no key is provided.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise LLMError("OpenAI API key is required")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
            return self._client
        except ImportError:
            raise LLMError(
                "openai package is not installed. Install it with: pip install openai"
            ) from None
        except Exception as e:
            raise LLMError(f"Failed to initialize OpenAI client: {e}") from e

    def chat(self, messages: list[ChatMessage], **kwargs) -> LLMResponse:
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            choice = response.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                model=response.model,
            )
        except Exception as e:
            raise LLMError(f"OpenAI chat error: {e}") from e

    def stream(self, messages: list[ChatMessage], **kwargs) -> Iterator[str]:
        client = self._get_client()
        try:
            stream = client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=True,
            )
            for chunk in stream:
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise LLMError(f"OpenAI stream error: {e}") from e

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            return len(text.split()) + len(text) // 4


class AnthropicProvider(LLMProvider):
    """Anthropic API provider.

    Configurable via api_key, model (default "claude-sonnet-4-20250514"),
    temperature, and max_tokens. Falls back to the ANTHROPIC_API_KEY
    environment variable if no key is provided.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise LLMError("Anthropic API key is required")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self.api_key)
            return self._client
        except ImportError:
            raise LLMError(
                "anthropic package is not installed. Install it with: pip install anthropic"
            ) from None
        except Exception as e:
            raise LLMError(f"Failed to initialize Anthropic client: {e}") from e

    def chat(self, messages: list[ChatMessage], **kwargs) -> LLMResponse:
        client = self._get_client()
        system = None
        chat_messages = messages
        if messages and messages[0]["role"] == "system":
            system = messages[0]["content"]
            chat_messages = messages[1:]
        try:
            response = client.messages.create(
                model=kwargs.get("model", self.model),
                messages=chat_messages,
                system=system,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            return LLMResponse(
                content=response.content[0].text,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
                model=response.model,
            )
        except Exception as e:
            raise LLMError(f"Anthropic chat error: {e}") from e

    def stream(self, messages: list[ChatMessage], **kwargs) -> Iterator[str]:
        client = self._get_client()
        system = None
        chat_messages = messages
        if messages and messages[0]["role"] == "system":
            system = messages[0]["content"]
            chat_messages = messages[1:]
        try:
            with client.messages.stream(
                model=kwargs.get("model", self.model),
                messages=chat_messages,
                system=system,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            ) as stream:
                yield from stream.text_stream
        except Exception as e:
            raise LLMError(f"Anthropic stream error: {e}") from e

    def count_tokens(self, text: str) -> int:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.api_key)
            return client.count_tokens(text)
        except ImportError:
            return len(text.split()) + len(text) // 4


def create_provider(provider: str = "mock", **kwargs) -> LLMProvider:
    """Factory function to create an LLM provider instance.

    Args:
        provider: One of "mock", "openai", or "anthropic".
        **kwargs: Provider-specific configuration passed to the constructor.

    Returns:
        An initialized LLMProvider instance.

    Raises:
        LLMError: If the provider name is unknown.
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock": MockProvider,
    }
    if provider not in providers:
        raise LLMError(
            f"Unknown provider: '{provider}'. "
            f"Available providers: {list(providers.keys())}"
        )
    return providers[provider](**kwargs)
