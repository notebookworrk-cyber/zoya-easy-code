"""Tests for Zoya Studio templates."""

import tempfile
from pathlib import Path

from zoya_studio.core.templates import TemplateManager, Template


def test_template_registry():
    """Test templates are registered."""
    templates = TemplateManager.list_templates()
    names = {t.name for t in templates}
    assert "console-app" in names
    assert "2d-game" in names
    assert "3d-game" in names
    assert "ai-assistant" in names
    assert "desktop-app" in names
    assert "web-api" in names
    assert "library" in names
    assert "plugin" in names


def test_template_by_category():
    """Test category filtering."""
    games = TemplateManager.list_by_category("Game")
    assert len(games) >= 2


def test_template_create_project():
    """Test project creation from template."""
    with tempfile.TemporaryDirectory() as tmp:
        success = TemplateManager.create_project("console-app", tmp, "myapp")
        assert success
        project_dir = Path(tmp) / "myapp"
        assert project_dir.exists()
        assert (project_dir / "main.zoya").exists()
        assert (project_dir / "zoya.toml").exists()

        content = (project_dir / "main.zoya").read_text()
        assert "myapp" in content


def test_template_create_plugin():
    """Test plugin template creation."""
    with tempfile.TemporaryDirectory() as tmp:
        success = TemplateManager.create_project("plugin", tmp, "myplugin")
        assert success
        project_dir = Path(tmp) / "myplugin"
        assert (project_dir / "plugin.json").exists()
        assert (project_dir / "plugin.py").exists()

        content = (project_dir / "plugin.py").read_text()
        assert "myplugin" in content
