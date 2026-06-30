from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    _pygame = None
    _screen = None
    _clock = None
    _sprites: list[dict[str, Any]] = []
    _running = False
    _keys: dict[int, bool] = {}
    _mouse_x = 0
    _mouse_y = 0
    _mouse_buttons = (False, False, False)

    def _to_color(c: Any) -> tuple[int, int, int]:
        if isinstance(c, (list, tuple)):
            return (int(c[0]), int(c[1]), int(c[2]))
        return (255, 255, 255)

    def _init() -> None:
        nonlocal _pygame
        if _pygame is None:
            try:
                import pygame as _pygame
                _pygame.init()
                _pygame.font.init()
            except ImportError:
                raise ImportError("pygame-ce is required. Install: pip install pygame-ce")

    def window(title: str, width: int, height: int) -> None:
        nonlocal _screen, _clock, _running
        _init()
        _screen = _pygame.display.set_mode((width, height))
        _pygame.display.set_caption(title)
        _clock = _pygame.time.Clock()
        _running = True

    def fill(r: int, g: int, b: int) -> None:
        if _screen:
            _screen.fill((r, g, b))

    def sprite(image_path: str, x: float = 0, y: float = 0) -> dict[str, Any]:
        _init()
        sprite_data = {
            "image": _pygame.image.load(image_path) if _pygame else None,
            "x": x,
            "y": y,
            "width": 0,
            "height": 0,
            "rotation": 0,
            "visible": True,
        }
        if sprite_data["image"]:
            sprite_data["width"] = sprite_data["image"].get_width()
            sprite_data["height"] = sprite_data["image"].get_height()
        _sprites.append(sprite_data)
        return sprite_data

    def rect(x: float, y: float, w: float, h: float, color: Any = (255, 255, 255)) -> dict[str, Any]:
        c = _to_color(color)
        sprite_data = {
            "type": "rect",
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "color": c,
            "rotation": 0,
            "visible": True,
        }
        _sprites.append(sprite_data)
        return sprite_data

    def circle(x: float, y: float, radius: float, color: Any = (255, 255, 255)) -> dict[str, Any]:
        c = _to_color(color)
        sprite_data = {
            "type": "circle",
            "x": x,
            "y": y,
            "radius": radius,
            "color": c,
            "visible": True,
        }
        _sprites.append(sprite_data)
        return sprite_data

    def text(content: str, x: float, y: float, size: int = 24, color: Any = (255, 255, 255)) -> dict[str, Any]:
        _init()
        c = _to_color(color)
        font = _pygame.font.Font(None, size) if _pygame else None
        text_surf = font.render(content, True, c) if font else None
        sprite_data = {
            "type": "text",
            "surface": text_surf,
            "x": x,
            "y": y,
            "content": content,
            "size": size,
            "color": c,
            "visible": True,
        }
        _sprites.append(sprite_data)
        return sprite_data

    def draw(sprite_obj: dict[str, Any]) -> None:
        if not _screen or not sprite_obj.get("visible", True):
            return
        if sprite_obj.get("type") == "rect":
            _pygame.draw.rect(
                _screen,
                sprite_obj["color"],
                (sprite_obj["x"], sprite_obj["y"], sprite_obj["width"], sprite_obj["height"]),
            )
        elif sprite_obj.get("type") == "circle":
            _pygame.draw.circle(
                _screen,
                sprite_obj["color"],
                (int(sprite_obj["x"]), int(sprite_obj["y"])),
                sprite_obj["radius"],
            )
        elif sprite_obj.get("type") == "text" and sprite_obj.get("surface"):
            _screen.blit(sprite_obj["surface"], (sprite_obj["x"], sprite_obj["y"]))
        elif sprite_obj.get("image"):
            img = sprite_obj["image"]
            if sprite_obj["rotation"]:
                img = _pygame.transform.rotate(img, sprite_obj["rotation"])
            _screen.blit(img, (sprite_obj["x"], sprite_obj["y"]))

    def move(sprite_obj: dict[str, Any], dx: float, dy: float) -> None:
        sprite_obj["x"] += dx
        sprite_obj["y"] += dy

    def rotate(sprite_obj: dict[str, Any], angle: float) -> None:
        sprite_obj["rotation"] = (sprite_obj.get("rotation", 0) + angle) % 360

    def collision(a: dict[str, Any], b: dict[str, Any]) -> bool:
        if a.get("type") == "circle" and b.get("type") == "circle":
            dx = a["x"] - b["x"]
            dy = a["y"] - b["y"]
            dist = (dx * dx + dy * dy) ** 0.5
            return dist < (a.get("radius", 0) + b.get("radius", 0))
        ax, ay = a.get("x", 0), a.get("y", 0)
        bx, by = b.get("x", 0), b.get("y", 0)
        aw, ah = a.get("width", 1), a.get("height", 1)
        bw, bh = b.get("width", 1), b.get("height", 1)
        return (ax < bx + bw) and (ax + aw > bx) and (ay < by + bh) and (ay + ah > by)

    def update(fps: int = 60) -> bool:
        nonlocal _running, _keys, _mouse_x, _mouse_y, _mouse_buttons
        if not _pygame or not _screen:
            return False
        _keys = {}
        for event in _pygame.event.get():
            if event.type == _pygame.QUIT:
                _running = False
                return False
            if event.type == _pygame.KEYDOWN:
                _keys[event.key] = True
            if event.type == _pygame.MOUSEMOTION:
                _mouse_x, _mouse_y = event.pos
            if event.type == _pygame.MOUSEBUTTONDOWN:
                _mouse_buttons = (True, False, False)
            if event.type == _pygame.MOUSEBUTTONUP:
                _mouse_buttons = (False, False, False)
        if _clock:
            _clock.tick(fps)
        return True

    def key_down(key: str) -> bool:
        if not _pygame:
            return False
        key_map = {
            "up": _pygame.K_UP, "down": _pygame.K_DOWN,
            "left": _pygame.K_LEFT, "right": _pygame.K_RIGHT,
            "space": _pygame.K_SPACE, "enter": _pygame.K_RETURN,
            "escape": _pygame.K_ESCAPE, "a": _pygame.K_a,
            "b": _pygame.K_b, "c": _pygame.K_c, "d": _pygame.K_d,
            "e": _pygame.K_e, "f": _pygame.K_f, "g": _pygame.K_g,
            "h": _pygame.K_h, "i": _pygame.K_i, "j": _pygame.K_j,
            "k": _pygame.K_k, "l": _pygame.K_l, "m": _pygame.K_m,
            "n": _pygame.K_n, "o": _pygame.K_o, "p": _pygame.K_p,
            "q": _pygame.K_q, "r": _pygame.K_r, "s": _pygame.K_s,
            "t": _pygame.K_t, "u": _pygame.K_u, "v": _pygame.K_v,
            "w": _pygame.K_w, "x": _pygame.K_x, "y": _pygame.K_y,
            "z": _pygame.K_z,
        }
        kc = key_map.get(key.lower())
        return _keys.get(kc, False) if kc else False

    def mouse_x() -> int:
        return _mouse_x

    def mouse_y() -> int:
        return _mouse_y

    def mouse_clicked() -> bool:
        return _mouse_buttons[0]

    def quit_game() -> None:
        nonlocal _running
        _running = False
        if _pygame:
            _pygame.quit()

    def set_fps(fps: int) -> None:
        nonlocal _clock
        if _clock:
            _clock.tick(fps)

    funcs = {
        "window": window,
        "fill": fill,
        "sprite": sprite,
        "rect": rect,
        "circle": circle,
        "text": text,
        "draw": draw,
        "move": move,
        "rotate": rotate,
        "collision": collision,
        "update": update,
        "key_down": key_down,
        "mouse_x": mouse_x,
        "mouse_y": mouse_y,
        "mouse_clicked": mouse_clicked,
        "quit": quit_game,
        "set_fps": set_fps,
        "width": lambda: _screen.get_width() if _screen else 0,
        "height": lambda: _screen.get_height() if _screen else 0,
    }

    return ZoyaModule("game", funcs)
