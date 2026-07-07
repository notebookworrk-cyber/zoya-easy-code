"""Zoya stdlib physics module."""

from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:

    class PhysicsBody:
        def __init__(self, x: float = 0, y: float = 0, z: float = 0) -> None:
            self.x = x
            self.y = y
            self.z = z
            self.vx = 0.0
            self.vy = 0.0
            self.vz = 0.0
            self.mass = 1.0
            self.bounce = 0.5
            self.friction = 0.98
            self.gravity_scale = 1.0
            self.fixed = False

        def apply_force(self, fx: float, fy: float, fz: float = 0) -> None:
            if self.fixed:
                return
            self.vx += fx / self.mass
            self.vy += fy / self.mass
            self.vz += fz / self.mass

        def update(self, dt: float = 1.0, gravity: float = 0) -> None:
            if self.fixed:
                return
            self.vy += gravity * self.gravity_scale * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z += self.vz * dt
            self.vx *= self.friction
            self.vy *= self.friction
            self.vz *= self.friction

        def get_pos(self) -> tuple[float, float, float]:
            return (self.x, self.y, self.z)

    def body(x: float = 0, y: float = 0, z: float = 0) -> PhysicsBody:
        return PhysicsBody(x, y, z)

    def distance(x1: float, y1: float, x2: float, y2: float) -> float:
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def distance_3d(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5

    def clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(value, max_val))

    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * max(0.0, min(1.0, t))

    def gravity_force(mass1: float, mass2: float, dist: float) -> float:
        G = 6.674e-11
        if dist <= 0:
            return 0
        return G * mass1 * mass2 / (dist * dist)

    funcs = {
        "body": body,
        "distance": distance,
        "distance_3d": distance_3d,
        "clamp": clamp,
        "lerp": lerp,
        "gravity_force": gravity_force,
    }

    from zoya.interpreter import ZoyaModule

    return ZoyaModule("physics", funcs)
