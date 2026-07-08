"""Templates for Zoya Studio."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Template:
    """Project template."""
    name: str
    category: str
    description: str
    files: dict[str, str] = field(default_factory=dict)
    post_create: list[str] = field(default_factory=list)


class TemplateManager:
    """Manages project templates."""

    TEMPLATES: dict[str, Template] = {}

    @classmethod
    def register(cls, template: Template) -> None:
        """Register a template."""
        cls.TEMPLATES[template.name] = template

    @classmethod
    def get_template(cls, name: str) -> Template | None:
        """Get template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_templates(cls) -> list[Template]:
        """List all templates."""
        return list(cls.TEMPLATES.values())

    @classmethod
    def list_by_category(cls, category: str) -> list[Template]:
        """List templates by category."""
        return [t for t in cls.TEMPLATES.values() if t.category == category]

    @classmethod
    def create_project(cls, template_name: str, project_path: str,
                       project_name: str) -> bool:
        """Create a project from template."""
        template = cls.TEMPLATES.get(template_name)
        if not template:
            return False

        path = Path(project_path) / project_name
        path.mkdir(parents=True, exist_ok=True)

        for file_path, content in template.files.items():
            content = content.replace("{{PROJECT_NAME}}", project_name)
            full_path = path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

        (path / "zoya.toml").write_text(
            f'[project]\nname = "{project_name}"\n'
            f'version = "0.1.0"\n'
            f'description = "{template.description}"\n'
            f'language = "zoya"\n'
            f'template = "{template_name}"\n'
        )

        return True


# Console App Template
TemplateManager.register(Template(
    name="console-app",
    category="Application",
    description="Console application template",
    files={
        "main.zoya": '''# {{PROJECT_NAME}} — Console Application
print "Welcome to {{PROJECT_NAME}}!"

fn main():
    print "Hello from the console!"
    name = input "What is your name? "
    print "Nice to meet you, " + name + "!"

main()
''',
        "README.md": '# {{PROJECT_NAME}}\n\nConsole application built with Zoya.\n',
        ".gitignore": '__pycache__/\n*.pyc\n.zoya/\n',
    },
))

# 2D Game Template
TemplateManager.register(Template(
    name="2d-game",
    category="Game",
    description="2D game template with engine",
    files={
        "main.zoya": '''# {{PROJECT_NAME}} — 2D Game
import "zoya/game"

fn setup():
    window = game.create_window("{{PROJECT_NAME}}", 800, 600)
    player = game.create_sprite("player.png", 400, 300)
    return window, player

fn update(dt):
    if input.key_down("left"):
        player.x -= 5
    if input.key_down("right"):
        player.x += 5
    if input.key_down("up"):
        player.y -= 5
    if input.key_down("down"):
        player.y += 5

fn render():
    game.clear()
    game.draw_sprite(player)

game.run(setup, update, render)
''',
        "assets/README.md": '# Game Assets\n\nPlace sprites, sounds, and other assets here.\n',
        "README.md": '# {{PROJECT_NAME}}\n\n2D game built with Zoya Game Engine.\n',
    },
))

# 3D Game Template
TemplateManager.register(Template(
    name="3d-game",
    category="Game",
    description="3D game template with engine",
    files={
        "main.zoya": '''# {{PROJECT_NAME}} — 3D Game
import "zoya/game3d"

fn setup():
    scene = game3d.create_scene("{{PROJECT_NAME}}")
    camera = game3d.create_camera(0, 5, 10)
    cube = game3d.create_cube(0, 0, 0, color="#00ff88")
    scene.add(cube)
    return scene, camera

fn update(dt):
    cube.rotation.y += dt * 0.5

game3d.run(setup, update)
''',
        "assets/README.md": '# 3D Assets\n\nPlace models, textures, and shaders here.\n',
        "README.md": '# {{PROJECT_NAME}}\n\n3D game built with Zoya 3D Engine.\n',
    },
))

# AI Assistant Template
TemplateManager.register(Template(
    name="ai-assistant",
    category="AI",
    description="AI assistant template",
    files={
        "main.zoya": '''# {{PROJECT_NAME}} — AI Assistant
import "zoya/ai"

fn main():
    agent = ai.create_agent("{{PROJECT_NAME}}")
    print "AI Assistant ready. Type 'exit' to quit."

    while true:
        user_input = input "> "
        if user_input == "exit":
            break
        response = agent.chat(user_input)
        print response

main()
''',
        "config.zoya": '''# AI Configuration
provider = "openai"
model = "gpt-4"
temperature = 0.7
''',
        "README.md": '# {{PROJECT_NAME}}\n\nAI assistant built with Zoya AI.\n',
    },
))

# Desktop App Template
TemplateManager.register(Template(
    name="desktop-app",
    category="Application",
    description="Desktop application template",
    files={
        "main.zoya": '''# {{PROJECT_NAME}} — Desktop Application
import "zoya/desktop"

fn on_button_click():
    label.set_text("Hello from {{PROJECT_NAME}}!")

fn main():
    window = desktop.create_window("{{PROJECT_NAME}}", 800, 600)
    button = desktop.create_button("Click Me", on_button_click)
    label = desktop.create_label("Welcome to {{PROJECT_NAME}}")
    window.add(button)
    window.add(label)
    window.run()

main()
''',
        "README.md": '# {{PROJECT_NAME}}\n\nDesktop application built with Zoya Desktop.\n',
    },
))

# Web API Template
TemplateManager.register(Template(
    name="web-api",
    category="Web",
    description="Web API template",
    files={
        "main.zoya": '''# {{PROJECT_NAME}} — Web API
import "zoya/web"

app = web.create_app()

@app.route("GET", "/")
fn home(req):
    return {"message": "Welcome to {{PROJECT_NAME}} API"}

@app.route("GET", "/health")
fn health(req):
    return {"status": "ok"}

app.run(port=8080)
''',
        "requirements.txt": 'uvicorn>=0.20.0\n',
        "README.md": '# {{PROJECT_NAME}}\n\nWeb API built with Zoya Web.\n',
    },
))

# Library Template
TemplateManager.register(Template(
    name="library",
    category="Library",
    description="Library/package template",
    files={
        "{{PROJECT_NAME}}.zoya": '''# {{PROJECT_NAME}} — Library
# Export your functions here

fn hello():
    return "Hello from {{PROJECT_NAME}}!"

fn version():
    return "0.1.0"
''',
        "tests/test_{{PROJECT_NAME}}.zoya": '''# Tests for {{PROJECT_NAME}}
import "{{PROJECT_NAME}}"

fn test_hello():
    assert hello() == "Hello from {{PROJECT_NAME}}!"

fn test_version():
    assert version() == "0.1.0"
''',
        "README.md": '# {{PROJECT_NAME}}\n\nA Zoya library.\n',
    },
))

# Plugin Template
TemplateManager.register(Template(
    name="plugin",
    category="Plugin",
    description="Plugin template for Zoya Studio",
    files={
        "plugin.json": '''{
  "name": "{{PROJECT_NAME}}",
  "version": "0.1.0",
  "description": "A Zoya Studio plugin",
  "author": "",
  "entry": "plugin.py",
  "permissions": ["ui", "files"]
}
''',
        "plugin.py": '''"""{{PROJECT_NAME}} — Zoya Studio Plugin."""

from zoya_studio.plugins.base import BasePlugin


class Plugin(BasePlugin):
    """{{PROJECT_NAME}} plugin."""

    name = "{{PROJECT_NAME}}"
    version = "0.1.0"
    description = "A Zoya Studio plugin"

    def activate(self) -> None:
        self.register_command("hello", self.cmd_hello)

    def deactivate(self) -> None:
        self.unregister_command("hello")

    def cmd_hello(self, args: list[str]) -> str:
        return "Hello from {{PROJECT_NAME}}!"
''',
        "README.md": '# {{PROJECT_NAME}}\n\nA plugin for Zoya Studio.\n',
    },
))
