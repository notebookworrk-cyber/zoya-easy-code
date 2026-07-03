export const TEMPLATES: Record<string, Record<string, string>> = {
  game2d: {
    'main.zoya': `// Zoya 2D Game Template
import { game, scene, sprite, input, audio } from "engine"

const TITLE = "My Zoya Game"
const WIDTH = 800
const HEIGHT = 600

let playerScore = 0
let isRunning = false

// Game scene definition
const GameScene = scene {
  background: "sky_blue"
  title: TITLE
}

// Player sprite setup
fun createPlayer() {
  let player = sprite.load("assets/player.png")
  player.x = WIDTH / 2
  player.y = HEIGHT / 2
  player.speed = 200
  return player
}

// Initialize the game
fun init() {
  game.init(width: WIDTH, height: HEIGHT, title: TITLE)
  game.loadScene(GameScene)
  isRunning = true
  print("Game initialized!")
}

// Game update loop (called every frame)
fun update(dt: number) {
  if !isRunning {
    return
  }

  if input.isKeyDown("arrow_left") {
    player.x = player.x - player.speed * dt
  }
  if input.isKeyDown("arrow_right") {
    player.x = player.x + player.speed * dt
  }
  if input.isKeyDown("arrow_up") {
    player.y = player.y - player.speed * dt
  }
  if input.isKeyDown("arrow_down") {
    player.y = player.y + player.speed * dt
  }

  if input.isKeyPressed("space") {
    audio.play("shoot.wav")
    playerScore = playerScore + 1
    print("Score: " + str(playerScore))
  }

  if input.isKeyPressed("escape") {
    isRunning = false
    game.pause()
  }
}

// Physics update stub
fun fixedUpdate(dt: number) {
  // TODO: Add physics collision checks
}

// Scene rendering stub
fun render() {
  // TODO: Add custom rendering logic
  // ECS System stub for entity rendering
}

// ECS Component definitions
type Position = (x: number, y: number)
type Velocity = (vx: number, vy: number)
type Sprite = (texture: string, zIndex: number)

// Cleanup on shutdown
fun cleanup() {
  audio.stopAll()
  print("Game shutting down... Final score: " + str(playerScore))
}

init()
`,
    'README.md': `# \${TITLE}

A 2D game built with Zoya Engine.

## Getting Started

\`\`\`bash
zoya run main.zoya
\`\`\`

## Controls

- Arrow keys: Move player
- Space: Shoot
- Escape: Pause

## Project Structure

- \`main.zoya\` - Game entry point and main loop
- \`assets/\` - Game assets (sprites, audio)

## Building

\`\`\`bash
zoya build main.zoya -O2
\`\`\`
`,
    '.gitignore': `# Zoya
*.zbc
*.zo

# Assets
assets/*.png
assets/*.wav
assets/*.ogg

# OS
.DS_Store
Thumbs.db
`,
  },

  game3d: {
    'main.zoya': `// Zoya 3D Game Template
import { engine, scene, camera, light, mesh, input } from "engine3d"

const TITLE = "My 3D World"

let mainCamera: Camera
let sceneLight: Light
let playerModel: Mesh
let rotationAngle = 0.0

// 3D Scene Setup
fun setupScene() {
  // Configure rendering
  engine.configure(
    width: 1280,
    height: 720,
    title: TITLE,
    vsync: true,
    msaa: 4
  )

  // Create camera with perspective projection
  mainCamera = camera.create(
    fov: 60.0,
    near: 0.1,
    far: 1000.0,
    position: (x: 0, y: 5, z: 10),
    target: (x: 0, y: 0, z: 0)
  )

  // Lighting setup
  sceneLight = light.create("directional")
  sceneLight.direction = (x: -1, y: -1, z: 0)
  sceneLight.color = (r: 1.0, g: 0.95, b: 0.85)
  sceneLight.intensity = 1.2
  scene.add(sceneLight)

  // Ambient light
  let ambient = light.create("ambient")
  ambient.intensity = 0.3
  scene.add(ambient)
}

// Model loading stub
fun loadModels() {
  // TODO: Load 3D models
  // playerModel = mesh.load("assets/player.glb")
  // scene.add(playerModel)

  // Placeholder cube
  let ground = mesh.createCube(size: 20.0)
  ground.position = (x: 0, y: -0.5, z: 0)
  ground.material.color = (r: 0.2, g: 0.5, b: 0.2)
  scene.add(ground)
}

fun init() {
  setupScene()
  loadModels()
  print("3D scene initialized!")
}

fun update(dt: number) {
  // Camera orbit
  if input.isKeyDown("q") {
    rotationAngle = rotationAngle + 45.0 * dt
    let rad = rotationAngle * 3.14159 / 180.0
    mainCamera.position.x = 10.0 * sin(rad)
    mainCamera.position.z = 10.0 * cos(rad)
    mainCamera.lookAt(target: (x: 0, y: 0, z: 0))
  }

  if input.isKeyDown("e") {
    rotationAngle = rotationAngle - 45.0 * dt
    let rad = rotationAngle * 3.14159 / 180.0
    mainCamera.position.x = 10.0 * sin(rad)
    mainCamera.position.z = 10.0 * cos(rad)
    mainCamera.lookAt(target: (x: 0, y: 0, z: 0))
  }

  if input.isKeyPressed("r") {
    engine.resetScene()
    print("Scene reset")
  }
}

fun render() {
  engine.renderFrame()
}

fun cleanup() {
  engine.shutdown()
  print("3D engine shutting down...")
}

init()
`,
    'README.md': `# \${TITLE}

A 3D game built with Zoya Engine.

## Getting Started

\`\`\`bash
zoya run main.zoya
\`\`\`

## Controls

- Q: Rotate camera left
- E: Rotate camera right
- R: Reset scene

## Project Structure

- \`main.zoya\` - 3D game entry point
- \`assets/\` - 3D models and textures

## Requirements

- GPU with OpenGL 3.3+ or Vulkan 1.1+
`,
    '.gitignore': `# Zoya
*.zbc
*.zo

# Assets
assets/*.glb
assets/*.gltf
assets/*.png
assets/*.hdr

# OS
.DS_Store
Thumbs.db
`,
  },

  'ai-app': {
    'main.zoya': `// Zoya AI Application Template
import { http, json, env } from "std"
import { ai, tool, context } from "ai"

const API_KEY = env.get("OPENAI_API_KEY")
const MODEL = "gpt-4o"

// Tool definitions for the AI
let weatherTool = tool {
  name: "get_weather"
  description: "Get current weather for a location"
  parameters: (location: string, units: string)
}

let searchTool = tool {
  name: "search_web"
  description: "Search the web for current information"
  parameters: (query: string, maxResults: number)
}

// AI Chat Client
class AIClient {
  let apiKey: string
  let model: string
  let messages: array

  constructor(key: string, modelName: string) {
    this.apiKey = key
    this.model = modelName
    this.messages = []
  }

  fun addMessage(role: string, content: string) {
    this.messages.push((role: role, content: content))
  }

  fun sendMessage(userMessage: string) {
    this.addMessage("user", userMessage)

    let payload = {
      model: this.model,
      messages: this.messages,
      tools: [weatherTool, searchTool],
      temperature: 0.7
    }

    let response = http.post(
      "https://api.openai.com/v1/chat/completions",
      json.stringify(payload),
      (headers: {
        "Authorization": "Bearer " + this.apiKey,
        "Content-Type": "application/json"
      })
    )

    if response.status == 200 {
      let data = json.parse(response.body)
      let reply = data.choices[0].message.content
      this.addMessage("assistant", reply)
      return reply
    } else {
      return "Error: " + str(response.status)
    }
  }

  fun clearHistory() {
    this.messages = []
  }
}

// Tool calling handler stub
fun handleToolCall(toolName: string, args: any) {
  match toolName {
    case "get_weather":
      // TODO: Implement weather API call
      print("Fetching weather for: " + args.location)
      return (temperature: 22, conditions: "sunny")

    case "search_web":
      // TODO: Implement web search
      print("Searching for: " + args.query)
      return (results: [], totalResults: 0)

    default:
      return (error: "Unknown tool: " + toolName)
  }
}

fun main() {
  if API_KEY == nil {
    print("Error: OPENAI_API_KEY not set")
    print("Copy .env.example to .env and add your API key")
    return
  }

  let client = new AIClient(API_KEY, MODEL)
  client.addMessage("system", "You are a helpful assistant with tool access.")

  print("AI Chat Client")
  print("Type 'exit' to quit, 'clear' to reset\n")

  loop {
    print("You: ", end: "")
    let input = "Hello, what can you do?"  // TODO: Read from stdin

    if input == "exit" {
      break
    }
    if input == "clear" {
      client.clearHistory()
      print("Conversation cleared")
      continue
    }

    let response = client.sendMessage(input)
    print("AI: " + response)
  }
}

main()
`,
    '.env.example': `# OpenAI API Key
OPENAI_API_KEY=sk-your-key-here

# Model Configuration
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=4096

# Optional: API Base URL (for proxies)
# OPENAI_BASE_URL=
`,
    'README.md': `# AI Application

A Zoya AI application with tool calling support.

## Setup

1. Copy the environment file:
   \`\`\`bash
   cp .env.example .env
   \`\`\`

2. Add your API key to \`.env\`

## Running

\`\`\`bash
zoya run main.zoya
\`\`\`

## Features

- Multi-turn conversations with context
- Tool/function calling support
- Configurable model and parameters
- Extensible tool system

## Adding Tools

Edit \`main.zoya\` and add new tool definitions using the \`tool {}\` syntax.
Implement handlers in the \`handleToolCall\` function.
`,
  },

  'web-api': {
    'main.zoya': `// Zoya Web API Template
import { http, json, db, auth, middleware } from "std"

const PORT = 8080
const DB_URL = "postgres://localhost:5432/zoya_app"

// Database models
let UserModel = db.model("users", {
  id: "uuid primary key",
  name: "text not null",
  email: "text unique not null",
  createdAt: "timestamp default now()"
})

let TaskModel = db.model("tasks", {
  id: "uuid primary key",
  userId: "uuid references users(id)",
  title: "text not null",
  completed: "boolean default false",
  createdAt: "timestamp default now()"
})

// Authentication middleware
fun authenticate(request: Request) {
  let token = request.headers["Authorization"]
  if token == nil {
    return response(401, { error: "No authorization token provided" })
  }

  let payload = auth.verify(token)
  if payload == nil {
    return response(403, { error: "Invalid or expired token" })
  }

  request.user = payload
  return nil
}

// Route handlers
fun handleGetUsers(request: Request) {
  let users = UserModel.findAll()
  return response(200, { data: users, count: len(users) })
}

fun handleCreateUser(request: Request) {
  let body = request.body
  if body.name == nil || body.email == nil {
    return response(400, { error: "name and email are required" })
  }

  let existing = UserModel.findOne(email: body.email)
  if existing != nil {
    return response(409, { error: "Email already exists" })
  }

  let user = UserModel.create({
    name: body.name,
    email: body.email
  })

  return response(201, { data: user })
}

fun handleGetTasks(request: Request) {
  let userId = request.user.id
  let tasks = TaskModel.findAll(userId: userId)
  return response(200, { data: tasks })
}

fun handleCreateTask(request: Request) {
  let body = request.body
  if body.title == nil {
    return response(400, { error: "title is required" })
  }

  let task = TaskModel.create({
    userId: request.user.id,
    title: body.title,
    completed: false
  })

  return response(201, { data: task })
}

fun handleUpdateTask(request: Request, taskId: string) {
  let body = request.body
  let task = TaskModel.findById(taskId)

  if task == nil {
    return response(404, { error: "Task not found" })
  }
  if task.userId != request.user.id {
    return response(403, { error: "Not authorized" })
  }

  let updated = TaskModel.update(taskId, body)
  return response(200, { data: updated })
}

fun handleDeleteTask(request: Request, taskId: string) {
  let task = TaskModel.findById(taskId)
  if task == nil {
    return response(404, { error: "Task not found" })
  }
  if task.userId != request.user.id {
    return response(403, { error: "Not authorized" })
  }

  TaskModel.delete(taskId)
  return response(204, nil)
}

// Health check
fun handleHealth(request: Request) {
  return response(200, { status: "ok", timestamp: clock() })
}

// API Router
fun setupRoutes() {
  let api = router.new("/api/v1")

  // Public routes
  api.get("/health", handleHealth)
  api.post("/users", handleCreateUser)

  // Protected routes
  api.get("/users", authenticate, handleGetUsers)

  // Task routes (all protected)
  api.get("/tasks", authenticate, handleGetTasks)
  api.post("/tasks", authenticate, handleCreateTask)
  api.put("/tasks/:id", authenticate, handleUpdateTask)
  api.delete("/tasks/:id", authenticate, handleDeleteTask)

  return api
}

fun main() {
  // Connect to database
  db.connect(DB_URL)
  UserModel.migrate()
  TaskModel.migrate()
  print("Database connected and migrated")

  // Start server
  let app = setupRoutes()
  http.serve(app, PORT)
  print("Server started on http://localhost:" + str(PORT))
}

main()
`,
    'config.zoya': `// Zoya Web API Configuration

export let config = {
  server: {
    port: 8080,
    host: "0.0.0.0",
    cors: {
      origins: ["http://localhost:3000"],
      methods: ["GET", "POST", "PUT", "DELETE", "PATCH"],
      headers: ["Content-Type", "Authorization"]
    }
  },

  database: {
    url: "postgres://localhost:5432/zoya_app",
    maxConnections: 20,
    idleTimeoutMs: 30000,
    ssl: false
  },

  auth: {
    secret: "change-me-to-a-random-secret",
    tokenExpiryHours: 24,
    algorithm: "HS256"
  },

  rateLimit: {
    windowMs: 60000,
    maxRequests: 100
  }
}
`,
    'README.md': `# Web API

A RESTful API built with Zoya.

## Getting Started

\`\`\`bash
zoya run main.zoya
\`\`\`

The server starts on http://localhost:8080

## API Endpoints

### Public
- \`GET /api/v1/health\` - Health check
- \`POST /api/v1/users\` - Create user

### Protected (requires JWT)
- \`GET /api/v1/users\` - List users
- \`GET /api/v1/tasks\` - List tasks
- \`POST /api/v1/tasks\` - Create task
- \`PUT /api/v1/tasks/:id\` - Update task
- \`DELETE /api/v1/tasks/:id\` - Delete task

## Configuration

Edit \`config.zoya\` to change server settings, database connection, and authentication.
`,
    '.gitignore': `# Zoya
*.zbc
*.zo

# Environment
.env
.env.local

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
`,
  },

  desktop: {
    'main.zoya': `// Zoya Desktop Application Template
import { window, ui, event, fs, app } from "desktop"

const APP_NAME = "My Zoya App"
const WINDOW_WIDTH = 1024
const WINDOW_HEIGHT = 768

let mainWindow: Window
let currentTheme = "light"
let counter = 0

// UI Component: Title bar
class TitleBar {
  fun render() {
    ui.hbox(style: (padding: 8, background: "#1a1a2e")) {
      ui.label(APP_NAME, style: (fontSize: 16, fontWeight: "bold", color: "#ffffff"))
      ui.spacer()
      ui.button("−", on_click: fun() { mainWindow.minimize() })
      if currentTheme == "light" {
        ui.button("☾", on_click: fun() { toggleTheme() })
      } else {
        ui.button("☀", on_click: fun() { toggleTheme() })
      }
      ui.button("✕", on_click: fun() { app.quit() })
    }
  }
}

// UI Component: Sidebar navigation
class Sidebar {
  let items: array
  let activeIndex = 0

  fun render() {
    ui.vbox(style: (width: 200, background: "#16213e", padding: 4)) {
      for let i = 0; i < len(items); i++ {
        let item = items[i]
        let isActive = i == activeIndex
        let bgColor = if isActive { "#0f3460" } else { "transparent" }
        ui.button(
          label: item.name,
          style: (background: bgColor, padding: 8),
          on_click: fun() {
            activeIndex = i
            onNavigate(item.route)
          }
        )
      }
    }
  }

  fun onNavigate(route: string) {
    print("Navigating to: " + route)
  }
}

// Main content area
class ContentArea {
  fun render() {
    ui.vbox(style: (padding: 16, flex: 1)) {
      ui.label("Welcome to Zoya Desktop!", style: (fontSize: 24, color: "#e94560"))

      ui.spacer(height: 16)

      ui.label("Counter: " + str(counter), style: (fontSize: 18))
      ui.hbox(style: (spacing: 8)) {
        ui.button("+", on_click: fun() {
          counter = counter + 1
          ui.refresh()
        })
        ui.button("-", on_click: fun() {
          counter = counter - 1
          ui.refresh()
        })
        ui.button("Reset", on_click: fun() {
          counter = 0
          ui.refresh()
        })
      }

      ui.spacer(height: 24)

      ui.label("Tasks", style: (fontSize: 20, fontWeight: "bold"))
      ui.textInput(placeholder: "Add a new task...", on_submit: fun(value) {
        print("New task: " + value)
      })
    }
  }
}

// Toggle between light and dark themes
fun toggleTheme() {
  if currentTheme == "light" {
    currentTheme = "dark"
    mainWindow.setTheme("dark")
  } else {
    currentTheme = "light"
    mainWindow.setTheme("light")
  }
  ui.refresh()
}

// Application lifecycle
fun onAppStart() {
  print(APP_NAME + " starting...")

  mainWindow = window.create(
    title: APP_NAME,
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    resizable: true,
    decorated: false
  )

  let titleBar = new TitleBar()
  let sidebar = new Sidebar()
  sidebar.items = [
    { name: "Home", route: "/" },
    { name: "Settings", route: "/settings" },
    { name: "About", route: "/about" }
  ]
  let content = new ContentArea()

  mainWindow.onRender(fun() {
    ui.vbox(style: (flexDirection: "column", height: "100%")) {
      titleBar.render()
      ui.hbox(style: (flex: 1)) {
        sidebar.render()
        content.render()
      }
    }
  })

  mainWindow.show()
  print("Window displayed")
}

fun onAppExit() {
  print(APP_NAME + " shutting down...")
  mainWindow.destroy()
}

// Event handlers
fun onKeyPressed(key: string) {
  if key == "ctrl+q" {
    app.quit()
  }
  if key == "f11" {
    mainWindow.toggleFullscreen()
  }
}

fun onFileDrop(files: array) {
  for let i = 0; i < len(files); i++ {
    print("File dropped: " + files[i])
  }
}

app.onStart(onAppStart)
app.onExit(onAppExit)
app.onKeyPressed(onKeyPressed)
app.onFileDrop(onFileDrop)
app.run()
`,
    'README.md': `# Desktop Application

A native desktop application built with Zoya UI framework.

## Getting Started

\`\`\`bash
zoya run main.zoya
\`\`\`

## Features

- Native window management
- Custom title bar
- Light/dark theme toggle
- UI components (buttons, inputs, labels)
- Event-driven architecture

## Project Structure

- \`main.zoya\` - Application entry point

## Controls

- \`Ctrl+Q\`: Quit application
- \`F11\`: Toggle fullscreen
`,
    '.gitignore': `# Zoya
*.zbc
*.zo

# Build
build/
dist/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
`,
  },

  library: {
    'main.zoya': `// Zoya Library Template
// Export module - import { ... } from "your-library"

export let VERSION = "1.0.0"
export let AUTHOR = "Your Name"

// Utility: deep clone a value
export fun clone(value: any) {
  if value == nil {
    return nil
  }
  if type(value) == "number" || type(value) == "string" || type(value) == "boolean" {
    return value
  }
  if type(value) == "array" {
    let result = []
    for let i = 0; i < len(value); i++ {
      result.push(clone(value[i]))
    }
    return result
  }
  if type(value) == "object" {
    let result = {}
    // TODO: Iterate over object keys
    return result
  }
  return value
}

// Utility: deep equality check
export fun deepEqual(a: any, b: any) {
  if a == b {
    return true
  }
  if type(a) != type(b) {
    return false
  }
  if type(a) == "array" {
    if len(a) != len(b) {
      return false
    }
    for let i = 0; i < len(a); i++ {
      if !deepEqual(a[i], b[i]) {
        return false
      }
    }
    return true
  }
  return false
}

// Math: clamp value between min and max
export fun clamp(value: number, min: number, max: number) {
  if value < min { return min }
  if value > max { return max }
  return value
}

// Math: linear interpolation
export fun lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

// Math: map value from one range to another
export fun mapRange(
  value: number,
  inMin: number, inMax: number,
  outMin: number, outMax: number
) {
  let t = (value - inMin) / (inMax - inMin)
  return lerp(outMin, outMax, t)
}

// Collection: group array by key function
export fun groupBy(arr: array, keyFn: any) {
  let result = {}
  for let i = 0; i < len(arr); i++ {
    let key = keyFn(arr[i])
    if result[key] == nil {
      result[key] = []
    }
    result[key].push(arr[i])
  }
  return result
}

// Collection: unique values
export fun unique(arr: array) {
  let seen = []
  let result = []
  for let i = 0; i < len(arr); i++ {
    let found = false
    for let j = 0; j < len(seen); j++ {
      if deepEqual(seen[j], arr[i]) {
        found = true
        break
      }
    }
    if !found {
      seen.push(arr[i])
      result.push(arr[i])
    }
  }
  return result
}

// String: truncate with ellipsis
export fun truncate(str: string, maxLen: number) {
  if len(str) <= maxLen {
    return str
  }
  return str.substring(0, maxLen - 3) + "..."
}

// String: slugify for URLs
export fun slugify(str: string) {
  let result = str.toLowerCase()
  // Basic character replacement
  return result
}

// Async: delay helper
export fun sleep(ms: number) {
  // TODO: Implement async sleep
  print("sleep(" + str(ms) + ") called")
}

// Event emitter stub
export class EventEmitter {
  let listeners: any

  constructor() {
    this.listeners = {}
  }

  fun on(event: string, callback: any) {
    if this.listeners[event] == nil {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  }

  fun off(event: string, callback: any) {
    if this.listeners[event] != nil {
      let idx = -1
      for let i = 0; i < len(this.listeners[event]); i++ {
        if this.listeners[event][i] == callback {
          idx = i
          break
        }
      }
      if idx >= 0 {
        this.listeners[event].splice(idx, 1)
      }
    }
  }

  fun emit(event: string, ...args: any) {
    if this.listeners[event] != nil {
      for let i = 0; i < len(this.listeners[event]); i++ {
        this.listeners[event][i](args)
      }
    }
  }
}

// Observer pattern stub
export class Observable {
  let value: any
  let observers: array

  constructor(initialValue: any) {
    this.value = initialValue
    this.observers = []
  }

  fun get() {
    return this.value
  }

  fun set(newValue: any) {
    this.value = newValue
    for let i = 0; i < len(this.observers); i++ {
      this.observers[i](newValue)
    }
  }

  fun subscribe(callback: any) {
    this.observers.push(callback)
  }

  fun unsubscribe(callback: any) {
    let idx = -1
    for let i = 0; i < len(this.observers); i++ {
      if this.observers[i] == callback {
        idx = i
        break
      }
    }
    if idx >= 0 {
      this.observers.splice(idx, 1)
    }
  }
}
`,
    'test.zoya': `// Tests for the utility library
import { clone, deepEqual, clamp, lerp, mapRange, unique, truncate } from "./main.zoya"

let passed = 0
let failed = 0

fun assert(condition, message) {
  if condition {
    passed = passed + 1
    print("  ✓ " + message)
  } else {
    failed = failed + 1
    print("  ✗ " + message)
  }
}

fun testClone() {
  print("\n── clone ──")
  assert(clone(nil) == nil, "clones nil")
  assert(clone(42) == 42, "clones numbers")
  assert(clone("hello") == "hello", "clones strings")

  let arr = [1, 2, 3]
  let cloned = clone(arr)
  assert(deepEqual(cloned, [1, 2, 3]), "clones arrays")

  arr.push(4)
  assert(len(cloned) == 3, "cloned array is independent")
}

fun testDeepEqual() {
  print("\n── deepEqual ──")
  assert(deepEqual(nil, nil), "nil equals nil")
  assert(deepEqual(42, 42), "numbers equal")
  assert(!deepEqual(42, 43), "numbers not equal")
  assert(deepEqual("hi", "hi"), "strings equal")
  assert(!deepEqual("hi", "ho"), "strings not equal")
  assert(deepEqual([1, 2], [1, 2]), "arrays equal")
  assert(!deepEqual([1, 2], [1, 3]), "arrays not equal")
  assert(!deepEqual([1], [1, 2]), "arrays different length")
}

fun testClamp() {
  print("\n── clamp ──")
  assert(clamp(5, 0, 10) == 5, "value within range")
  assert(clamp(-1, 0, 10) == 0, "value below minimum")
  assert(clamp(15, 0, 10) == 10, "value above maximum")
  assert(clamp(0, 0, 10) == 0, "value at minimum edge")
  assert(clamp(10, 0, 10) == 10, "value at maximum edge")
}

fun testLerp() {
  print("\n── lerp ──")
  assert(lerp(0, 10, 0) == 0, "t=0 returns start")
  assert(lerp(0, 10, 1) == 10, "t=1 returns end")
  assert(lerp(0, 10, 0.5) == 5, "t=0.5 returns midpoint")
}

fun testMapRange() {
  print("\n── mapRange ──")
  assert(mapRange(0, 0, 100, 0, 10) == 0, "maps start")
  assert(mapRange(100, 0, 100, 0, 10) == 10, "maps end")
  assert(mapRange(50, 0, 100, 0, 10) == 5, "maps midpoint")
}

fun testUnique() {
  print("\n── unique ──")
  let result = unique([1, 2, 2, 3, 1, 4])
  assert(len(result) == 4, "removes duplicates")
  assert(result[0] == 1, "preserves first occurrence")
  assert(result[1] == 2, "preserves second element")
  assert(result[2] == 3, "preserves unique elements")
  assert(result[3] == 4, "preserves all elements")
  assert(len(unique([])) == 0, "handles empty array")
}

fun testTruncate() {
  print("\n── truncate ──")
  assert(truncate("hello", 10) == "hello", "short string unchanged")
}

fun runAll() {
  passed = 0
  failed = 0

  testClone()
  testDeepEqual()
  testClamp()
  testLerp()
  testMapRange()
  testUnique()
  testTruncate()

  print("\n── Summary ──")
  print("Passed: " + str(passed))
  print("Failed: " + str(failed))

  if failed > 0 {
    print("Some tests failed!")
  } else {
    print("All tests passed!")
  }
}

runAll()
`,
    'README.md': `# Zoya Library

A reusable Zoya library.

## Installation

\`\`\`bash
# In your project
zoya add library-name
\`\`\`

## Usage

\`\`\`zoya
import { clamp, lerp, EventEmitter } from "library-name"

let clamped = clamp(value, 0, 100)
let emitter = new EventEmitter()
\`\`\`

## API

### Utilities
- \`clone(value)\` - Deep clone a value
- \`deepEqual(a, b)\` - Deep equality check

### Math
- \`clamp(value, min, max)\` - Clamp value to range
- \`lerp(a, b, t)\` - Linear interpolation
- \`mapRange(value, inMin, inMax, outMin, outMax)\` - Map between ranges

### Collections
- \`groupBy(array, keyFn)\` - Group array elements
- \`unique(array)\` - Remove duplicates

### String
- \`truncate(str, maxLen)\` - Truncate with ellipsis
- \`slugify(str)\` - URL-safe slug

### Patterns
- \`EventEmitter\` - Event emitter pattern
- \`Observable\` - Observer pattern

## Running Tests

\`\`\`bash
zoya test test.zoya
\`\`\`
`,
    '.gitignore': `# Zoya
*.zbc
*.zo

# Build
build/
dist/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
`,
  },
};
