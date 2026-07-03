# Zoya — Software Development Platform v4.0

**Zoya** is a complete software development platform: a beginner-friendly programming language **and** a pure-Python SDK with 15+ module areas for building web, desktop, mobile, AI, cloud, and enterprise applications — with zero external dependencies.

## Quick Start

### Zoya Language (Zoya 3.0 — Core Interpreter)

```bash
git clone https://github.com/notebookworrk-cyber/zoya-easy-code.git
cd zoya-easy-code
pip install -e .
```

```bash
zoya hello.zoya    # Run a script
zoya --repl        # Interactive REPL
```

### Zoya Python SDK (Zoya 4.0 — Platform Modules)

```python
from zoya.web import create_app
from zoya.ai import create_agent
from zoya.cloud import create_cloud
from zoya.data import DataFrame
from zoya.security import Validator, Hasher
```

All modules are **pure Python** — no `numpy`, `pandas`, `openai`, `flask`, or any third-party packages required.

## Zoya SDK Modules — 1,512 tests, 0 failures

| Module | Description | Key Features |
|--------|-------------|--------------|
| `zoya.web` | Web Framework | Router (path params), Middleware chain (Logging/Auth/Error), API responses, `create_app()` |
| `zoya.desktop` | Desktop Framework | Window manager, Widget base, Button/TextBox, event callbacks |
| `zoya.stdlib.scientific` | Scientific Computing | Matrix ops, Linear Algebra, Statistics, Optimization (gradient descent, genetic algos), ML (LinearRegression, KMeans, RandomForest, SVM, NaiveBayes, PCA) |
| `zoya.ai` | AI Platform | LLM providers (OpenAI/Anthropic/Mock), ReAct Agent, Tools (calc, web search, file I/O, shell), Memory (conversation, semantic TF-IDF), Embeddings, RAG |
| `zoya.cloud` | Cloud Platform | Auth (register/login/OAuth/SAML), Document DB (10 query operators, transactions, schemas), Storage (buckets, signed URLs), Realtime (pub/sub, presence), Leaderboard, Multiplayer (matchmaking, lobbies, state sync), Analytics (events, retention, funnels) |
| `zoya.ide` | AI-Assisted IDE | Code completion (keywords, dot, scope), NL→Zoya code generation, Code review (12 rules), Refactoring (14 operations), Debug assistant, Documentation generator |
| `zoya.data` | Data Science | DataFrame (Pandas-like: CRUD, filter, groupby, merge, describe), Series, GroupBy, ASCII Plot (line/bar/histogram/scatter/pie) |
| `zoya.mobile` | Mobile Framework | 15 widgets (Label, Button, TextField, Image, ListView, ScrollView, Column, Row, Card, Switch, Slider, ProgressBar, Spinner, Toast, Modal), Navigator (push/pop/replace), GestureDetector (tap, double-tap, long-press, swipe, pinch, pan), NativeBridge (iOS/Android) |
| `zoya.security` | Security | AESCipher (XOR+SHA-256), Hasher (SHA-256/512, HMAC, PBKDF2, bcrypt), KeyGenerator, Validator (email, URL, IP, credit card, password strength, SQLi/XSS/path traversal detection), Sanitizer (HTML, shell, SQL escaping) |
| `zoya.devops` | DevOps | CI/CD PipelineRunner (sequential/parallel stages), Deployer (rolling, blue-green, canary, recreate strategies, health checks, rollback) |
| `zoya.marketplace` | Marketplace | Package registry, search, version management, dependency resolver (semver, constraint satisfaction) |
| `zoya.visual` | Visual Builder | JSON spec → Zoya code generation, ComponentLibrary (12 types), LayoutEngine, Theme engine, ASCII preview |
| `zoya.export` | Cross-Platform Export | 6 targets: web, desktop, mobile, CLI, library, Docker — generates project structures and Dockerfiles |
| `zoya.enterprise` | Enterprise | RBAC (roles/permissions), AuditLogger, FeatureFlags, SSOManager (SAML/OIDC), TenantManager (multi-tenant isolation) |
| `zoya.robotics` | Robotics SDK | Robot/Drone controllers, 6 sensor types (Ultrasonic, IR, Camera, Lidar, GPS, IMU), Servo, SimulationEnvironment |

## Language Syntax (Zoya 3.0)

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

### Conditionals & Loops

```zoya
if score >= 100 {
    print "You win!"
} else {
    print "Keep trying!"
}

loop 5 {
    print "Hello"
}
```

### Functions

```zoya
fn greet(name) {
    return "Hello, " + name
}
```

### Import SDK Modules from Zoya Language

```zoya
import "ai" as ai
bot = ai.model("gemini")
response = bot.ask("Hello!")
```

## CLI Usage

```
zoya script.zoya      # Run script
zoya --repl            # Interactive REPL
zoya --version         # Show version
zoya --help            # Show help
zoya -c "print 1+1"    # One-liner
```

## Project Structure

```
zoya/
├── __init__.py          # Core interpreter
├── ast.py               # AST nodes
├── lexer.py             # Lexer/tokenizer
├── parser.py            # Parser
├── interpreter.py       # Tree-walk interpreter
├── builtins.py          # Built-in functions
├── environment.py       # Variable scoping
├── errors.py            # Error types
├── repl.py              # Interactive REPL
├── cli.py               # CLI entry point
├── stdlib/              # Standard library modules
│   └── scientific/      # Scientific computing
├── ai/                  # AI Platform
├── cloud/               # Cloud Platform
├── ide/                 # AI-Assisted IDE
├── data/                # Data Science
├── mobile/              # Mobile Framework
├── security/            # Security
├── devops/              # DevOps
├── marketplace/         # Package Marketplace
├── visual/              # Visual Builder
├── export/              # Cross-Platform Export
├── enterprise/          # Enterprise
├── robotics/            # Robotics SDK
├── web/                 # Web Framework
└── desktop/             # Desktop Framework
```

## Test Suite

```bash
python test_web_framework.py        # 8 tests
python test_desktop_framework.py     # 3 tests
python test_scientific.py            # 187 tests
python test_ai_platform.py           # 148 tests
python test_cloud_platform.py        # 246 tests
python test_ide_platform.py          # 199 tests
python test_data_science.py          # 169 tests
python test_mobile_framework.py      # 129 tests
python test_security_module.py       # 98 tests
python test_devops_module.py         # 43 tests
python test_marketplace_visual_export.py  # 141 tests
python test_enterprise_robotics.py   # 141 tests
```

**Total: 1,512 tests — all passing, zero external dependencies.**

## License

MIT
