"""Zoya 4.0 Gesture Recognition module.

Provides touch event handling and gesture detection for mobile interactions.
"""

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TouchEvent:
    """Represents a single touch event."""

    x: float
    y: float
    timestamp: float
    pointer_id: int = 0
    event_type: str = "down"


class GestureRecognizer(ABC):
    """Abstract base for all gesture recognizers."""

    @abstractmethod
    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        """Detect gesture type from a batch of touch events.

        Returns the gesture name (e.g. 'tap', 'swipe_left') or None.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Clear internal state between gesture attempts."""
        ...


class TapRecognizer(GestureRecognizer):
    """Detects a single tap: finger down then up within distance and time."""

    def __init__(self, max_distance: float = 10, max_duration: float = 0.3) -> None:
        self.max_distance = max_distance
        self.max_duration = max_duration
        self._start_x: Optional[float] = None
        self._start_y: Optional[float] = None
        self._start_time: Optional[float] = None
        self._touching = False

    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        for touch in touches:
            if touch.event_type == "down" and not self._touching:
                self._start_x = touch.x
                self._start_y = touch.y
                self._start_time = touch.timestamp
                self._touching = True

            elif touch.event_type == "up" and self._touching:
                if (
                    self._start_x is None
                    or self._start_y is None
                    or self._start_time is None
                ):
                    continue
                dx = abs(touch.x - self._start_x)
                dy = abs(touch.y - self._start_y)
                duration = touch.timestamp - self._start_time
                self.reset()
                if (
                    dx <= self.max_distance
                    and dy <= self.max_distance
                    and 0 < duration <= self.max_duration
                ):
                    return "tap"

            elif touch.event_type == "cancel":
                self.reset()

        return None

    def reset(self) -> None:
        self._start_x = None
        self._start_y = None
        self._start_time = None
        self._touching = False


class DoubleTapRecognizer(GestureRecognizer):
    """Detects two quick taps in succession."""

    def __init__(self, max_interval: float = 0.3) -> None:
        self.max_interval = max_interval
        self._last_tap_time: Optional[float] = None
        self._sub = TapRecognizer()

    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        result = self._sub.recognize(touches)

        if result == "tap":
            now = time.time()
            if (
                self._last_tap_time is not None
                and (now - self._last_tap_time) <= self.max_interval
            ):
                self.reset()
                return "double_tap"
            self._last_tap_time = now

        return None

    def reset(self) -> None:
        self._last_tap_time = None
        self._sub.reset()


class LongPressRecognizer(GestureRecognizer):
    """Detects a finger held down for a minimum duration."""

    def __init__(self, min_duration: float = 0.5) -> None:
        self.min_duration = min_duration
        self._start_x: Optional[float] = None
        self._start_y: Optional[float] = None
        self._start_time: Optional[float] = None
        self._touching = False
        self._triggered = False

    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        for touch in touches:
            if touch.event_type == "down" and not self._touching:
                self._start_x = touch.x
                self._start_y = touch.y
                self._start_time = touch.timestamp
                self._touching = True
                self._triggered = False

            elif touch.event_type == "move" and self._touching and not self._triggered:
                if self._start_time is not None:
                    elapsed = touch.timestamp - self._start_time
                    if elapsed >= self.min_duration:
                        self._triggered = True
                        return "long_press"

            elif touch.event_type in ("up", "cancel"):
                self.reset()

        return None

    def reset(self) -> None:
        self._start_x = None
        self._start_y = None
        self._start_time = None
        self._touching = False
        self._triggered = False


class SwipeRecognizer(GestureRecognizer):
    """Detects a swipe gesture in a specified direction.

    Direction can be 'left', 'right', 'up', 'down', or 'any'.
    """

    def __init__(self, min_distance: float = 50, direction: str = "any") -> None:
        self.min_distance = min_distance
        self.direction = direction
        self._start_x: Optional[float] = None
        self._start_y: Optional[float] = None
        self._touching = False

    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        for touch in touches:
            if touch.event_type == "down" and not self._touching:
                self._start_x = touch.x
                self._start_y = touch.y
                self._touching = True

            elif touch.event_type == "up" and self._touching:
                if self._start_x is None or self._start_y is None:
                    continue
                dx = touch.x - self._start_x
                dy = touch.y - self._start_y
                distance = math.sqrt(dx * dx + dy * dy)
                self.reset()

                if distance < self.min_distance:
                    return None

                angle = math.degrees(math.atan2(dy, dx))
                detected = self._direction_name(angle)

                if self.direction == "any" or detected == self.direction:
                    return f"swipe_{detected}"

            elif touch.event_type == "cancel":
                self.reset()

        return None

    @staticmethod
    def _direction_name(angle: float) -> str:
        if -45 <= angle < 45:
            return "right"
        elif 45 <= angle < 135:
            return "down"
        elif -135 <= angle < -45:
            return "up"
        else:
            return "left"

    def reset(self) -> None:
        self._start_x = None
        self._start_y = None
        self._touching = False


class PinchRecognizer(GestureRecognizer):
    """Detects a two-finger pinch-to-zoom gesture."""

    def __init__(self, min_scale: float = 0.5) -> None:
        self.min_scale = min_scale
        self._initial_distance: Optional[float] = None
        self._active = False

    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        pointers: Dict[int, Tuple[float, float]] = {}

        for t in touches:
            pointers[t.pointer_id] = (t.x, t.y)
            if t.event_type == "down":
                self._active = False
                self._initial_distance = None
            elif t.event_type in ("up", "cancel"):
                self.reset()
                return None

        if len(pointers) < 2:
            return None

        keys = list(pointers.keys())[:2]
        p1 = pointers[keys[0]]
        p2 = pointers[keys[1]]
        current_distance = math.sqrt(
            (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
        )

        if current_distance < 1:
            return None

        if self._initial_distance is None:
            self._initial_distance = current_distance
            self._active = True
            return None

        scale = current_distance / self._initial_distance
        delta = abs(scale - 1.0)

        if delta >= self.min_scale:
            direction = "in" if scale < 1.0 else "out"
            return f"pinch_{direction}"

        return None

    def reset(self) -> None:
        self._initial_distance = None
        self._active = False


class PanRecognizer(GestureRecognizer):
    """Detects a drag/pan gesture with continuous tracking."""

    def __init__(self, min_distance: float = 10) -> None:
        self.min_distance = min_distance
        self._start_x: Optional[float] = None
        self._start_y: Optional[float] = None
        self._last_x: Optional[float] = None
        self._last_y: Optional[float] = None
        self._touching = False

    def recognize(self, touches: List[TouchEvent]) -> Optional[str]:
        for touch in touches:
            if touch.event_type == "down" and not self._touching:
                self._start_x = touch.x
                self._start_y = touch.y
                self._last_x = touch.x
                self._last_y = touch.y
                self._touching = True

            elif touch.event_type == "move" and self._touching:
                if self._start_x is None or self._start_y is None:
                    continue
                dx = touch.x - self._start_x
                dy = touch.y - self._start_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance >= self.min_distance:
                    if self._last_x is not None and self._last_y is not None:
                        self._last_x = touch.x
                        self._last_y = touch.y
                        return "pan"

            elif touch.event_type in ("up", "cancel"):
                self.reset()

        return None

    def reset(self) -> None:
        self._start_x = None
        self._start_y = None
        self._last_x = None
        self._last_y = None
        self._touching = False


class GestureDetector:
    """Orchestrates multiple gesture recognizers on touch input."""

    def __init__(self) -> None:
        self.recognizers: List[GestureRecognizer] = []

    def add_recognizer(self, recognizer: GestureRecognizer) -> None:
        """Register a recognizer for gesture detection."""
        self.recognizers.append(recognizer)

    def process_touches(
        self, touches: List[TouchEvent]
    ) -> Optional[Tuple[str, Dict]]:
        """Feed touch events to all recognizers.

        Returns the first matching (gesture_name, params) or None.
        """
        for recognizer in self.recognizers:
            gesture = recognizer.recognize(touches)
            if gesture is not None:
                params = self._extract_params(touches)
                return (gesture, params)
        return None

    @staticmethod
    def _extract_params(touches: List[TouchEvent]) -> Dict:
        if not touches:
            return {}
        t = touches[-1]
        return {"x": t.x, "y": t.y, "timestamp": t.timestamp}

    def reset(self) -> None:
        """Reset all recognizers to their initial state."""
        for recognizer in self.recognizers:
            recognizer.reset()
