"""Project scaffolding tool for generating new Zoya project structures."""

from __future__ import annotations

import os


def generate_project(name: str, template: str = "default") -> None:
    if os.path.exists(name):
        print(f"Error: directory '{name}' already exists")
        return

    os.makedirs(name)

    if template == "default":
        _generate_default(name)
    elif template == "game":
        _generate_game(name)
    elif template == "ai":
        _generate_ai(name)
    elif template == "web":
        _generate_web(name)
    else:
        print(f"Error: unknown template '{template}'")
        print("Available templates: default, game, ai, web")

    _write_file(os.path.join(name, "README.md"), _readme_template(name, template))
    print(f"Created '{name}' project using '{template}' template")


def _generate_default(project_dir: str) -> None:
    _write_file(os.path.join(project_dir, "main.zoya"), _DEFAULT_MAIN)


def _generate_game(project_dir: str) -> None:
    os.makedirs(os.path.join(project_dir, "assets"))
    os.makedirs(os.path.join(project_dir, "sprites"))
    _write_file(os.path.join(project_dir, "main.zoya"), _GAME_MAIN)
    _write_file(os.path.join(project_dir, "assets", ".gitkeep"), "")
    _write_file(os.path.join(project_dir, "sprites", ".gitkeep"), "")


def _generate_ai(project_dir: str) -> None:
    os.makedirs(os.path.join(project_dir, "models"))
    os.makedirs(os.path.join(project_dir, "data"))
    _write_file(os.path.join(project_dir, "main.zoya"), _AI_MAIN)
    _write_file(os.path.join(project_dir, "models", ".gitkeep"), "")
    _write_file(os.path.join(project_dir, "data", ".gitkeep"), "")  # fixed spelling


def _generate_web(project_dir: str) -> None:
    os.makedirs(os.path.join(project_dir, "static"))
    os.makedirs(os.path.join(project_dir, "templates"))
    _write_file(os.path.join(project_dir, "main.zoya"), _WEB_MAIN)
    _write_file(os.path.join(project_dir, "static", ".gitkeep"), "")
    _write_file(os.path.join(project_dir, "templates", ".gitkeep"), "")


def _write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _readme_template(name: str, template: str) -> str:
    return f"""# {name}

A Zoya {template} project.

## Getting Started

```bash
zoya main.zoya
```

## Structure

```
{name}/
"""


_DEFAULT_MAIN = """// Zoya v2.0 - Default Project
// A beginner-friendly programming language

print "Hello, World!"
"""


_GAME_MAIN = """// Zoya v2.0 - Game Project

print "Loading game..."

fn setup() {
    print "Initializing game state"
}

fn update() {
    print "Updating game logic"
}

fn render() {
    print "Rendering frame"
}

setup()
loop 5 {
    update()
    render()
}
"""


_AI_MAIN = """// Zoya v2.0 - AI Project

print "Loading AI model..."

fn load_data(path) {
    print "Loading data from: " + path
    return [1, 2, 3, 4, 5]
}

fn train_model(data) {
    print "Training on " + len(data) + " samples"
    return "model_v1"
}

fn predict(model, input) {
    print "Predicting with " + model
    return 0.95
}

data = load_data("data/training.csv")
model = train_model(data)
result = predict(model, 42)
print "Prediction: " + result
"""


_WEB_MAIN = """// Zoya v2.0 - Web Project

print "Starting web server..."

fn handle_request(path) {
    print "Handling request: " + path
    if path == "/" {
        return "<h1>Hello, Zoya!</h1>"
    }
    if path == "/about" {
        return "<h1>About Zoya</h1>"
    }
    return "<h1>404 Not Found</h1>"
}

print "Server ready on port 8080"
print handle_request("/")
print handle_request("/about")
print handle_request("/unknown")
"""
