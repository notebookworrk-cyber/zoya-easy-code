"""Dialog widgets for Zoya Studio."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListView, Static


class InputDialog(ModalScreen):
    """Simple input dialog."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Confirm"),
    ]

    def __init__(self, title: str, prompt: str, placeholder: str = ""):
        super().__init__()
        self.dialog_title = title
        self.dialog_prompt = prompt
        self.dialog_placeholder = placeholder

    def compose(self):
        yield Vertical(
            Label(self.dialog_title, id="dialog-title"),
            Label(self.dialog_prompt, id="dialog-prompt"),
            Input(placeholder=self.dialog_placeholder, id="dialog-input"),
            Button("OK", id="dialog-ok", variant="primary"),
            id="dialog-container",
        )

    def on_mount(self):
        self.query_one("#dialog-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "dialog-input":
            self.action_confirm()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "dialog-ok":
            self.action_confirm()

    def action_confirm(self):
        value = self.query_one("#dialog-input", Input).value
        self.dismiss(value)

    def action_cancel(self):
        self.dismiss(None)


class PathDialog(InputDialog):
    """Path input dialog with browse support."""

    def __init__(self, title: str, prompt: str, placeholder: str = ""):
        super().__init__(title, prompt, placeholder)

    def compose(self):
        yield Vertical(
            Label(self.dialog_title, id="dialog-title"),
            Label(self.dialog_prompt, id="dialog-prompt"),
            Input(placeholder=self.dialog_placeholder or ".", id="dialog-input"),
            Button("Browse", id="dialog-browse"),
            Button("OK", id="dialog-ok", variant="primary"),
            id="dialog-container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "dialog-browse":
            self._browse()
        else:
            super().on_button_pressed(event)

    def _browse(self):
        from tkinter import filedialog, Tk

        root = Tk()
        root.withdraw()
        path = filedialog.askdirectory()
        root.destroy()
        if path:
            self.query_one("#dialog-input", Input).value = path


class ConfirmDialog(ModalScreen):
    """Confirmation dialog."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
    ]

    def __init__(self, title: str, message: str, danger: bool = False):
        super().__init__()
        self.dialog_title = title
        self.dialog_message = message
        self.dialog_danger = danger

    def compose(self):
        yield Vertical(
            Label(self.dialog_title, id="dialog-title"),
            Static(self.dialog_message, id="dialog-message"),
            Button("Yes", id="dialog-yes", variant="error" if self.dialog_danger else "primary"),
            Button("No", id="dialog-no"),
            id="dialog-container",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "dialog-yes":
            self.action_confirm()
        else:
            self.action_cancel()

    def action_confirm(self):
        self.dismiss(True)

    def action_cancel(self):
        self.dismiss(False)


class SelectDialog(ModalScreen):
    """Selection dialog with options."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title: str, options: list[str], message: str = ""):
        super().__init__()
        self.dialog_title = title
        self.dialog_options = options
        self.dialog_message = message

    def compose(self):
        from textual.widgets import ListView

        yield Vertical(
            Label(self.dialog_title, id="dialog-title"),
            Static(self.dialog_message, id="dialog-message") if self.dialog_message else Static(""),
            ListView(id="dialog-list"),
            id="dialog-container",
        )

    def on_mount(self):
        from textual.widgets import ListItem, Static

        list_view = self.query_one("#dialog-list", ListView)
        for opt in self.dialog_options:
            list_view.append(ListItem(Static(opt), id=f"opt-{opt}"))

    def on_list_view_selected(self, event):
        if event.item.id and event.item.id.startswith("opt-"):
            self.dismiss(event.item.id[4:])

    def action_cancel(self):
        self.dismiss(None)
