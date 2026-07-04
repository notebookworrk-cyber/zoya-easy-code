from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    _clients: dict[str, Any] = {}

    def model(provider: str, api_key: str = "", base_url: str = "") -> Any:
        provider = provider.lower()

        if provider == "gemini":
            return _gemini_model(api_key)
        elif provider in ("openai", "gpt"):
            return _openai_model(api_key, base_url)
        elif provider == "ollama":
            return _ollama_model(base_url)
        elif provider == "lmstudio":
            return _lmstudio_model(base_url)
        else:
            raise ValueError(
                f"Unknown AI provider: {provider}. Supported: gemini, openai, ollama, lmstudio"
            )

    def _gemini_model(api_key: str) -> dict[str, Any]:
        try:
            import google.generativeai as genai

            if api_key:
                genai.configure(api_key=api_key)

            def ask(prompt: str) -> str:
                try:
                    model_instance = genai.GenerativeModel("gemini-pro")
                    response = model_instance.generate_content(prompt)
                    return response.text
                except Exception as e:
                    return f"Error: {e}"

            return {"ask": ask, "provider": "gemini"}
        except ImportError:
            return {
                "ask": lambda p: "[gemini] Install: pip install google-generativeai",
                "provider": "gemini",
            }

    def _openai_model(api_key: str, base_url: str = "") -> dict[str, Any]:
        try:
            import openai

            client_kwargs: dict[str, Any] = {}
            if api_key:
                client_kwargs["api_key"] = api_key
            if base_url:
                client_kwargs["base_url"] = base_url

            client = (
                openai.OpenAI(**client_kwargs) if client_kwargs else openai.OpenAI()
            )

            def ask(prompt: str) -> str:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message.content or ""
                except Exception as e:
                    return f"Error: {e}"

            return {"ask": ask, "provider": "openai"}
        except ImportError:
            return {
                "ask": lambda p: "[openai] Install: pip install openai",
                "provider": "openai",
            }

    def _ollama_model(base_url: str = "") -> dict[str, Any]:
        url = base_url or "http://localhost:11434"

        def ask(prompt: str) -> str:
            try:
                import json
                from urllib.request import Request, urlopen

                data = json.dumps(
                    {
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                    }
                ).encode()
                req = Request(
                    f"{url}/api/generate",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                    return result.get("response", "")
            except Exception as e:
                return f"Error: {e}"

        return {"ask": ask, "provider": "ollama"}

    def _lmstudio_model(base_url: str = "") -> dict[str, Any]:
        url = base_url or "http://localhost:1234"

        def ask(prompt: str) -> str:
            try:
                import json
                from urllib.request import Request, urlopen

                data = json.dumps(
                    {
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    }
                ).encode()
                req = Request(
                    f"{url}/v1/chat/completions",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())
                    return result["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Error: {e}"

        return {"ask": ask, "provider": "lmstudio"}

    funcs = {
        "model": model,
    }

    return ZoyaModule("ai", funcs)
