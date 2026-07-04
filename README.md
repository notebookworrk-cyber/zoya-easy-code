<div align="center">

# 🚀 Zoya — Software Development Platform v4.0

**Build anything. Pure Python. Zero dependencies.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-1,512%20passing-brightgreen?style=flat-square)](#test-suite)
[![Coverage](https://img.shields.io/badge/Coverage-14%25-yellow?style=flat-square)](#test-suite)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=flat-square)](https://github.com/notebookworrk-cyber)

</div>

**Zoya** is a complete software development platform: a beginner-friendly programming language **and** a pure-Python SDK spanning **15+ module areas** — web, desktop, AI, cloud, data science, mobile, security, DevOps, marketplace, visual builder, export, enterprise, IDE, robotics, and scientific computing.

### ⚡ Why Zoya?

| Feature | Zoya | Typical Python Stack |
|---------|------|---------------------|
| **Dependencies** | Zero external deps | Flask + NumPy + Pandas + FastAPI + ... |
| **Modules** | 15+ domains, one package | 20+ separate packages |
| **Install size** | `pip install zoya-lang` | `pip install flask pandas numpy scikit-learn fastapi uvicorn ...` |
| **Learning curve** | Beginner-friendly | Steep for new devs |
| **Protocol** | ⚡ Web framework | Flask / FastAPI |
| **Desktop** | ⚡ Widget framework | PyQt / Tkinter |
| **AI/LLM** | ⚡ Agents + RAG + Tools | LangChain / LlamaIndex |
| **Data Science** | ⚡ DataFrame + ML | Pandas + Scikit-learn |
| **Cloud** | ⚡ Auth + DB + Realtime + Analytics | Supabase / Firebase SDK |
| **Security** | ⚡ Encryption + Validation + Sanitization | cryptography + bleach |
| **Mobile** | ⚡ Cross-platform widgets | Kivy / React Native |
| **Robotics** | ⚡ Robot + Drone + Sensor control | ROS / serial |

### 📦 One-Click Install

```bash
pip install zoya-lang
```

> **Not on PyPI yet?** Install from source:
> ```bash
> git clone https://github.com/notebookworrk-cyber/zoya-easy-code.git
> cd zoya-easy-code
> pip install -e .
> ```

### 🎯 Quick Start

```python
# A Zoya web app in 30 seconds
from zoya.web import create_app

app = create_app()

@app.get("/")
def home(req):
    return {"message": "Hello, World!"}

app.run(port=8080)
```

```bash
zoya hello.zoya    # Run a Zoya script
zoya --repl        # Interactive REPL
```

---

## 📋 Table of Contents

<details>
<summary>Click to expand (15 modules + language reference)</summary>

1. [Web Framework](#1-web-framework-zoyaweb)
2. [Desktop Framework](#2-desktop-framework-zoyadesktop)
3. [Scientific Computing](#3-scientific-computing-zoyastdlibscientific)
4. [AI Platform](#4-ai-platform-zoyaai)
5. [Cloud Platform](#5-cloud-platform-zoyacloud)
6. [AI-Assisted IDE](#6-ai-assisted-ide-zoyaide)
7. [Data Science](#7-data-science-zoyadata)
8. [Mobile Framework](#8-mobile-framework-zoyamobile)
9. [Security](#9-security-zoyasecurity)
10. [DevOps](#10-devops-zoyadevops)
11. [Marketplace](#11-marketplace-zoyamarketplace)
12. [Visual Builder](#12-visual-builder-zoyavisual)
13. [Cross-Platform Export](#13-cross-platform-export-zoyaexport)
14. [Enterprise](#14-enterprise-zoyaenterprise)
15. [Robotics SDK](#15-robotics-sdk-zoyarobotics)
16. [Zoya Language Syntax](#zoya-language-syntax)
17. [Test Suite](#test-suite)

</details>

---

## 1. Web Framework (`zoya.web`)

A lightweight HTTP router and middleware stack for building web APIs.

### Quick Start

```python
from zoya.web import create_app

app = create_app()

@app.get("/")
def home(req):
    return {"message": "Hello, World!"}

@app.get("/hello/{name}")
def greet(req):
    return {"greeting": f"Hello, {req.params['name']}!"}

app.run(port=8080)
```

### Custom Middleware

```python
from zoya.web import create_app
from zoya.web.middleware import LoggingMiddleware, AuthMiddleware, ErrorHandlingMiddleware

app = create_app()
app.use(LoggingMiddleware())
app.use(AuthMiddleware(api_key="secret"))
app.use(ErrorHandlingMiddleware())

@app.get("/secure/data")
def secure_data(req):
    return {"secret": 42}
```

### API Responses

```python
from zoya.web.response import create_success, create_error, ApiResponse

success = create_success(data={"user": "alice"}, meta={"total": 1})
error = create_error("Not found", code="NOT_FOUND", status=404)

isinstance(success, ApiResponse)  # True
```

### API Reference

| Function / Class | Description |
|-----------------|-------------|
| `create_app()` | Create a new Web application instance |
| `Router()` | URL router with path parameter support (`/users/{id}`) |
| `LoggingMiddleware()` | Logs all incoming requests |
| `AuthMiddleware(api_key)` | Validates `Authorization` header |
| `ErrorHandlingMiddleware()` | Catches and formats errors |
| `create_success(data, meta)` | Standardized success response |
| `create_error(message, code, status)` | Standardized error response |
| `ApiResponse` | Response envelope with `success`, `data`, `error`, `meta` |

---

## 2. Desktop Framework (`zoya.desktop`)

A widget-based desktop application framework.

### Quick Start

```python
from zoya.desktop import create_desktop_app

app = create_desktop_app("My App", width=800, height=600)

def on_click():
    print("Button clicked!")

app.add_widget("button", text="Click Me", callback=on_click)
app.run()
```

### Custom Widgets

```python
from zoya.desktop import create_desktop_app, Widget

app = create_desktop_app("Dashboard", 1024, 768)

class CustomWidget(Widget):
    def __init__(self, name):
        super().__init__(name)
    
    def render(self):
        return f"[CustomWidget: {self.name}]"

app.add_widget(CustomWidget("status_bar"))
app.run()
```

### API Reference

| Function / Class | Description |
|-----------------|-------------|
| `create_desktop_app(title, width, height)` | Create a desktop application window |
| `Window(title, width, height)` | Top-level window container |
| `Widget(name)` | Base class for all widgets |
| `window.add_widget(widget_or_type)` | Add a widget to the window |
| `window.run()` | Start the application event loop |

---

## 3. Scientific Computing (`zoya.stdlib.scientific`)

Pure-Python scientific computing with matrix operations, statistics, optimization, and machine learning.

### Linear Algebra

```python
from zoya.stdlib.scientific import Matrix, Vector, eye, zeros, ones, dot, solve

A = Matrix([[1, 2], [3, 4]])
b = Vector([5, 6])
x = solve(A, b)             # Solve Ax = b
print(x)                    # Vector([-4.0, 4.5])

I = eye(3)                  # 3x3 identity
det = A.det()               # Determinant: -2.0
inv = A.inv()               # Inverse
eigvals, eigvecs = A.eig()  # Eigen decomposition
u, s, vt = A.svd()          # SVD decomposition
```

### Statistics

```python
from zoya.stdlib.scientific import (
    mean, median, mode, std, variance,
    percentile, iqr, corr, pearson, zscore,
    t_test, chi_square, f_test,
    Distributions
)

data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
print(mean(data))           # 5.5
print(median(data))         # 5.5
print(std(data))            # 2.872
print(corr(data, [x*2 for x in data]))  # 1.0
print(pearson(data, [x*2 for x in data]))  # 1.0

# Probability distributions
norm = Distributions.normal(mean=0, std=1)
print(norm.pdf(0))          # 0.3989
print(norm.cdf(1.96))       # 0.975

# Hypothesis testing
stat, p = t_test([1,2,3], [4,5,6])
print(p)                    # p-value
```

### Optimization

```python
from zoya.stdlib.scientific import (
    gradient_descent, newton_method,
    simulated_annealing, genetic_algorithm,
    linear_programming, minimize_scalar
)

# Gradient descent
f = lambda x: (x[0]-3)**2 + (x[1]+1)**2
result = gradient_descent(f, [0.0, 0.0], step_size=0.1, max_iter=100)
print(result)               # ~[3.0, -1.0]

# Genetic algorithm
f = lambda x: -((x[0]-3)**2 + (x[1]+1)**2)  # maximize
result = genetic_algorithm(f, bounds=[(-10,10), (-10,10)], pop_size=50, generations=100)
print(result)

# Simulated annealing
f = lambda x: (x[0]-3)**2 + (x[1]+1)**2
result = simulated_annealing(f, [0.0, 0.0], bounds=[(-10,10), (-10,10)])
print(result)
```

### Machine Learning

```python
from zoya.stdlib.scientific import (
    LinearRegression, LogisticRegression, RidgeRegression, LassoRegression,
    KMeans, PCA,
    DecisionTree, RandomForest, SVM, GaussianNB,
    train_test_split, accuracy_score, mean_squared_error, confusion_matrix
)

# Regression
X = [[1.0], [2.0], [3.0], [4.0], [5.0]]
y = [2.1, 4.0, 5.9, 8.2, 10.1]
model = LinearRegression().fit(X, y)
print(model.predict([[6.0]]))  # ~12.0
print(model.coefficients)      # [~2.0]
print(model.intercept)         # ~0.1

# Classification
X = [[1], [2], [3], [10], [11], [12]]
y = [0, 0, 0, 1, 1, 1]
clf = LogisticRegression().fit(X, y)
print(clf.predict([[5], [15]]))

# Clustering
kmeans = KMeans(n_clusters=2).fit(X)
print(kmeans.labels)
print(kmeans.centroids)

# Random Forest
rf = RandomForest(n_trees=10, max_depth=5).fit(X, y)
print(rf.predict([[6]]))

# SVM
svm = SVM(kernel='rbf', C=1.0).fit(X, y)
print(svm.predict([[6]]))

# Dimensionality Reduction
pca = PCA(n_components=1).fit(X)
print(pca.transform(X))
```

### API Reference

| Module | Key Classes/Functions |
|--------|----------------------|
| `linear` | `Matrix`, `Vector`, `eye`, `zeros`, `ones`, `dot`, `cross`, `norm`, `solve`, `inv`, `det`, `eig`, `svd`, `qr`, `cholesky`, `lu` |
| `statistics` | `mean`, `median`, `mode`, `std`, `variance`, `percentile`, `iqr`, `corr`, `pearson`, `spearman`, `zscore`, `t_test`, `chi_square`, `f_test`, `Distributions` (normal, uniform, exponential, binomial, poisson) |
| `optimization` | `gradient_descent`, `newton_method`, `simulated_annealing`, `genetic_algorithm`, `linear_programming`, `minimize_scalar`, `particle_swarm` |
| `ml` | `LinearRegression`, `RidgeRegression`, `LassoRegression`, `LogisticRegression`, `KMeans`, `PCA`, `DecisionTree`, `RandomForest`, `SVM`, `GaussianNB`, `train_test_split`, `accuracy_score`, `mean_squared_error`, `confusion_matrix`, `StandardScaler` |

---

## 4. AI Platform (`zoya.ai`)

A complete AI platform with LLM providers, tools, memory, embeddings, agents, and RAG.

### LLM Providers

```python
from zoya.ai.llm import OpenAIProvider, AnthropicProvider, MockProvider

# Mock provider for testing (no API key needed)
llm = MockProvider()
print(llm.generate("Hello!"))
print(llm.chat([{"role": "user", "content": "Hi"}]))
print(llm.stream("Tell me a story"))  # Generator

# Real providers (require API keys)
# gpt = OpenAIProvider(api_key="sk-...", model="gpt-4")
# claude = AnthropicProvider(api_key="sk-ant-...", model="claude-3")
```

### Tools & Tool Registry

```python
from zoya.ai.tools import ToolRegistry, tool

registry = ToolRegistry()
registry.register("calculator", lambda a, b: a + b)
result = registry.execute("calculator", 3, 4)  # 7

# @tool decorator
@tool(name="search", description="Search the web")
def web_search(query: str) -> str:
    return f"Results for: {query}"

registry.register_tool(web_search)
```

Built-in tools: `CalculatorTool`, `WebSearchTool`, `FileReadWriteTool`, `PythonExecuteTool`, `ShellTool`.

### Memory

```python
from zoya.ai.memory import ConversationMemory, SemanticMemory, AgentMemory

# Conversation memory
conv = ConversationMemory(max_turns=10)
conv.add("user", "What is AI?")
conv.add("assistant", "AI is...")
print(conv.get_history())

# Semantic memory (TF-IDF based)
sem = SemanticMemory()
sem.store("key1", {"text": "Python is a programming language"})
results = sem.query("programming")  # Returns relevant entries

# Agent memory (persistent)
agent_mem = AgentMemory()
agent_mem.save("C:/agent_memory.json")  # Persist to disk
agent_mem.load("C:/agent_memory.json")  # Restore
```

### Embeddings

```python
from zoya.ai.embeddings import TFIDFVectorizer, cosine_similarity

vectorizer = TFIDFVectorizer()
documents = ["AI is the future", "Machine learning is AI"]
vectors = [vectorizer.fit_transform(doc) for doc in documents]

similarity = cosine_similarity(vectors[0], vectors[1])

emb = TextEmbedding(model="mock")  # Mock for testing
embeddings = emb.embed(["hello world"])
```

### Agents

```python
from zoya.ai import create_agent

# Basic ReAct agent
agent = create_agent(
    name="Assistant",
    llm=MockProvider(),
    tools=registry
)

response = agent.run("Calculate 5 + 3 and search for AI news")
print(response)

# Planning agent
from zoya.ai.agent import PlanningAgent
planner = PlanningAgent(llm=MockProvider())
result = planner.run("Build a web app")
```

### RAG (Retrieval-Augmented Generation)

```python
from zoya.ai.rag import DocumentChunker, RAGIndex, RAGRetriever

docs = [
    "Python is a high-level programming language.",
    "It was created by Guido van Rossum in 1991.",
    "Python emphasizes code readability."
]

chunker = DocumentChunker(chunk_size=50, overlap=10)
chunks = chunker.chunk(docs)  # Split docs into chunks

index = RAGIndex()
index.add_documents(chunks)

retriever = RAGRetriever(index, top_k=2)
results = retriever.retrieve("Who created Python?")
```

### API Reference

| Module | Key Classes/Functions |
|--------|----------------------|
| `llm` | `OpenAIProvider`, `AnthropicProvider`, `MockProvider`, `BaseLLM` |
| `tools` | `Tool`, `ToolRegistry`, `tool()` decorator, `CalculatorTool`, `WebSearchTool`, `FileReadWriteTool`, `PythonExecuteTool`, `ShellTool` |
| `memory` | `ConversationMemory`, `SemanticMemory`, `AgentMemory` |
| `embeddings` | `TFIDFVectorizer`, `TextEmbedding`, `cosine_similarity` |
| `agent` | `Agent` (ReAct loop), `PlanningAgent`, `create_agent()` |
| `rag` | `DocumentChunker`, `RAGIndex`, `RAGRetriever` |

---

## 5. Cloud Platform (`zoya.cloud`)

A full-featured cloud backend with auth, database, storage, realtime, leaderboards, multiplayer, and analytics.

### Authentication

```python
from zoya.cloud import create_cloud

cloud = create_cloud()

# User management
user = cloud.auth.register("alice@example.com", "securepass123")
session = cloud.auth.login("alice@example.com", "securepass123")
print(session.token)

# OAuth
oauth_url = cloud.auth.oauth_login("google", "http://localhost/callback")
token = cloud.auth.oauth_callback("google", {"code": "abc123"})

# Anonymous
anon = cloud.auth.anonymous()

# Session management
me = cloud.auth.get_user(session.token)
cloud.auth.logout(session.token)

# Password management
cloud.auth.reset_password_request("alice@example.com")
cloud.auth.reset_password("reset_token_123", "newpassword")
cloud.auth.change_password(session.token, "oldpass", "newpass")
```

### Database

```python
from zoya.cloud.database import DocumentDB

db = DocumentDB()

# CRUD operations
user = db.insert("users", {"name": "Alice", "email": "alice@example.com", "age": 30})
updated = db.update("users", user["id"], {"age": 31})
found = db.get("users", user["id"])
db.delete("users", user["id"])

# Query operators
results = db.query("users", {
    "age": {"$gte": 18, "$lt": 65},
    "name": {"$in": ["Alice", "Bob"]},
    "email": {"$regex": "@example.com"},
    "score": {"$exists": True}
})

# Transactions
with db.transaction():
    db.insert("accounts", {"owner": "Alice", "balance": 100})
    db.insert("accounts", {"owner": "Bob", "balance": 200})

# Schemas
db.create_schema("users", {
    "name": {"type": "string", "required": True},
    "age": {"type": "number", "min": 0, "max": 150}
})
```

Query operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, `$regex`, `$exists`.

### Storage

```python
# Buckets
bucket = cloud.storage.create_bucket("my-files")
buckets = cloud.storage.list_buckets()

# Upload/Download
url = cloud.storage.upload("my-files", "hello.txt", b"Hello, World!")
data = cloud.storage.download("my-files", "hello.txt")

# Signed URLs
signed = cloud.storage.get_signed_url("my-files", "hello.txt", expires_in=3600)
```

### Realtime

```python
# Pub/Sub
cloud.realtime.subscribe("chat:general", lambda msg: print(msg))
cloud.realtime.publish("chat:general", {"user": "Alice", "text": "Hello!"})

# Presence
cloud.realtime.track_presence("room:1", "user:alice")
users = cloud.realtime.get_presence("room:1")
cloud.realtime.untrack_presence("room:1", "user:alice")
```

### Leaderboard

```python
# Different update strategies
cloud.leaderboard.update_score("global", "alice", 100)       # default: replace
cloud.leaderboard.update_score("global", "alice", 50, "increment")  # add
cloud.leaderboard.update_score("global", "alice", 500, "max")       # keep highest
cloud.leaderboard.update_score("global", "bob", 75)

# Rankings
top = cloud.leaderboard.get_rankings("global", top_n=10)
alice_rank = cloud.leaderboard.get_rank("global", "alice")
alice_score = cloud.leaderboard.get_score("global", "alice")
```

### Multiplayer

```python
# Matchmaking
ticket = cloud.multiplayer.join_queue("ranked")
match = cloud.multiplayer.find_match("ranked")  # Returns when match found

# Lobbies
lobby = cloud.multiplayer.create_lobby("My Game", max_players=4)
cloud.multiplayer.join_lobby(lobby["id"])
players = cloud.multiplayer.lobby_players(lobby["id"])
cloud.multiplayer.ready_up(lobby["id"], "alice")
cloud.multiplayer.start_game(lobby["id"])

# Parties
party = cloud.multiplayer.create_party("alice")
cloud.multiplayer.invite_to_party(party["id"], "bob")
cloud.multiplayer.join_party(party["id"], "bob")

# State Sync
state = cloud.multiplayer.get_state("game:123")
cloud.multiplayer.update_state("game:123", {"players": {"alice": {"x": 10, "y": 20}}})
```

### Analytics

```python
# Event tracking
cloud.analytics.track("user_signup", {"source": "google"})
cloud.analytics.track("level_complete", {"level": 5, "score": 1000})

# Sessions
session_id = cloud.analytics.start_session("user:alice")
cloud.analytics.end_session(session_id)

# Queries
events = cloud.analytics.get_events("user_signup")
sessions = cloud.analytics.get_sessions(days=7)

# User retention
retention = cloud.analytics.get_retention("user:alice")
```

### API Reference

| Module | Key Classes/Functions |
|--------|----------------------|
| `auth` | `register`, `login`, `oauth_login`, `oauth_callback`, `anonymous`, `get_user`, `logout`, `reset_password`, `change_password` |
| `database` | `DocumentDB`, `insert`, `get`, `update`, `delete`, `query` (10 operators), `transaction`, `create_schema` |
| `storage` | `create_bucket`, `list_buckets`, `upload`, `download`, `get_signed_url` |
| `realtime` | `subscribe`, `publish`, `track_presence`, `get_presence`, `untrack_presence` |
| `leaderboard` | `update_score` (replace/increment/max/avg), `get_rankings`, `get_rank`, `get_score` |
| `multiplayer` | `join_queue`, `find_match`, `create_lobby`, `join_lobby`, `ready_up`, `start_game`, `create_party`, `invite_to_party`, `get_state`, `update_state` |
| `analytics` | `track`, `start_session`, `end_session`, `get_events`, `get_sessions`, `get_retention` |
| main | `ZoyaCloud`, `create_cloud()` |

---

## 6. AI-Assisted IDE (`zoya.ide`)

An AI-powered IDE assistant with code completion, generation, review, refactoring, debugging, and documentation.

### Code Completion

```python
from zoya.ide import create_ide_assistant

ide = create_ide_assistant()

# Keyword completions
completions = ide.complete("def ", "python")
# Returns: ["def function_name():", "def class_name():"]

# Scope-aware completions
completions = ide.complete("pri", "zoya", scope={"functions": ["print", "println"]})
# Returns: ["print", "println"]

# Dot completions
completions = ide.complete("math.sqr", "python")
# Returns: ["math.sqrt(", "math.sqr()"]

# Snippets
snippet = ide.get_snippet("for_loop")
# Returns: "for item in iterable:\n    pass"
```

Built-in snippets: `for_loop`, `while_loop`, `if_else`, `fn_def`, `class_def`, `import_stmt`, `try_catch`, `switch_case`, `list_comp`, `lambda_fn`, `decorator`, `context_manager`, `main_guard`, `list_append`, `dict_get`, `error_handler`.

### Code Generation

```python
# NL to Zoya code
code = ide.generate("create a function that calculates fibonacci numbers")
# Returns: "fn fibonacci(n) {\n    if n <= 1 { return n }\n    return fibonacci(n-1) + fibonacci(n-2)\n}"

# Code explanation
explanation = ide.explain("fn add(a, b) { return a + b }")

# Language translation
java_code = ide.translate("print 'hello'", "zoya", "python")
# Returns: "print('hello')"
```

### Code Review

```python
reviews = ide.review("""
    fn bad(a, b) {
        x = a + b
        print x
    }
""")
for r in reviews:
    print(f"[{r.severity}] {r.rule}: {r.message} (line {r.line})")
```

Built-in rules: `line-too-long`, `missing-docstring`, `unused-variable`, `inconsistent-naming`, `deep-nesting`, `magic-number`, `todo-comment`, `empty-except`, `shadow-builtin`, `duplicate-code`, `complex-function`, `missing-type-hint`.

### Refactoring

```python
# Rename
result = ide.refactor("rename", "print greet(name) { return 'Hi ' + name }",
                       old_name="greet", new_name="greet_user")

# Extract function
result = ide.refactor("extract-function", "x = a + b; print(x)", name="add_and_print")

# Inline variable
result = ide.refactor("inline-variable", "x = 5; print(x)")

# Convert loop
result = ide.refactor("convert-loop", "for i in range(10): print(i)", target="while")

# Format
result = ide.refactor("format", "fn  add(a,b){return a+b}")

# Remove dead code
result = ide.refactor("remove-dead-code", "x = 5\ny = 10\nprint(y)")
```

All 14 operations: `rename`, `extract-function`, `extract-variable`, `inline-variable`, `convert-loop`, `split-loop`, `merge-loops`, `convert-if-to-switch`, `convert-switch-to-if`, `reorder-params`, `encapsulate-field`, `format`, `remove-dead-code`, `simplify-expression`.

### Debugging

```python
# Find bugs
bugs = ide.debug("""
    fn divide(a, b) {
        return a / b
    }
    print divide(5, 0)
""")
for bug in bugs:
    print(f"[{bug.severity}] {bug.type}: {bug.message}")

# Automatic fix
fixes = ide.fix_bugs("""
    def calculate():
        x = 10
        return y
""")
```

Detectable bug patterns: `division-by-zero`, `infinite-loop`, `null-reference`, `type-error`, `off-by-one`, `uninitialized-var`, `dead-code`, `memory-leak`, `race-condition`, `redundant-assignment`.

### Documentation Generation

```python
# Generate docs
from zoya.ide.docs import DocGenerator

generator = DocGenerator()
docs = generator.generate_api_docs({"add": {"params": ["a", "b"], "returns": "a + b"}}, "markdown")

# README generation
readme = generator.generate_readme("My Project", description="A great project")

# CHANGELOG
changes = generator.generate_changelog([{"version": "1.0.0", "changes": ["Initial release"]}])
```

### API Reference

| Module | Key Classes/Functions |
|--------|----------------------|
| `completion` | `CodeCompleter`, `SnippetManager`, `complete()`, `get_snippet()` |
| `generation` | `CodeGenerator`, `generate()`, `explain()`, `translate()` |
| `review` | `Reviewer`, `review()` — 12 built-in rules |
| `refactor` | `RefactorEngine`, `refactor()` — 14 operations |
| `debug` | `DebugAssistant`, `debug()`, `fix_bugs()` — 10 bug patterns |
| `docs` | `DocGenerator`, `generate_api_docs()`, `generate_readme()`, `generate_changelog()` |
| main | `IDEAssistant`, `create_ide_assistant()` |

---

## 7. Data Science (`zoya.data`)

A Pandas-like DataFrame with Series, GroupBy, and ASCII visualization.

### DataFrame

```python
from zoya.data import DataFrame, create_dataframe

df = DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "salary": [50000, 60000, 70000]
})

# Inspection
print(df.shape)             # (3, 3)
print(df.columns)           # ["name", "age", "salary"]
print(df.dtypes)            # {col: type}
print(df.head(2))
print(df.describe())

# Selection
print(df["name"])           # Column
print(df[["name", "age"]])  # Multiple columns
print(df.iloc[0])           # Row by index
print(df.iloc[1:3])         # Row slice

# Filtering
adults = df[df["age"] >= 30]
filtered = df.query("age > 25 and salary > 55000")

# Operations
df["bonus"] = df["salary"] * 0.1         # New column
df = df.rename({"salary": "compensation"})
df = df.drop(columns=["bonus"])

# Aggregation
avg_age = df["age"].mean()
total = df["salary"].sum()
stats = df.agg({"age": ["mean", "std"], "salary": ["sum", "min", "max"]})

# GroupBy
by_name = df.groupby("name")
for name, group in by_name:
    print(name, group)

# Merge
df1 = DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
df2 = DataFrame({"id": [1, 2], "score": [95, 87]})
merged = df1.merge(df2, on="id", how="inner")

# I/O
df.to_csv("data.csv")
df.to_json("data.json")
loaded = create_dataframe("data.csv")
```

### Series

```python
from zoya.data import Series

s = Series([1, 2, 3, 4, 5], index=["a", "b", "c", "d", "e"])
print(s["a"])                # 1
print(s.mean())              # 3.0
print(s.std())               # 1.581
print(s.min(), s.max())      # 1, 5
print(s.sum())               # 15

s2 = s.apply(lambda x: x * 2)
```

### ASCII Visualization

```python
from zoya.data import Plot

# Line chart
Plot.line([1, 2, 3, 4, 5], [2, 4, 6, 8, 10], title="Linear Growth")

# Bar chart
Plot.bar(["A", "B", "C", "D"], [3, 7, 2, 5], title="Categories")

# Histogram
Plot.histogram([1, 2, 2, 3, 3, 3, 4, 4, 5], bins=5)

# Scatter plot
Plot.scatter([1, 2, 3, 4], [2, 4, 6, 8])

# Pie chart
Plot.pie(["Apples", "Oranges", "Bananas"], [30, 50, 20])
```

### API Reference

| Component | Key Features |
|-----------|-------------|
| `DataFrame` | CRUD, filter, query, groupby, merge, sort, rename, drop, agg, head, describe, dtypes, shape, I/O (CSV, JSON, HTML) |
| `Series` | Vectorized ops, mean/std/min/max/sum, apply, map, iloc |
| `GroupBy` | Iteration, aggregation |
| `Plot` | `line`, `bar`, `histogram`, `scatter`, `pie` (all ASCII) |

---

## 8. Mobile Framework (`zoya.mobile`)

Build mobile UIs with 15 built-in widgets, navigation, and gesture detection.

### Quick Start

```python
from zoya.mobile import App, Screen, Button, Label, TextField, Navigator

class HomeScreen(Screen):
    def __init__(self):
        super().__init__("home")
        self.count = 0
    
    def init(self):
        self.label = Label("Count: 0")
        btn = Button("Increment", on_click=self.increment)
        self.add_widget(self.label)
        self.add_widget(btn)
    
    def increment(self):
        self.count += 1
        self.label.text = f"Count: {self.count}"

app = App("MyApp", HomeScreen(), version="1.0.0")
app.run()
```

### Navigation

```python
from zoya.mobile import Navigator

nav = Navigator()
nav.push("settings")
nav.push("profile")
print(nav.current)  # "profile"
print(nav.size)     # 3
nav.pop()           # back to "settings"
nav.replace("home") # replaces current
```

### Gestures

```python
from zoya.mobile import GestureDetector, TapGesture, SwipeGesture, PinchGesture

detector = GestureDetector()

# Tap
tap = TapGesture(on_tap=lambda: print("Tapped!"))
detector.add_recognizer(tap)

# Swipe
swipe = SwipeGesture(direction="right", on_swipe=lambda: print("Swiped right!"))
detector.add_recognizer(swipe)

# Pinch
pinch = PinchGesture(on_pinch=lambda scale: print(f"Pinched: {scale}"))
detector.add_recognizer(pinch)

# Pan
from zoya.mobile import PanGesture
pan = PanGesture(on_pan=lambda dx, dy: print(f"Moved: {dx}, {dy}"))
```

### Native Bridge

```python
from zoya.mobile import NativeBridge

bridge = NativeBridge(platform="android")

# Permissions
bridge.request_permission("camera")
bridge.request_permission("location")

# Share
bridge.share_text("Check this out!")

# Device
bridge.open_url("https://example.com")
bridge.save_to_gallery("/tmp/photo.jpg")

# iOS specific
ios_bridge = NativeBridge(platform="ios")
ios_bridge.pick_file()
```

### All Widgets

```python
from zoya.mobile import (
    Label, Button, TextField, Image,
    ListView, ScrollView,
    Column, Row,
    Card, Switch, Slider,
    ProgressBar, Spinner,
    Toast, Modal
)

# Layout
Column([
    Label("Title"),
    Button("Click", on_click=lambda: None),
    TextField(placeholder="Enter text")
])

Row([
    Card("Card 1", "Description"),
    Card("Card 2", "Description")
])

ScrollView(children=[Label(f"Item {i}") for i in range(100)])
ListView(items=["A", "B", "C"], on_select=lambda item: print(item))

Switch(initial=True, on_toggle=lambda v: print(v))
Slider(min=0, max=100, initial=50, on_change=lambda v: print(v))
ProgressBar(value=0.75)
Spinner()
Toast("Saved!", duration=2)
Modal(title="Confirm", content="Are you sure?")
```

### Widget Lifecycle

```python
class MyScreen(Screen):
    def init(self):          # Called once when created
        pass
    
    def on_load(self):       # Called when screen becomes active
        pass
    
    def on_unload(self):     # Called when navigating away
        pass
    
    def on_destroy(self):    # Called when screen is removed
        pass
```

### API Reference

| Component | Description |
|-----------|-------------|
| `App(title, root_screen, version)` | Mobile application entry point |
| `Screen(name)` | Base screen with lifecycle hooks |
| `Navigator()` | push/pop/replace navigation stack |
| `GestureDetector()` | Tap, DoubleTap, LongPress, Swipe, Pinch, Pan recognizers |
| `NativeBridge(platform)` | iOS/Android native API calls |
| Widgets | Label, Button, TextField, Image, ListView, ScrollView, Column, Row, Card, Switch, Slider, ProgressBar, Spinner, Toast, Modal |

---

## 9. Security (`zoya.security`)

Encryption, hashing, key generation, input validation, and sanitization.

### Encryption

```python
from zoya.security import AESCipher

cipher = AESCipher(key="my-secret-key-123")
encrypted = cipher.encrypt("Hello, World!")
decrypted = cipher.decrypt(encrypted)
print(decrypted)  # "Hello, World!"
```

### Hashing

```python
from zoya.security import Hasher

# SHA-256
hash = Hasher.sha256("hello")
print(hash)  # hex digest

# SHA-512
hash = Hasher.sha512("hello")

# HMAC
hmac = Hasher.hmac("message", "key", "sha256")

# PBKDF2
key = Hasher.pbkdf2("password", "salt", iterations=100000)

# bcrypt-style
hashed = Hasher.bcrypt("password")
verified = Hasher.bcrypt_verify("password", hashed)
```

### Key Generation

```python
from zoya.security import KeyGenerator

# API keys
api_key = KeyGenerator.api_key()       # e.g., "zoya_a1b2c3d4e5f6..."
api_key = KeyGenerator.api_key(prefix="prod", length=48)

# OTP
otp = KeyGenerator.otp(length=6)       # "483921"

# UUID
uuid = KeyGenerator.uuid()             # "550e8400-e29b-41d4-..."
```

### Validation

```python
from zoya.security import Validator, ValidationError

# Email
Validator.email("user@example.com")    # True
Validator.email("invalid")             # raises ValidationError

# URLs
Validator.url("https://example.com")   # True

# IP addresses
Validator.ip("192.168.1.1")            # True (v4)
Validator.ip("::1")                    # True (v6)

# Credit card
Validator.credit_card("4111111111111111")  # True (Luhn check)

# Password strength
Validator.password_strength("Weak1")             # raises (too short)
Validator.password_strength("Str0ng!Pass")        # True
Validator.password_strength("abc", min_length=3, require_upper=False, require_digits=False)  # True

# Security detection
Validator.detect_sqli("' OR 1=1 --")    # True (detected)
Validator.detect_xss("<script>alert(1)</script>")  # True
Validator.detect_path_traversal("../../../etc/passwd")  # True
```

### Sanitization

```python
from zoya.security import Sanitizer

# HTML
clean = Sanitizer.html("<script>alert('xss')</script><p>Hello</p>")
# Returns: "&lt;script&gt;...&lt;/p&gt;"

# Shell
safe = Sanitizer.shell_arg("file; rm -rf /")
# Returns: "'file; rm -rf /'"

# SQL
safe = Sanitizer.sql_string("O'Brien")
# Returns: "O''Brien"

# Filename
safe = Sanitizer.filename("../../etc/passwd")
# Returns: "etc_passwd"
```

### API Reference

| Component | Features |
|-----------|----------|
| `AESCipher(key)` | `encrypt()`, `decrypt()` — XOR + SHA-256 stream cipher |
| `Hasher` | `sha256()`, `sha512()`, `md5()`, `hmac()`, `pbkdf2()`, `bcrypt()`, `bcrypt_verify()` |
| `KeyGenerator` | `api_key()`, `otp()`, `uuid()` |
| `Validator` | `email()`, `url()`, `ip()`, `credit_card()`, `password_strength()`, `detect_sqli()`, `detect_xss()`, `detect_path_traversal()` |
| `Sanitizer` | `html()`, `shell_arg()`, `sql_string()`, `filename()` |

---

## 10. DevOps (`zoya.devops`)

CI/CD pipelines and deployment strategies.

### CI/CD Pipelines

```python
from zoya.devops import PipelineRunner

def build():
    print("Building...")
    return True

def test():
    print("Testing...")
    return True

def deploy():
    print("Deploying...")
    return True

# Sequential pipeline
pipeline = PipelineRunner()
pipeline.add_stage("build", build)
pipeline.add_stage("test", test, depends_on=["build"])
pipeline.add_stage("deploy", deploy, depends_on=["test"])
pipeline.run()  # Executes build → test → deploy

# Parallel stages
pipeline2 = PipelineRunner()
pipeline2.add_stage("lint", lambda: print("Lint"))
pipeline2.add_stage("test", lambda: print("Test"))
pipeline2.add_stage("package", lambda: print("Package"), depends_on=["lint", "test"])
pipeline2.run()  # lint + test in parallel → package
```

### Deployment Strategies

```python
from zoya.devops import Deployer

# Rolling update
deployer = Deployer(strategy="rolling")
deployer.deploy(
    deploy_func=lambda: print("Deploying..."),
    health_check=lambda: True,
    instances=3
)

# Blue-green
deployer = Deployer(strategy="blue-green")
deployer.deploy(deploy_func=lambda: None, health_check=lambda: True)

# Canary
deployer = Deployer(strategy="canary", canary_percent=10)
deployer.deploy(deploy_func=lambda: None, health_check=lambda: True)

# Recreate
deployer = Deployer(strategy="recreate")

# Rollback
deployer.rollback(version="1.0.0")
```

### API Reference

| Component | Features |
|-----------|----------|
| `PipelineRunner()` | `add_stage()`, `run()` — sequential/parallel execution |
| `Deployer(strategy)` | `deploy()`, `rollback()` — rolling, blue-green, canary, recreate |
| Stages | Named pipeline steps with dependency graph |
| Health checks | Callback-based verification before/after deployment |

---

## 11. Marketplace (`zoya.marketplace`)

Package registry and dependency resolution with semver support.

### Package Registry

```python
from zoya.marketplace import MarketplaceRegistry

registry = MarketplaceRegistry()

# Register package
registry.register("my-package", "1.0.0", author="Alice")

# Search
results = registry.search("my-pack")
results = registry.search_by_author("Alice")

# Install
pkg = registry.install("my-package", version=">=1.0.0")

# Update
registry.update("my-package", "1.1.0")

# Deprecate
registry.deprecate("my-package", "1.0.0", reason="Security fix available")
```

### Dependency Resolution

```python
from zoya.marketplace import DependencyResolver

resolver = DependencyResolver()
resolver.add_package("app", "1.0.0", deps={"flask": ">=2.0"})
resolver.add_package("flask", "2.1.0")
resolver.add_package("flask", "2.0.0")

# Resolve dependencies
resolved = resolver.resolve("app", "1.0.0")
# Returns: {"flask": "2.1.0"}

# Semver validation
from zoya.marketplace.utils import satisfies
print(satisfies("2.1.0", ">=2.0.0"))   # True
print(satisfies("1.9.0", ">=2.0.0"))   # False
```

### API Reference

| Component | Features |
|-----------|----------|
| `MarketplaceRegistry()` | `register()`, `search()`, `search_by_author()`, `install()`, `update()`, `deprecate()` |
| `DependencyResolver()` | `add_package()`, `resolve()` |
| `utils.satisfies(version, constraint)` | Semver constraint checking |

---

## 12. Visual Builder (`zoya.visual`)

Build UIs from JSON specs — generates Zoya code with preview.

### Quick Start

```python
from zoya.visual import create_builder
from zoya.visual.components import ComponentLibrary

# JSON spec → Zoya code
spec = {
    "type": "screen",
    "children": [
        {"type": "label", "props": {"text": "Hello, World!"}},
        {"type": "button", "props": {"text": "Click Me"}}
    ]
}

builder = create_builder(spec)
code = builder.generate()
print(code)
# fn main() {
#     print("Hello, World!")
#     input("Click Me")
# }

# ASCII preview
preview = builder.preview()
print(preview)
```

### Component Library

```python
library = ComponentLibrary()
print(library.list_components())
# ["label", "button", "textfield", "image", "list", "card",
#  "column", "row", "switch", "slider", "progress", "spacer"]

defs = library.get_component("button")
print(defs.props)  # {"text": "string", "on_click": "callback"}
```

### Layout Engine

```python
from zoya.visual.layout import LayoutEngine

engine = LayoutEngine()
layout = engine.create_layout(spec, mode="column")  # or "row", "grid"
rendered = engine.render(layout)
```

### Themes

```python
from zoya.visual.theme import Theme

theme = Theme(
    primary_color="#4A90D9",
    secondary_color="#F5F5F5",
    font_size=14,
    spacing=8
)
styled_spec = theme.apply(spec)
```

### API Reference

| Component | Features |
|-----------|----------|
| `VisualBuilder(spec)` | `generate()` → Zoya code, `preview()` → ASCII |
| `ComponentLibrary()` | `list_components()`, `get_component()` — 12 types |
| `LayoutEngine()` | `create_layout()`, `render()` |
| `Theme(...)` | `apply(spec)` — color, font, spacing theming |

---

## 13. Cross-Platform Export (`zoya.export`)

Export projects to web, desktop, mobile, CLI, library, and Docker targets.

### Web Export

```python
from zoya.export import create_exporter

exporter = create_exporter(target="web")
project = exporter.export(
    name="my-app",
    files={"main.zoya": "print 'Hello'"}
)
# Generates: index.html, main.zoya, style.css
```

### Desktop Export

```python
exporter = create_exporter(target="desktop")
project = exporter.export(name="MyApp", files={"main.py": "..."})
# Generates: main.py, requirements.txt, setup.py
```

### Mobile Export

```python
exporter = create_exporter(target="mobile")
project = exporter.export(name="MyApp", files={"app.py": "..."})
# Generates: app.py, build.gradle (Android), Info.plist (iOS)
```

### CLI Export

```python
exporter = create_exporter(target="cli")
project = exporter.export(name="mycli", files={"cli.py": "..."})
# Generates: cli.py, setup.py (entry point)
```

### Library Export

```python
exporter = create_exporter(target="library")
project = exporter.export(name="mylib", files={"lib.py": "..."})
# Generates: lib.py, setup.py, __init__.py
```

### Docker Export

```python
exporter = create_exporter(target="docker")
project = exporter.export(
    name="my-app",
    files={"app.py": "..."},
    docker_options={
        "base_image": "python:3.11-slim",
        "port": 8080,
        "entrypoint": "python app.py"
    }
)
# Generates: Dockerfile, .dockerignore, app.py
```

### API Reference

| Target | Generated Files |
|--------|----------------|
| `web` | `index.html`, `style.css`, `script.js` |
| `desktop` | `main.py`, `requirements.txt`, `setup.py` |
| `mobile` | `app.py`, `build.gradle`, `Info.plist` |
| `cli` | `cli.py`, `setup.py` with console_scripts |
| `library` | `__init__.py`, `setup.py` |
| `docker` | `Dockerfile`, `.dockerignore` |

---

## 14. Enterprise (`zoya.enterprise`)

Enterprise features: RBAC, audit logging, feature flags, SSO, and multi-tenant management.

### Role-Based Access Control

```python
from zoya.enterprise import RBACManager

rbac = RBACManager()

# Define roles and permissions
rbac.create_role("admin", permissions=["read", "write", "delete", "manage"])
rbac.create_role("editor", permissions=["read", "write"])
rbac.create_role("viewer", permissions=["read"])

# Assign roles
rbac.assign_role("user:alice", "admin")
rbac.assign_role("user:bob", "viewer")

# Check permissions
print(rbac.check_permission("user:alice", "delete"))  # True
print(rbac.check_permission("user:bob", "write"))      # False

# Revoke
rbac.revoke_role("user:bob", "viewer")
```

### Audit Logging

```python
from zoya.enterprise import AuditLogger

logger = AuditLogger()

logger.log(
    action="user.login",
    actor="user:alice",
    resource="session",
    details={"ip": "192.168.1.1"}
)

logs = logger.query(user="user:alice", action="user.login")
print(logs[0].timestamp)
print(logs[0].actor)
```

### Feature Flags

```python
from zoya.enterprise import FeatureFlags

flags = FeatureFlags()

flags.add_flag("dark-mode", enabled=True)
flags.add_flag("new-dashboard", enabled=False, rollout_percent=25)
flags.add_flag("beta-feature", enabled=True, user_segments=["premium"])

print(flags.is_enabled("dark-mode"))                # True
print(flags.is_enabled("beta-feature", user="user:premium:alice"))  # True
```

### SSO

```python
from zoya.enterprise import SSOManager

sso = SSOManager()

# SAML
saml_url = sso.get_saml_login_url("https://myapp.com/acs")
saml_user = sso.handle_saml_response("..."  # SAML response XML

# OIDC
oidc_url = sso.get_oidc_login_url("google", "https://myapp.com/callback")
token = sso.handle_oidc_callback("google", {"code": "..."})
user_info = sso.get_oidc_user_info("google", token)
```

### Tenant Management

```python
from zoya.enterprise import TenantManager

tm = TenantManager()

# Create tenant
tenant = tm.create_tenant("acme-corp", "Acme Corporation")
tenant = tm.create_tenant("megacorp", plan="enterprise", max_users=1000)

# Membership
tm.add_user(tenant["id"], "user:alice", role="admin")
users = tm.get_users(tenant["id"])

# Isolation
ctx = tm.get_tenant_context(tenant["id"])
# Returns isolated config for this tenant
```

### API Reference

| Component | Features |
|-----------|----------|
| `RBACManager()` | `create_role()`, `assign_role()`, `revoke_role()`, `check_permission()` |
| `AuditLogger()` | `log()`, `query()` — filter by user, action, resource, time |
| `FeatureFlags()` | `add_flag()`, `is_enabled()` — with rollout % and user segments |
| `SSOManager()` | `get_saml_login_url()`, `handle_saml_response()`, `get_oidc_login_url()`, `handle_oidc_callback()`, `get_oidc_user_info()` |
| `TenantManager()` | `create_tenant()`, `add_user()`, `get_users()`, `get_tenant_context()` |

---

## 15. Robotics SDK (`zoya.robotics`)

Robot and drone control, sensors, servo motors, and simulation.

### Robot Controller

```python
from zoya.robotics import RobotController, Motor

robot = RobotController("Rover-1")

# Movement
robot.move_forward(speed=0.8)
robot.move_backward(speed=0.5)
robot.turn_left(degrees=45)
robot.turn_right(degrees=90)
robot.stop()

# Motor control
robot.set_motor_speed("left", 0.9)
robot.set_motor_speed("right", 0.7)
```

### Drone Controller

```python
from zoya.robotics import DroneController

drone = DroneController("Quad-1")

drone.arm()
drone.takeoff(altitude=10)

drone.move_forward(5)     # 5 meters
drone.move_right(3)
drone.move_up(2)

drone.rotate(yaw=90)      # rotate 90 degrees
drone.set_altitude(20)

drone.land()
drone.disarm()
```

### Sensors

```python
from zoya.robotics import (
    UltrasonicSensor, IRSensor, Camera,
    LidarSensor, GPSModule, IMUSensor
)

# Ultrasonic
us = UltrasonicSensor(pin=7)
distance = us.read()  # cm

# IR
ir = IRSensor(pin=8)
detected = ir.detect_obstacle()

# Camera
cam = Camera()
frame = cam.capture()
cam.process_image(frame, "grayscale")

# Lidar
lidar = LidarSensor()
scan = lidar.scan()  # 360° point cloud

# GPS
gps = GPSModule()
lat, lon = gps.read()
altitude = gps.get_altitude()

# IMU
imu = IMUSensor()
accel = imu.read_acceleration()
gyro = imu.read_gyroscope()
heading = imu.read_compass()
```

### Servo

```python
from zoya.robotics import Servo

servo = Servo(pin=9)
servo.set_angle(90)
servo.set_angle(180)
current = servo.get_angle()
```

### Simulation

```python
from zoya.robotics import SimulationEnvironment

sim = SimulationEnvironment(dimensions=(100, 100, 50))

robot = RobotController("TestBot")
sim.add_robot(robot, position=(10, 10, 0))

# Add obstacles
sim.add_obstacle(position=(50, 50, 0), size=(5, 5, 10))

# Step simulation
sim.step()
position = robot.get_position()
```

### API Reference

| Component | Features |
|-----------|----------|
| `RobotController(name)` | `move_forward()`, `move_backward()`, `turn_left()`, `turn_right()`, `stop()`, `set_motor_speed()`, `get_position()` |
| `DroneController(name)` | `arm()`, `disarm()`, `takeoff()`, `land()`, `move_forward()`, `move_backward()`, `move_left()`, `move_right()`, `move_up()`, `move_down()`, `rotate()`, `set_altitude()` |
| `UltrasonicSensor(pin)` | `read()` — distance in cm |
| `IRSensor(pin)` | `detect_obstacle()` |
| `Camera()` | `capture()`, `process_image()` |
| `LidarSensor()` | `scan()` — 360° point cloud |
| `GPSModule()` | `read()`, `get_altitude()` |
| `IMUSensor()` | `read_acceleration()`, `read_gyroscope()`, `read_compass()` |
| `Servo(pin)` | `set_angle()`, `get_angle()` |
| `SimulationEnvironment(dim)` | `add_robot()`, `add_obstacle()`, `step()` |

---

## Zoya Language Syntax

### Hello World

```zoya
print "Hello, World!"
```

### Variables & Math

```zoya
name = "Zoya"
version = 4.0
result = (10 + 5) * 2 / 3
```

### Conditionals

```zoya
if score >= 100 {
    print "You win!"
} else if score >= 50 {
    print "Almost there!"
} else {
    print "Keep trying!"
}
```

### Loops

```zoya
x = 0
while x < 10 {
    print x
    x = x + 1
}

loop 5 {
    print "Hello"
}

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

fn add(a, b) {
    return a + b
}
```

### Lists & Dictionaries

```zoya
nums = [1, 2, 3, 4, 5]
nums.append(6)
print nums[0]
print nums.length()
nums.sort()

person = {"name": "Alice", "age": 30}
print person["name"]
```

### String Interpolation

```zoya
name = "Zoya"
print f"Hello, {name}! Version 4.0"
```

### Import SDK Modules

```zoya
import "math" as math
print math.sqrt(16)

import "ai" as ai
bot = ai.model("gemini")
response = bot.ask("Hello!")
```

---

## Test Suite

```bash
# All 1,512 tests passing
python test_web_framework.py           # 8 tests
python test_desktop_framework.py        # 3 tests
python test_scientific.py               # 187 tests
python test_ai_platform.py              # 148 tests
python test_cloud_platform.py           # 246 tests
python test_ide_platform.py             # 199 tests
python test_data_science.py             # 169 tests
python test_mobile_framework.py         # 129 tests
python test_security_module.py          # 98 tests
python test_devops_module.py            # 43 tests
python test_marketplace_visual_export.py   # 141 tests
python test_enterprise_robotics.py      # 141 tests
```

## Project Structure

```
zoya/
├── __init__.py          # Core interpreter entry
├── ast.py               # AST node definitions
├── lexer.py             # Lexer / tokenizer
├── parser.py            # Parser
├── interpreter.py       # Tree-walk interpreter
├── builtins.py          # Built-in functions
├── environment.py       # Variable scoping
├── errors.py            # Error types
├── repl.py              # Interactive REPL
├── cli.py               # CLI entry point
├── stdlib/              # Language stdlib (20+ modules)
├── ai/                  # AI Platform (LLM, agents, RAG, tools, memory, embeddings)
├── cloud/               # Cloud Platform (auth, DB, storage, realtime, multiplayer, analytics)
├── ide/                 # AI-Assisted IDE (completion, review, refactor, debug, docs)
├── data/                # Data Science (DataFrame, Series, visualization)
├── mobile/              # Mobile Framework (widgets, navigation, gestures)
├── security/            # Security (encryption, hashing, validation, sanitization)
├── devops/              # DevOps (CI/CD pipelines, deployment strategies)
├── marketplace/         # Package Marketplace (registry, dependency resolution)
├── visual/              # Visual Builder (JSON-to-UI, layout engine, themes)
├── export/              # Cross-Platform Export (web, desktop, mobile, CLI, Docker)
├── enterprise/          # Enterprise (RBAC, audit, feature flags, SSO, multi-tenant)
├── robotics/            # Robotics SDK (robot, drone, sensors, servos, simulation)
├── web/                 # Web Framework (HTTP router, middleware, responses)
└── desktop/             # Desktop Framework (widget-based GUI applications)

```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

- 🐛 [Report a bug](https://github.com/notebookworrk-cyber/zoya-easy-code/issues/new)
- 💡 [Request a feature](https://github.com/notebookworrk-cyber/zoya-easy-code/discussions)
- ⭐ [Star the repo](https://github.com/notebookworrk-cyber/zoya-easy-code) if you find it useful!

### 📚 Resources

- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Discussions](https://github.com/notebookworrk-cyber/zoya-easy-code/discussions)

---

<div align="center">

**Built with ❤️ by [Lucky](https://github.com/notebookworrk-cyber)**

[![GitHub followers](https://img.shields.io/github/followers/notebookworrk-cyber?style=social)](https://github.com/notebookworrk-cyber)
[![GitHub stars](https://img.shields.io/github/stars/notebookworrk-cyber/zoya-easy-code?style=social)](https://github.com/notebookworrk-cyber/zoya-easy-code)

⭐ If Zoya helps you learn or build something, consider giving it a star!

</div>
