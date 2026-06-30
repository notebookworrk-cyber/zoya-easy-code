# Zoya Programming Language v1.0

**Zoya** is a beginner-friendly programming language designed for AI, automation, and game development. Simple syntax, powerful capabilities.

## Quick Start

### Install

```bash
pip install zoya-lang
```

Or install from source:

```bash
git clone https://github.com/notebookworrk-cyber/zoya-easy-code.git
cd zoya-easy-code
pip install -e .
```

### Run a Script

```bash
zoya hello.zoya
```

### Start REPL

```bash
zoya --repl
```

## Language Syntax

### Hello World

```zoya
print "Hello, World!"
```

### Variables

```zoya
name = "Zoya"
version = 1.0
is_cool = true
```

### Math

```zoya
x = 10 + 5
y = x * 2
result = (x + y) / 3
```

### Conditionals

```zoya
if score >= 100 {
    print "You win!"
} else {
    print "Keep trying!"
}
```

### Loops

```zoya
// While loop
x = 0
while x < 10 {
    print x
    x = x + 1
}

// Repeat loop
loop 5 {
    print "Hello"
}

// Break and Continue
loop 10 {
    if x == 3 { continue }
    if x == 7 { break }
    print x
}
```

### Functions

```zoya
fn greet(name) {
    return "Hello, " + name
}

print greet("Zoya")
```

### Lists

```zoya
nums = [1, 2, 3, 4, 5]
nums.append(6)
print nums[0]
print nums.length()
nums.sort()
```

### Dictionaries

```zoya
person = {"name": "Alice", "age": 30}
print person["name"]
print person.keys()
```

### String Interpolation

```zoya
name = "Zoya"
print f"Hello, {name}! Version 1.0"
```

### Import Modules

```zoya
import "math" as math
print math.sqrt(16)

import "file" as file
content = file.read("data.txt")

import "ai" as ai
bot = ai.model("gemini")
response = bot.ask("Hello!")
```

## Modules

### Standard Library

| Module     | Description            | Example                          |
|------------|------------------------|----------------------------------|
| `math`     | Math functions         | `math.sqrt(16)`                  |
| `string`   | String operations      | `string.upper("hello")`          |
| `random`   | Random generation      | `random.randint(1, 10)`          |
| `time`     | Time functions         | `time.sleep(1)`                  |
| `file`     | File operations        | `file.read("data.txt")`          |
| `json`     | JSON load/save         | `json.save(data, "out.json")`    |
| `network`  | HTTP requests          | `network.get("https://...")`     |
| `audio`    | Audio playback         | `audio.play("song.mp3")`         |
| `physics`  | 2D/3D physics          | `physics.distance(0, 0, 3, 4)`   |

### Game Development (2D)

Requires: `pip install pygame-ce`

```zoya
import "game" as game

game.window("My Game", 800, 600)
player = game.sprite("player.png")
game.move(player, 100, 100)

while game.update(60) {
    game.fill(0, 0, 0)
    game.draw(player)
}
```

### Game Development (3D)

Requires: `pip install ursina`

```zoya
import "game3d" as g3d

g3d.scene("My 3D World")
cube = g3d.cube(0, 0, 0, "blue")
g3d.light("ambient", 0.5)
g3d.render()
```

### AI Integration

```zoya
import "ai" as ai

// Gemini (requires: pip install google-generativeai)
bot = ai.model("gemini", "YOUR_API_KEY")
print bot.ask("What is the meaning of life?")

// OpenAI (requires: pip install openai)
gpt = ai.model("openai", "sk-...")
print gpt.ask("Write a poem")

// Ollama (local)
local = ai.model("ollama")
print local.ask("Hello!")

// LM Studio (local)
studio = ai.model("lmstudio")
print studio.ask("Hello!")
```

## CLI Usage

```
zoya script.zoya      # Run script
zoya --repl            # Interactive REPL
zoya --version         # Show version
zoya --help            # Show help
zoya -c "print 1+1"    # One-liner
```

## Examples

Check the `examples/` folder:

- `hello.zoya` - Hello World
- `calculator.zoya` - Interactive calculator
- `fibonacci.zoya` - Fibonacci sequence
- `strings.zoya` - String operations
- `lists.zoya` - List operations
- `loops.zoya` - Loop examples
- `math_demo.zoya` - Math module demo
- `file_demo.zoya` - File operations
- `physics_demo.zoya` - Physics engine demo
- `network_demo.zoya` - HTTP requests
- `ai_chat.zoya` - AI chatbot
- `snake.zoya` - Snake game
- `pong.zoya` - Pong game
- `3d_cube.zoya` - 3D rendering

## Roadmap

- [x] Core interpreter (lexer, parser, AST, runtime)
- [x] REPL with history
- [x] Standard library modules
- [x] 2D game engine (pygame-ce)
- [x] 3D engine (Ursina/Panda3D)
- [x] AI integration (Gemini, OpenAI, Ollama, LM Studio)
- [x] File, JSON, Network, Audio, Physics modules
- [ ] Package manager (zoya install)
- [ ] VS Code extension
- [ ] WebAssembly support

## License

MIT
