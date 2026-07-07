"""Zoya stdlib audio module."""

from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    _initialized = False
    _player = None

    def _ensure_init() -> None:
        nonlocal _initialized, _player
        if not _initialized:
            try:
                import pygame as _pygame

                _pygame.mixer.init()
                _initialized = True
            except ImportError:
                pass

    def play(path: str, loop: bool = False) -> None:
        _ensure_init()
        nonlocal _player
        try:
            import pygame as _pygame

            _pygame.mixer.music.load(path)
            _pygame.mixer.music.play(-1 if loop else 0)
        except Exception as e:
            print(f"Audio error: {e}")

    def pause() -> None:
        try:
            import pygame as _pygame

            _pygame.mixer.music.pause()
        except ImportError:
            pass

    def stop() -> None:
        try:
            import pygame as _pygame

            _pygame.mixer.music.stop()
        except ImportError:
            pass

    def resume() -> None:
        try:
            import pygame as _pygame

            _pygame.mixer.music.unpause()
        except ImportError:
            pass

    def set_volume(vol: float) -> None:
        try:
            import pygame as _pygame

            _pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
        except ImportError:
            pass

    funcs = {"play": play, "pause": pause, "stop": stop, "resume": resume, "set_volume": set_volume}

    return ZoyaModule("audio", funcs)
