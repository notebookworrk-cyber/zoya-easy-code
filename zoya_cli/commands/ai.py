"""AI command group: zoya ai chat / explain / debug / review / optimize / generate / docs / test."""

from __future__ import annotations

import sys
from pathlib import Path

from zoya_cli._meta import __version__
from zoya_cli.commands.base import Command, Context, Option, OptionAction
from zoya_cli.core.registry import register
from zoya_cli.core.errors import AIError


def _get_ai_provider(ctx: Context):
    from zoya_cli.ai import get_provider, list_providers

    provider_name = ctx.opts.get("--provider") or ctx.config.get("ai.provider", "mock")
    try:
        return get_provider(provider_name, config=ctx.config)
    except ValueError as exc:
        raise AIError(str(exc)) from exc


def _read_file(ctx: Context, path_str: str) -> str:
    p = Path(path_str)
    if not p.exists():
        raise AIError(f"File `{path_str}` not found.")
    return p.read_text(encoding="utf-8")


def _handle_ai_response(ctx: Context, response) -> None:
    ctx.console.rich.print(response.content)
    if ctx.opts.get("--json", False):
        import json

        ctx.console.print_json(
            {
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "usage": response.usage,
            }
        )


def _cmd_ai_chat(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    messages_raw = ctx.opts.get("--message") or (" ".join(ctx.args) if ctx.args else "")
    system = ctx.opts.get("--system", "You are a helpful programming assistant.")
    messages = [{"role": "system", "content": system}]
    if messages_raw:
        messages.append({"role": "user", "content": messages_raw})
    else:
        messages.append({"role": "user", "content": "Hello!"})
    # Interactive mode if no message provided
    if not ctx.args and not ctx.opts.get("--message"):
        ctx.console.info("Interactive AI chat. Type /exit to quit.")
        while True:
            try:
                line = ctx.args[0] if ctx.args else input("> ")
                ctx.args = ctx.args[1:] if ctx.args else []
            except (EOFError, KeyboardInterrupt):
                break
            if line.strip() == "/exit":
                break
            messages.append({"role": "user", "content": line})
            response = provider.chat(messages)
            ctx.console.rich.print(response.content)
            messages.append({"role": "assistant", "content": response.content})
        return 0
    response = provider.chat(messages)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_explain(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    code = _read_file(ctx, ctx.args[0]) if ctx.args else ""
    context = ctx.opts.get("--context", "")
    response = provider.explain_code(code, context=context)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_debug(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    error = ctx.opts.get("--error") or " ".join(ctx.args) if ctx.args else ""
    code = _read_file(ctx, ctx.opts.get("--file", "")) if ctx.opts.get("--file") else ""
    response = provider.debug_error(error, code=code)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_review(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    path = ctx.args[0] if ctx.args else "."
    target = Path(path)
    if target.is_dir():
        # Collect all .py files
        code_parts = []
        for pyfile in sorted(target.rglob("*.py")):
            if "__pycache__" not in pyfile.parts:
                code_parts.append(f"--- {pyfile} ---\n{pyfile.read_text(encoding='utf-8')}")
        code = "\n\n".join(code_parts)
    else:
        code = _read_file(ctx, path)
    response = provider.review_code(code)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_optimize(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    code = _read_file(ctx, ctx.args[0]) if ctx.args else ""
    response = provider.optimize_code(code)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_generate(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    spec = " ".join(ctx.args) if ctx.args else ctx.opts.get("--spec", "")
    if not spec:
        spec = "A Python function that greets a user by name."
    response = provider.generate_code(spec)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_docs(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    code = _read_file(ctx, ctx.args[0]) if ctx.args else ""
    response = provider.generate_docs(code)
    _handle_ai_response(ctx, response)
    return 0


def _cmd_ai_test(ctx: Context) -> int:
    provider = _get_ai_provider(ctx)
    code = _read_file(ctx, ctx.args[0]) if ctx.args else ""
    response = provider.generate_tests(code)
    _handle_ai_response(ctx, response)
    return 0


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------


def _ai_sub(name: str, help: str, run, examples: list[str] | None = None) -> Command:
    cmd = Command(
        name=name,
        help=help,
        run=run,
        examples=examples or [],
        options=[
            Option("--provider", help="AI provider to use (mock, openai)"),
            Option("--json", help="Output as JSON", action=OptionAction.STORE_TRUE),
            Option("--model", help="Model name override"),
        ],
    )
    return cmd


def register_ai_commands() -> None:
    ai_group = Command(
        "ai",
        help="AI-powered assistant commands",
        description="Chat with, explain, debug, review, optimize, generate, document, and test code using AI.",
        examples=["zoya ai chat", "zoya ai explain main.py", "zoya ai review ."],
    )

    ai_group.add_command(
        _ai_sub(
            "chat",
            "Chat with the AI assistant",
            _cmd_ai_chat,
            examples=["zoya ai chat", 'zoya ai chat --message "Explain generators"'],
        )
    )
    ai_group.add_command(
        _ai_sub("explain", "Explain code", _cmd_ai_explain, examples=["zoya ai explain main.py"])
    )
    ai_group.add_command(
        _ai_sub(
            "debug",
            "Debug an error",
            _cmd_ai_debug,
            examples=['zoya ai debug --error "KeyError: x"'],
        )
    )
    ai_group.add_command(
        _ai_sub(
            "review",
            "Review code for issues",
            _cmd_ai_review,
            examples=["zoya ai review", "zoya ai review main.py"],
        )
    )
    ai_group.add_command(
        _ai_sub(
            "optimize",
            "Suggest performance optimizations",
            _cmd_ai_optimize,
            examples=["zoya ai optimize main.py"],
        )
    )
    ai_group.add_command(
        _ai_sub(
            "generate",
            "Generate code from a specification",
            _cmd_ai_generate,
            examples=['zoya ai generate "function to sort a list"'],
        )
    )
    ai_group.add_command(
        _ai_sub(
            "docs",
            "Generate documentation for code",
            _cmd_ai_docs,
            examples=["zoya ai docs main.py"],
        )
    )
    ai_group.add_command(
        _ai_sub("test", "Generate tests for code", _cmd_ai_test, examples=["zoya ai test main.py"])
    )

    register(ai_group)
