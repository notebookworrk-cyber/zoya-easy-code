"""Settings screen for Zoya Studio."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, Switch, TabbedContent, TabPane


class SettingsScreen(ModalScreen):
    """Settings configuration screen."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, app):
        super().__init__()
        self.studio_app = app
        self.config = app.config

    def compose(self):
        yield Vertical(
            Label("⚙ Settings", id="settings-title"),
            TabbedContent(id="settings-tabs"),
            Horizontal(
                Button("Save", id="settings-save", variant="primary"),
                Button("Cancel", id="settings-cancel"),
                id="settings-buttons",
            ),
            id="settings-container",
        )

    def on_mount(self):
        self._build_tabs()

    def _build_tabs(self):
        tabs = self.query_one("#settings-tabs", TabbedContent)

        with tabs:
            with TabPane("AI Provider", id="settings-ai"):
                yield Label("Provider", classes="settings-label")
                yield Select(
                    [(p, p) for p in self.studio_app.ai_manager.available_providers()],
                    value=self.config.ai.provider,
                    id="ai-provider",
                )
                yield Label("Model", classes="settings-label")
                yield Input(value=self.config.ai.model, id="ai-model")
                yield Label("Base URL (optional)", classes="settings-label")
                yield Input(value=self.config.ai.base_url, id="ai-base-url")
                yield Label("API Key (encrypted)", classes="settings-label")
                yield Input(value="", password=True, id="ai-api-key", placeholder="Enter API key")
                yield Label("Temperature", classes="settings-label")
                yield Input(value=str(self.config.ai.temperature), id="ai-temperature")
                yield Label("System Prompt", classes="settings-label")
                yield Input(value=self.config.ai.systems_prompt, id="ai-system-prompt")

            with TabPane("Theme", id="settings-theme"):
                from zoya_studio.core.config import THEME_PRESETS

                yield Label("Theme", classes="settings-label")
                yield Select(
                    [(name, name) for name in THEME_PRESETS.keys()],
                    value=self.config.theme.name,
                    id="theme-select",
                )

            with TabPane("Editor", id="settings-editor"):
                yield Label("Tab Size", classes="settings-label")
                yield Input(value=str(self.config.editor.tab_size), id="editor-tab-size")
                yield Label("Insert Spaces", classes="settings-label")
                yield Switch(value=self.config.editor.insert_spaces, id="editor-insert-spaces")
                yield Label("Auto Save", classes="settings-label")
                yield Switch(value=self.config.editor.auto_save, id="editor-auto-save")
                yield Label("Format on Save", classes="settings-label")
                yield Switch(value=self.config.editor.format_on_save, id="editor-format-on-save")
                yield Label("Line Numbers", classes="settings-label")
                yield Switch(value=self.config.ui.line_numbers, id="editor-line-numbers")

            with TabPane("Git", id="settings-git"):
                yield Label("User Name", classes="settings-label")
                yield Input(value=self.config.git.user_name, id="git-user-name")
                yield Label("User Email", classes="settings-label")
                yield Input(value=self.config.git.user_email, id="git-user-email")
                yield Label("Default Branch", classes="settings-label")
                yield Input(value=self.config.git.default_branch, id="git-default-branch")
                yield Label("Auto Fetch", classes="settings-label")
                yield Switch(value=self.config.git.auto_fetch, id="git-auto-fetch")

            with TabPane("Packages", id="settings-packages"):
                yield Label("Registry URL", classes="settings-label")
                yield Input(value=self.config.packages.registry, id="pkg-registry")
                yield Label("Auto Update", classes="settings-label")
                yield Switch(value=self.config.packages.auto_update, id="pkg-auto-update")

            with TabPane("Privacy", id="settings-privacy"):
                yield Label("Encrypt Credentials", classes="settings-label")
                yield Switch(value=True, id="privacy-encrypt", disabled=True)
                yield Label("Local AI Fallback", classes="settings-label")
                yield Switch(value=self.config.ai.use_local_fallback, id="privacy-local-fallback")
                yield Static("API keys are stored encrypted on disk.", classes="settings-note")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "settings-save":
            self.action_save()
        elif event.button.id == "settings-cancel":
            self.action_close()

    def action_save(self):
        """Save settings."""
        try:
            # AI settings
            ai_provider = self.query_one("#ai-provider", Select).value
            if ai_provider:
                self.config.ai.provider = ai_provider
                self.studio_app.ai_manager.set_provider(ai_provider)

            ai_model = self.query_one("#ai-model", Input).value
            if ai_model:
                self.config.ai.model = ai_model

            ai_base_url = self.query_one("#ai-base-url", Input).value
            self.config.ai.base_url = ai_base_url

            ai_api_key = self.query_one("#ai-api-key", Input).value
            if ai_api_key:
                from zoya_studio.security.crypto import CredentialStore

                store = CredentialStore(self.studio_app.crypto)
                store.store(f"ai_{self.config.ai.provider}_key", ai_api_key)
                encrypted = self.studio_app.crypto.encrypt(ai_api_key)
                self.config.ai.api_key = encrypted

            ai_temp = self.query_one("#ai-temperature", Input).value
            try:
                self.config.ai.temperature = float(ai_temp)
            except ValueError:
                pass

            ai_system = self.query_one("#ai-system-prompt", Input).value
            if ai_system:
                self.config.ai.systems_prompt = ai_system

            # Theme
            theme = self.query_one("#theme-select", Select).value
            if theme:
                from zoya_studio.core.config import THEME_PRESETS

                if theme in THEME_PRESETS:
                    self.config.theme = THEME_PRESETS[theme]
                    self.studio_app._apply_theme()

            # Editor
            tab_size = self.query_one("#editor-tab-size", Input).value
            try:
                self.config.editor.tab_size = int(tab_size)
            except ValueError:
                pass

            self.config.editor.insert_spaces = self.query_one("#editor-insert-spaces", Switch).value
            self.config.editor.auto_save = self.query_one("#editor-auto-save", Switch).value
            self.config.editor.format_on_save = self.query_one(
                "#editor-format-on-save", Switch
            ).value
            self.config.ui.line_numbers = self.query_one("#editor-line-numbers", Switch).value

            # Git
            self.config.git.user_name = self.query_one("#git-user-name", Input).value
            self.config.git.user_email = self.query_one("#git-user-email", Input).value
            self.config.git.default_branch = self.query_one("#git-default-branch", Input).value
            self.config.git.auto_fetch = self.query_one("#git-auto-fetch", Switch).value

            if self.config.git.user_name and self.config.git.user_email:
                self.studio_app.git_manager.configure_user(
                    self.config.git.user_name, self.config.git.user_email
                )

            # Packages
            self.config.packages.registry = self.query_one("#pkg-registry", Input).value
            self.config.packages.auto_update = self.query_one("#pkg-auto-update", Switch).value

            # Privacy
            self.config.ai.use_local_fallback = self.query_one(
                "#privacy-local-fallback", Switch
            ).value

            self.config.save()
            self.studio_app._update_ai_provider_status()
            self.studio_app._center_panel.write_log("[green]Settings saved[/]")
            self.dismiss(True)

        except Exception as e:
            self.studio_app._center_panel.write_log(f"[red]Settings save failed: {e}[/]")

    def action_close(self):
        self.dismiss(False)
