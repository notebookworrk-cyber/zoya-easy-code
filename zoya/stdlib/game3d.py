from __future__ import annotations

import contextlib
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    _app = None
    _entities: list[Any] = []
    _running = False

    def scene(title: str = "Zoya 3D") -> None:
        nonlocal _app
        try:
            from ursina import Ursina

            _app = Ursina()
        except ImportError:
            try:
                from direct.showbase.ShowBase import ShowBase

                class Zoya3DApp(ShowBase):
                    def __init__(self):
                        super().__init__()

                _app = Zoya3DApp()
            except ImportError:
                raise ImportError(
                    "Ursina or Panda3D required. Install: pip install ursina"
                ) from None

    def cube(x: float = 0, y: float = 0, z: float = 0, color: str = "white") -> Any:
        nonlocal _entities
        try:
            from ursina import Entity
            from ursina import color as ucolor

            c = getattr(ucolor, color, ucolor.white)
            ent = Entity(model="cube", position=(x, y, z), color=c)
            _entities.append(ent)
            return ent
        except ImportError:
            _dummy = {"type": "cube", "x": x, "y": y, "z": z, "color": color}
            _entities.append(_dummy)
            return _dummy

    def sphere(x: float = 0, y: float = 0, z: float = 0, color: str = "white") -> Any:
        nonlocal _entities
        try:
            from ursina import Entity
            from ursina import color as ucolor

            c = getattr(ucolor, color, ucolor.white)
            ent = Entity(model="sphere", position=(x, y, z), color=c)
            _entities.append(ent)
            return ent
        except ImportError:
            _dummy = {"type": "sphere", "x": x, "y": y, "z": z, "color": color}
            _entities.append(_dummy)
            return _dummy

    def light(type_: str = "ambient", intensity: float = 1.0) -> Any:
        try:
            from ursina import Entity

            ent = Entity(model="cube", scale=0, light=type_)
            return ent
        except ImportError:
            return {"type": "light", "light_type": type_, "intensity": intensity}

    def camera(x: float = 0, y: float = 0, z: float = -10) -> None:
        try:
            from ursina import camera as ucam

            ucam.position = (x, y, z)
        except ImportError:
            pass

    def rotate(entity: Any, x: float = 0, y: float = 0, z: float = 0) -> None:
        with contextlib.suppress(AttributeError, TypeError):
            entity.rotation += (x, y, z)

    def move(entity: Any, x: float = 0, y: float = 0, z: float = 0) -> None:
        try:
            entity.position += (x, y, z)
        except (AttributeError, TypeError):
            if isinstance(entity, dict):
                entity["x"] = entity.get("x", 0) + x
                entity["y"] = entity.get("y", 0) + y
                entity["z"] = entity.get("z", 0) + z

    def render() -> None:
        nonlocal _running
        _running = True
        try:
            from ursina import application

            application.run()
        except ImportError:
            pass

    def quit_3d() -> None:
        try:
            from ursina import application

            application.quit()
        except ImportError:
            pass
        nonlocal _running
        _running = False

    funcs = {
        "scene": scene,
        "cube": cube,
        "sphere": sphere,
        "light": light,
        "camera": camera,
        "rotate": rotate,
        "move": move,
        "render": render,
        "quit": quit_3d,
    }

    return ZoyaModule("game3d", funcs)
