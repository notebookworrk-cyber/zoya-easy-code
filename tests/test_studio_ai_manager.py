"""Tests for Zoya Studio AI manager."""

import asyncio
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.core.ai_manager import (
    AIManager,
    MockProvider,
    Message,
    AIResponse,
)
from zoya_studio.security.crypto import CryptoManager


class FakeApp:
    def __init__(self):
        self.config = Config()
        self.config.ai.provider = "mock"
        self.project_manager = None


def test_mock_provider_generate():
    """Test mock provider generates response."""
    config = Config()
    provider = MockProvider(config)
    response = asyncio.run(provider.generate("hello"))
    assert isinstance(response, AIResponse)
    assert response.provider == "mock"
    assert len(response.content) > 0


def test_mock_provider_chat():
    """Test mock provider chat."""
    config = Config()
    provider = MockProvider(config)
    messages = [Message("user", "hi")]
    response = asyncio.run(provider.chat(messages))
    assert response.content


def test_ai_manager_init_mock():
    """Test AI manager initializes mock provider."""
    app = FakeApp()
    manager = AIManager(app)
    asyncio.run(manager.initialize())
    assert manager.provider is not None
    assert manager.provider.name == "mock"


def test_ai_manager_available_providers():
    """Test provider listing."""
    app = FakeApp()
    manager = AIManager(app)
    providers = manager.available_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "gemini" in providers
    assert "ollama" in providers
    assert "mock" in providers


def test_ai_manager_set_provider():
    """Test changing provider."""
    app = FakeApp()
    manager = AIManager(app)
    asyncio.run(manager.initialize())
    manager.set_provider("ollama")
    assert manager.config.ai.provider == "ollama"
    assert manager.provider.name == "ollama"


def test_ai_manager_send_message():
    """Test sending message."""
    app = FakeApp()
    manager = AIManager(app)
    asyncio.run(manager.initialize())
    response = asyncio.run(manager.send_message("hello"))
    assert response.content
    assert len(manager.get_conversation()) >= 2


def test_ai_manager_clear():
    """Test clearing conversation."""
    app = FakeApp()
    manager = AIManager(app)
    asyncio.run(manager.initialize())
    asyncio.run(manager.send_message("test"))
    manager.clear_conversation()
    assert len(manager.get_conversation()) == 1


def test_ai_manager_analyze_code():
    """Test code analysis."""
    app = FakeApp()
    manager = AIManager(app)
    asyncio.run(manager.initialize())
    response = asyncio.run(manager.analyze_code("print 'hi'", "explain"))
    assert response.content
