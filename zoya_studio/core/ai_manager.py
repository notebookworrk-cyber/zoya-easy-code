"""AI integration manager for Zoya Studio."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable

from zoya_studio.core.config import Config
from zoya_studio.security.crypto import CryptoManager


@dataclass
class Message:
    """A chat message."""

    role: str
    content: str
    timestamp: str = ""


@dataclass
class AIResponse:
    """AI response."""

    content: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    finish_reason: str = ""


class BaseAIProvider(ABC):
    """Base class for AI providers."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        self.config = config
        self.crypto = crypto
        self.name = "base"

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Generate a response from a prompt."""
        raise NotImplementedError

    @abstractmethod
    async def chat(self, messages: list[Message], **kwargs: Any) -> AIResponse:
        """Chat with conversation history."""
        raise NotImplementedError

    @abstractmethod
    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncGenerator[str, None]:
        """Stream a response token by token."""
        raise NotImplementedError

    def get_api_key(self) -> str:
        """Get decrypted API key."""
        if self.crypto and self.config.ai.api_key:
            try:
                return self.crypto.decrypt(self.config.ai.api_key)
            except Exception:
                return self.config.ai.api_key
        return self.config.ai.api_key


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "openai"
        self.base_url = config.ai.base_url or "https://api.openai.com/v1"

    async def generate(self, prompt: str, **kwargs: Any) -> AIResponse:
        messages = [
            Message("system", self.config.ai.systems_prompt),
            Message("user", prompt),
        ]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[Message], **kwargs: Any) -> AIResponse:
        try:
            import openai

            client = openai.AsyncOpenAI(
                api_key=self.get_api_key(),
                base_url=self.base_url if self.config.ai.base_url else None,
            )

            response = await client.chat.completions.create(
                model=self.config.ai.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=self.config.ai.temperature,
                max_tokens=self.config.ai.max_tokens,
            )

            return AIResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                provider=self.name,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason or "",
            )
        except ImportError:
            return await self._fallback(messages)
        except Exception as e:
            if self.config.ai.use_local_fallback:
                return await self._fallback(messages, str(e))
            raise

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncGenerator[str, None]:
        try:
            import openai

            client = openai.AsyncOpenAI(
                api_key=self.get_api_key(),
                base_url=self.base_url if self.config.ai.base_url else None,
            )

            stream = await client.chat.completions.create(
                model=self.config.ai.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=self.config.ai.temperature,
                max_tokens=self.config.ai.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except ImportError:
            async for chunk in self._fallback_stream(messages):
                yield chunk
        except Exception:
            if self.config.ai.use_local_fallback:
                async for chunk in self._fallback_stream(messages):
                    yield chunk
            else:
                raise

    async def _fallback(self, messages: list[Message], error: str = "") -> AIResponse:
        """Local fallback when API unavailable."""
        prompt = messages[-1].content if messages else ""
        return AIResponse(
            content=MockProvider(self.config).generate(prompt).content,
            model="mock",
            provider="mock",
        )

    async def _fallback_stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        """Stream fallback response."""
        response = await self._fallback(messages)
        yield response.content


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "anthropic"
        self.base_url = config.ai.base_url or "https://api.anthropic.com"

    async def generate(self, prompt: str, **kwargs: Any) -> AIResponse:
        messages = [Message("user", prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[Message], **kwargs: Any) -> AIResponse:
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.get_api_key())

            system_msg = self.config.ai.systems_prompt
            conv_messages = [
                {"role": m.role, "content": m.content} for m in messages if m.role != "system"
            ]

            response = await client.messages.create(
                model=self.config.ai.model or "claude-3-sonnet-20240229",
                max_tokens=self.config.ai.max_tokens,
                system=system_msg,
                messages=conv_messages,
            )

            return AIResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                provider=self.name,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason or "",
            )
        except ImportError:
            return await self._fallback(messages)
        except Exception as e:
            if self.config.ai.use_local_fallback:
                return await self._fallback(messages, str(e))
            raise

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncGenerator[str, None]:
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.get_api_key())

            conv_messages = [
                {"role": m.role, "content": m.content} for m in messages if m.role != "system"
            ]

            stream = await client.messages.create(
                model=self.config.ai.model or "claude-3-sonnet-20240229",
                max_tokens=self.config.ai.max_tokens,
                system=self.config.ai.systems_prompt,
                messages=conv_messages,
                stream=True,
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.text:
                    yield chunk.delta.text
        except ImportError:
            async for chunk in self._fallback_stream(messages):
                yield chunk
        except Exception:
            if self.config.ai.use_local_fallback:
                async for chunk in self._fallback_stream(messages):
                    yield chunk
            else:
                raise

    async def _fallback(self, messages: list[Message], error: str = "") -> AIResponse:
        prompt = messages[-1].content if messages else ""
        return AIResponse(
            content=MockProvider(self.config).generate(prompt).content,
            model="mock",
            provider="mock",
        )

    async def _fallback_stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        response = await self._fallback(messages)
        yield response.content


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "gemini"
        self.base_url = config.ai.base_url or "https://generativelanguage.googleapis.com"

    async def generate(self, prompt: str, **kwargs: Any) -> AIResponse:
        messages = [Message("user", prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[Message], **kwargs: Any) -> AIResponse:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.get_api_key())
            model = genai.GenerativeModel(
                self.config.ai.model or "gemini-pro",
                system_instruction=self.config.ai.systems_prompt,
            )

            history = [
                {"role": m.role, "parts": [m.content]} for m in messages if m.role != "system"
            ]

            chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
            response = await chat.send_message_async(history[-1]["parts"][0])

            return AIResponse(
                content=response.text,
                model=self.config.ai.model or "gemini-pro",
                provider=self.name,
            )
        except ImportError:
            return await self._fallback(messages)
        except Exception as e:
            if self.config.ai.use_local_fallback:
                return await self._fallback(messages, str(e))
            raise

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncGenerator[str, None]:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.get_api_key())
            model = genai.GenerativeModel(
                self.config.ai.model or "gemini-pro",
                system_instruction=self.config.ai.systems_prompt,
            )

            prompt = messages[-1].content if messages else ""
            response = await model.generate_content_async(prompt, stream=True)

            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except ImportError:
            async for chunk in self._fallback_stream(messages):
                yield chunk
        except Exception:
            if self.config.ai.use_local_fallback:
                async for chunk in self._fallback_stream(messages):
                    yield chunk
            else:
                raise

    async def _fallback(self, messages: list[Message], error: str = "") -> AIResponse:
        prompt = messages[-1].content if messages else ""
        return AIResponse(
            content=MockProvider(self.config).generate(prompt).content,
            model="mock",
            provider="mock",
        )

    async def _fallback_stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        response = await self._fallback(messages)
        yield response.content


class OllamaProvider(BaseAIProvider):
    """Ollama local provider."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "ollama"
        self.base_url = config.ai.base_url or "http://localhost:11434"

    async def generate(self, prompt: str, **kwargs: Any) -> AIResponse:
        messages = [Message("user", prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[Message], **kwargs: Any) -> AIResponse:
        import urllib.request

        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.config.ai.model or "llama2",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                return AIResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=data.get("model", ""),
                    provider=self.name,
                )
        except Exception as e:
            if self.config.ai.use_local_fallback:
                return await self._fallback(messages, str(e))
            raise

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncGenerator[str, None]:
        import urllib.request

        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.config.ai.model or "llama2",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    if line.strip():
                        data = json.loads(line.decode())
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
        except Exception:
            if self.config.ai.use_local_fallback:
                async for chunk in self._fallback_stream(messages):
                    yield chunk
            else:
                raise

    async def _fallback(self, messages: list[Message], error: str = "") -> AIResponse:
        prompt = messages[-1].content if messages else ""
        return AIResponse(
            content=MockProvider(self.config).generate(prompt).content,
            model="mock",
            provider="mock",
        )

    async def _fallback_stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        response = await self._fallback(messages)
        yield response.content


class LMStudioProvider(OllamaProvider):
    """LM Studio local provider (OpenAI-compatible)."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "lmstudio"
        self.base_url = config.ai.base_url or "http://localhost:1234/v1"


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter provider (OpenAI-compatible)."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "openrouter"
        self.base_url = config.ai.base_url or "https://openrouter.ai/api/v1"


class CustomProvider(OpenAIProvider):
    """Custom OpenAI-compatible provider."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "custom"
        self.base_url = config.ai.base_url or "http://localhost:8080/v1"


class MockProvider(BaseAIProvider):
    """Local mock provider (no API key needed)."""

    def __init__(self, config: Config, crypto: CryptoManager | None = None):
        super().__init__(config, crypto)
        self.name = "mock"

    async def generate(self, prompt: str, **kwargs: Any) -> AIResponse:
        return AIResponse(
            content=self._respond(prompt),
            model="zoya-mock-1.0",
            provider="mock",
        )

    async def chat(self, messages: list[Message], **kwargs: Any) -> AIResponse:
        prompt = messages[-1].content if messages else ""
        return await self.generate(prompt, **kwargs)

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncGenerator[str, None]:
        response = await self._fallback(messages) if False else await self.chat(messages)
        yield response.content

    def _respond(self, prompt: str) -> str:
        """Generate a mock response."""
        p = prompt.lower()

        if "hello" in p or "hi" in p:
            return (
                "Hello! I'm Zoya Studio AI. I can help you write code, "
                "debug, explain concepts, and more. What would you like to do?"
            )

        if "explain" in p:
            return (
                "I'd explain this code in detail, but I'm running in mock mode. "
                "Configure an AI provider (OpenAI, Anthropic, Gemini, Ollama, etc.) "
                "in Settings to get real explanations."
            )

        if "create" in p or "build" in p or "generate" in p:
            return (
                "I can help create projects! With a real AI provider configured, "
                "I'll generate the files for you. Try the Templates panel to "
                "scaffold a project right now."
            )

        if "fix" in p or "error" in p or "debug" in p:
            return (
                "I can help fix errors! Connect an AI provider and I'll analyze "
                "your code and suggest fixes. In mock mode, I can still run "
                "the compiler to show you the errors."
            )

        if "optimize" in p:
            return (
                "Code optimization requires an AI provider. Connect one in Settings "
                "to get specific optimization suggestions."
            )

        return (
            f"I received your message: '{prompt[:100]}...'\n\n"
            f"I'm currently in mock mode (no API key configured). "
            f"To enable full AI capabilities, go to Settings (Ctrl+,) and configure "
            f"an AI provider with your API key. Your key will be stored encrypted."
        )


class AIManager:
    """Manages AI providers and conversations."""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
        "lmstudio": LMStudioProvider,
        "openrouter": OpenRouterProvider,
        "custom": CustomProvider,
        "mock": MockProvider,
    }

    def __init__(self, app: Any):
        self.app = app
        self.config = app.config if hasattr(app, "config") else Config.load()
        self.crypto = CryptoManager()
        self.provider: BaseAIProvider | None = None
        self.conversation: list[Message] = []
        self.system_prompt = self.config.ai.systems_prompt
        self._tasks: list[dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the AI provider."""
        provider_name = self.config.ai.provider
        if provider_name not in self.PROVIDERS:
            provider_name = "mock"

        provider_class = self.PROVIDERS[provider_name]
        self.provider = provider_class(self.config, self.crypto)
        self.conversation = [
            Message("system", self.system_prompt, ""),
        ]

    def set_provider(self, name: str) -> None:
        """Change the AI provider."""
        if name not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {name}")
        self.config.ai.provider = name
        self.config.save()
        provider_class = self.PROVIDERS[name]
        self.provider = provider_class(self.config, self.crypto)

    def available_providers(self) -> list[str]:
        """Get list of available providers."""
        return list(self.PROVIDERS.keys())

    async def send_message(
        self,
        content: str,
        stream_callback: Callable[[str], None] | None = None,
        context: str | None = None,
    ) -> AIResponse:
        """Send a message and get a response."""
        if not self.provider:
            await self.initialize()

        user_msg = Message("user", content, self._now())
        self.conversation.append(user_msg)

        messages = list(self.conversation)
        if context:
            messages.insert(1, Message("system", f"Context:\n{context}", ""))

        if self.config.ai.stream and stream_callback and hasattr(self.provider, "stream"):
            collected = []
            async for chunk in self.provider.stream(messages):
                collected.append(chunk)
                stream_callback(chunk)

            response_content = "".join(collected)
            response = AIResponse(
                content=response_content,
                model=self.config.ai.model,
                provider=self.provider.name,
            )
        else:
            response = await self.provider.chat(messages)

        self.conversation.append(Message("assistant", response.content, self._now()))

        if getattr(self.app, "project_manager", None) is not None:
            self.app.project_manager.add_conversation("user", content)
            self.app.project_manager.add_conversation("assistant", response.content)

        return response

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation = [Message("system", self.system_prompt, "")]

    def get_conversation(self) -> list[Message]:
        """Get conversation history."""
        return self.conversation

    def run_task(self, task: str) -> None:
        """Queue an AI task."""
        self._tasks.append(
            {
                "task": task,
                "status": "queued",
                "created": self._now(),
            }
        )

    def get_tasks(self) -> list[dict[str, Any]]:
        """Get queued tasks."""
        return self._tasks

    def _now(self) -> str:
        from datetime import datetime

        return datetime.now().isoformat()

    async def analyze_code(self, code: str, action: str = "explain") -> AIResponse:
        """Analyze code with AI."""
        prompts = {
            "explain": f"Explain this code:\n\n{code}",
            "fix": f"Fix any errors in this code:\n\n{code}",
            "optimize": f"Optimize this code:\n\n{code}",
            "document": f"Generate documentation for this code:\n\n{code}",
            "test": f"Generate tests for this code:\n\n{code}",
            "review": f"Review this code for issues:\n\n{code}",
        }
        prompt = prompts.get(action, prompts["explain"])
        return await self.send_message(prompt)

    async def generate_commit_message(self, diff: str) -> AIResponse:
        """Generate a commit message from diff."""
        prompt = (
            "Generate a concise git commit message (conventional commits format) "
            f"for this diff:\n\n{diff[:4000]}"
        )
        return await self.send_message(prompt)

    async def search_codebase(self, query: str, files: list[str] | None = None) -> AIResponse:
        """Search codebase with AI."""
        context = ""
        if files:
            context = f"Relevant files: {', '.join(files[:20])}"
        prompt = f"Search the codebase for: {query}\n{context}"
        return await self.send_message(prompt)
