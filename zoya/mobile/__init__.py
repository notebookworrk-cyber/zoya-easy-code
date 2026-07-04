"""Zoya 4.0 Mobile Framework module.

Provides cross-platform mobile UI widgets, screen management, navigation,
and native bridge support.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class MobileError(Exception):
    """Base exception for mobile framework errors."""

    pass


class Widget:
    """Base class for all mobile widgets."""

    def __init__(
        self,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 50,
    ) -> None:
        self.id = widget_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.enabled = True
        self.on_click: Callable[[], None] | None = None
        self.on_long_press: Callable[[], None] | None = None
        self.on_swipe: Callable[[str], None] | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id='{self.id}')"


class Label(Widget):
    """Text display widget."""

    def __init__(
        self,
        text: str,
        font_size: int = 16,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.text = text
        self.font_size = font_size


class Button(Widget):
    """Action button widget."""

    def __init__(
        self,
        text: str,
        on_click: Callable[[], None] | None = None,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.text = text
        self.on_click = on_click

    def press(self) -> None:
        """Programmatically press the button."""
        if self.on_click and self.enabled:
            self.on_click()


class TextField(Widget):
    """Text input widget."""

    def __init__(
        self,
        placeholder: str = "",
        on_change: Callable[[str], None] | None = None,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.placeholder = placeholder
        self.text: str = ""
        self.on_change = on_change

    def set_text(self, text: str) -> None:
        """Set the text field value and trigger on_change."""
        self.text = text
        if self.on_change:
            self.on_change(text)


class Image(Widget):
    """Image display widget."""

    def __init__(
        self,
        source: str,
        width: int = 100,
        height: int = 100,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y, width=width, height=height)
        self.source = source


class ListView(Widget):
    """Scrollable list widget."""

    def __init__(
        self,
        items: list[Any],
        on_select: Callable[[Any], None] | None = None,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.items = items
        self.on_select = on_select

    def select(self, index: int) -> None:
        """Select an item by index."""
        if 0 <= index < len(self.items) and self.on_select:
            self.on_select(self.items[index])


class ScrollView(Widget):
    """Scrollable container widget."""

    def __init__(
        self,
        content: Widget,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.content = content


class Column(Widget):
    """Vertical layout widget."""

    def __init__(
        self,
        children: list[Widget],
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.children = children

    def add(self, widget: Widget) -> None:
        """Add a child widget."""
        self.children.append(widget)

    def remove(self, widget: Widget) -> None:
        """Remove a child widget."""
        self.children.remove(widget)


class Row(Widget):
    """Horizontal layout widget."""

    def __init__(
        self,
        children: list[Widget],
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.children = children

    def add(self, widget: Widget) -> None:
        """Add a child widget."""
        self.children.append(widget)

    def remove(self, widget: Widget) -> None:
        """Remove a child widget."""
        self.children.remove(widget)


class Card(Widget):
    """Styled card widget."""

    def __init__(
        self,
        title: str,
        content: Widget,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.title = title
        self.content = content


class Switch(Widget):
    """Toggle switch widget."""

    def __init__(
        self,
        value: bool = False,
        on_toggle: Callable[[bool], None] | None = None,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.value = value
        self.on_toggle = on_toggle

    def toggle(self) -> None:
        """Flip the switch value."""
        self.value = not self.value
        if self.on_toggle:
            self.on_toggle(self.value)


class Slider(Widget):
    """Slider widget for range selection."""

    def __init__(
        self,
        min_value: float = 0,
        max_value: float = 100,
        value: float = 50,
        on_change: Callable[[float], None] | None = None,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.min = min_value
        self.max = max_value
        self.value = value
        self.on_change = on_change

    def set_value(self, value: float) -> None:
        """Set slider value clamped to range."""
        self.value = max(self.min, min(self.max, value))
        if self.on_change:
            self.on_change(self.value)


class ProgressBar(Widget):
    """Progress indicator widget."""

    def __init__(
        self,
        value: float = 0,
        max_value: float = 100,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.value = value
        self.max = max_value

    @property
    def percentage(self) -> float:
        """Progress as a percentage (0-100)."""
        return (self.value / self.max * 100) if self.max > 0 else 0


class Spinner(Widget):
    """Loading spinner widget."""

    def __init__(
        self,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)


class Toast(Widget):
    """Notification toast widget. Auto-dismisses after duration."""

    def __init__(
        self,
        message: str,
        duration: float = 2.0,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.message = message
        self.duration = duration


class Modal(Widget):
    """Modal overlay widget."""

    def __init__(
        self,
        content: Widget,
        widget_id: str = "",
        x: float = 0,
        y: float = 0,
    ) -> None:
        super().__init__(widget_id=widget_id, x=x, y=y)
        self.content = content
        self.is_open = False

    def open(self) -> None:
        """Show the modal."""
        self.is_open = True
        self.visible = True

    def close(self) -> None:
        """Hide the modal."""
        self.is_open = False
        self.visible = False


class Screen:
    """A screen/page in the mobile application."""

    def __init__(self, name: str, title: str = "") -> None:
        self.name = name
        self.title = title or name
        self.widgets: list[Widget] = []

    def add_widget(self, widget: Widget) -> None:
        """Add a widget to the screen."""
        self.widgets.append(widget)

    def remove_widget(self, widget: Widget) -> None:
        """Remove a widget from the screen."""
        if widget in self.widgets:
            self.widgets.remove(widget)

    def on_load(self) -> None:
        """Lifecycle: screen is being loaded."""
        pass

    def on_unload(self) -> None:
        """Lifecycle: screen is being destroyed."""
        pass

    def on_appear(self) -> None:
        """Visibility: screen became visible."""
        pass

    def on_disappear(self) -> None:
        """Visibility: screen is no longer visible."""
        pass

    def build(self) -> list[Widget]:
        """Build and return the screen's widget tree."""
        return self.widgets


class Navigator:
    """Manages screen navigation stack."""

    def __init__(self) -> None:
        self._stack: list[Screen] = []

    def push(self, screen: Screen, animated: bool = True) -> None:
        """Push a screen onto the navigation stack."""
        if self._stack:
            self._stack[-1].on_disappear()
        screen.on_load()
        screen.on_appear()
        self._stack.append(screen)

    def pop(self, animated: bool = True) -> None:
        """Pop the current screen from the stack."""
        if not self._stack:
            return
        current = self._stack.pop()
        current.on_disappear()
        current.on_unload()
        if self._stack:
            self._stack[-1].on_appear()

    def replace(self, screen: Screen) -> None:
        """Replace the current screen without changing stack depth."""
        if self._stack:
            old = self._stack.pop()
            old.on_disappear()
            old.on_unload()
        screen.on_load()
        screen.on_appear()
        self._stack.append(screen)

    def pop_to_root(self) -> None:
        """Pop all screens back to the first one."""
        while len(self._stack) > 1:
            popped = self._stack.pop()
            popped.on_disappear()
            popped.on_unload()
        if self._stack:
            self._stack[-1].on_appear()

    def get_current(self) -> Screen | None:
        """Get the topmost screen."""
        if not self._stack:
            return None
        return self._stack[-1]

    def get_history(self) -> list[str]:
        """Return the list of screen names in the stack."""
        return [s.name for s in self._stack]

    def can_go_back(self) -> bool:
        """Check if there is a screen to pop to."""
        return len(self._stack) > 1


class App:
    """Main mobile application."""

    def __init__(self, name: str = "ZoyaApp", version: str = "1.0.0") -> None:
        self.name = name
        self.version = version
        self.screens: dict[str, Screen] = {}
        self.initial_route: str = ""
        self.navigator = Navigator()
        self.theme: dict[str, Any] = {
            "primary_color": "#007AFF",
            "background_color": "#FFFFFF",
            "text_color": "#000000",
            "font_family": "system",
            "spacing": 8,
            "border_radius": 8,
        }

    def add_screen(self, name: str, screen: Screen) -> None:
        """Register a screen with the app."""
        self.screens[name] = screen

    def set_initial_route(self, name: str) -> None:
        """Set the first screen to display on launch."""
        self.initial_route = name

    def get_screen(self, name: str) -> Screen | None:
        """Retrieve a registered screen by name."""
        return self.screens.get(name)

    def run(self) -> None:
        """Start the mobile application."""
        if not self.initial_route and self.screens:
            self.initial_route = next(iter(self.screens))
        screen = self.screens.get(self.initial_route)
        if screen:
            self.navigator.push(screen)
            print(f"Zoya Mobile App '{self.name}' v{self.version} running")
            print(f"Initial screen: {screen.name}")
        else:
            raise MobileError(f"Initial route '{self.initial_route}' not found")


class NativeBridge(ABC):
    """Abstract interface for native platform calls."""

    @abstractmethod
    def request_permission(self, permission: str) -> bool: ...

    @abstractmethod
    def get_device_info(self) -> dict[str, Any]: ...

    @abstractmethod
    def show_notification(self, title: str, body: str) -> None: ...

    @abstractmethod
    def vibrate(self, duration: int = 100) -> None: ...

    @abstractmethod
    def get_location(self) -> dict[str, Any]: ...

    @abstractmethod
    def take_photo(self) -> str: ...

    @abstractmethod
    def pick_file(self) -> str: ...

    @abstractmethod
    def open_url(self, url: str) -> None: ...

    @abstractmethod
    def share_text(self, text: str) -> None: ...


class IOSBridge(NativeBridge):
    """iOS native bridge implementation."""

    def request_permission(self, permission: str) -> bool:
        print(f"[iOS] Requesting permission: {permission}")
        return True

    def get_device_info(self) -> dict[str, Any]:
        return {"platform": "iOS", "model": "iPhone", "os_version": "17.0"}

    def show_notification(self, title: str, body: str) -> None:
        print(f"[iOS] Notification: {title} - {body}")

    def vibrate(self, duration: int = 100) -> None:
        print(f"[iOS] Vibrate for {duration}ms")

    def get_location(self) -> dict[str, Any]:
        return {"lat": 37.7749, "lng": -122.4194}

    def take_photo(self) -> str:
        path = "/tmp/ios_photo.jpg"
        print(f"[iOS] Photo saved to {path}")
        return path

    def pick_file(self) -> str:
        path = "/tmp/ios_picked_file.pdf"
        print(f"[iOS] File picked: {path}")
        return path

    def open_url(self, url: str) -> None:
        print(f"[iOS] Opening URL: {url}")

    def share_text(self, text: str) -> None:
        print(f"[iOS] Sharing text: {text}")


class AndroidBridge(NativeBridge):
    """Android native bridge implementation."""

    def request_permission(self, permission: str) -> bool:
        print(f"[Android] Requesting permission: {permission}")
        return True

    def get_device_info(self) -> dict[str, Any]:
        return {"platform": "Android", "model": "Pixel 8", "os_version": "14.0"}

    def show_notification(self, title: str, body: str) -> None:
        print(f"[Android] Notification: {title} - {body}")

    def vibrate(self, duration: int = 100) -> None:
        print(f"[Android] Vibrate for {duration}ms")

    def get_location(self) -> dict[str, Any]:
        return {"lat": 37.7749, "lng": -122.4194}

    def take_photo(self) -> str:
        path = "/storage/emulated/0/DCIM/photo.jpg"
        print(f"[Android] Photo saved to {path}")
        return path

    def pick_file(self) -> str:
        path = "/storage/emulated/0/Download/picked_file.pdf"
        print(f"[Android] File picked: {path}")
        return path

    def open_url(self, url: str) -> None:
        print(f"[Android] Opening URL: {url}")

    def share_text(self, text: str) -> None:
        print(f"[Android] Sharing text: {text}")


def create_mobile_app(name: str = "ZoyaApp") -> App:
    """Create a new mobile application instance."""
    return App(name=name)
