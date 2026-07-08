# Zoya Studio AI Provider Integration

Zoya Studio uses a provider-independent AI architecture. All providers implement the same interface, making it easy to switch or add new ones.

## Supported Providers

| Provider | Class | Requires |
|----------|-------|----------|
| OpenAI | `OpenAIProvider` | `openai` package + API key |
| Anthropic | `AnthropicProvider` | `anthropic` package + API key |
| Google Gemini | `GeminiProvider` | `google-generativeai` + API key |
| Ollama | `OllamaProvider` | Ollama running locally |
| LM Studio | `LMStudioProvider` | LM Studio running locally |
| OpenRouter | `OpenRouterProvider` | `openai` package + API key |
| Custom | `CustomProvider` | OpenAI-compatible endpoint |
| Mock | `MockProvider` | Nothing (built-in) |

## Architecture

```
BaseAIProvider (ABC)
├── generate(prompt) -> AIResponse
├── chat(messages) -> AIResponse
└── stream(messages) -> AsyncGenerator[str, None]

OpenAIProvider / AnthropicProvider / GeminiProvider /
OllamaProvider / LMStudioProvider / OpenRouterProvider /
CustomProvider / MockProvider
```

## Configuration

Configure in Settings (F1) or via config file:

```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "base_url": "",
    "api_key": "<encrypted>",
    "temperature": 0.7,
    "max_tokens": 4096,
    "stream": true,
    "use_local_fallback": true,
    "systems_prompt": "You are Zoya Studio AI..."
  }
}
```

## Adding a New Provider

Subclass `BaseAIProvider`:

```python
from zoya_studio.core.ai_manager import BaseAIProvider, AIResponse, Message


class MyProvider(BaseAIProvider):
    def __init__(self, config, crypto=None):
        super().__init__(config, crypto)
        self.name = "myprovider"

    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        messages = [Message("user", prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[Message], **kwargs) -> AIResponse:
        # Call your API here
        return AIResponse(
            content="response text",
            model="my-model",
            provider=self.name,
        )

    async def stream(self, messages: list[Message], **kwargs):
        # Yield tokens
        yield "token1"
        yield "token2"
```

Register it:

```python
from zoya_studio.core.ai_manager import AIManager
AIManager.PROVIDERS["myprovider"] = MyProvider
```

## Security

API keys are:
1. Encrypted with Fernet before storage
2. Decrypted only at runtime when needed
3. Never logged or exposed in UI
4. Stored at `~/.zoya/studio/credentials/`

## Fallback

If a provider fails (network error, invalid key), and `use_local_fallback` is enabled, Zoya Studio automatically uses `MockProvider` to ensure the UI remains responsive.

## Streaming

When `stream: true` and a `stream_callback` is provided, responses are streamed token-by-token to the UI for a live chat experience.

## Context

AI requests include project context (architecture, goals, current file) automatically when available. This helps the AI give more relevant responses.
