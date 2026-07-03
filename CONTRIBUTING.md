# Contributing to Zoya

First off, thank you for considering contributing to Zoya! We welcome contributions from everyone.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
- Check the [issues](https://github.com/notebookworrk-cyber/zoya-easy-code/issues) to see if it's already reported
- Use the bug report template when creating an issue

### Suggesting Features

Feature requests are welcome! Use the feature request template and clearly describe:
- The problem you're trying to solve
- The proposed solution
- Any alternatives you've considered

### Pull Requests

1. Fork the repo and create your branch from `main` (or `master`)
2. If you've added code, add tests
3. Ensure the test suite passes
4. Make sure your code lints
5. Issue the pull request

## Development Setup

```bash
# Clone the repo
git clone https://github.com/notebookworrk-cyber/zoya-easy-code.git
cd zoya-easy-code

# Install in editable mode
pip install -e .

# Install dev dependencies
pip install pytest pytest-cov black ruff
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zoya --cov-report=term-missing
```

## Code Style

- We use `ruff` for linting and `black` for formatting
- Run `ruff check .` before committing
- Run `black .` to auto-format
- Type hints are encouraged for all public APIs

## Project Structure

```
zoya/
├── zoya/              # Core interpreter
│   ├── lexer.py       # Lexical analysis
│   ├── parser.py      # Syntax analysis
│   ├── interpreter.py # Runtime execution
│   ├── ast.py         # AST node definitions
│   ├── builtins.py    # Built-in functions
│   ├── environment.py # Variable scoping
│   └── errors.py      # Error types
├── stdlib/            # Standard library modules
├── tools/             # Developer tools
├── tests/             # Test suite
└── examples/          # Example programs
```

## Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers where applicable
- Use present tense ("Add feature" not "Added feature")

## Questions?

Open a [discussion](https://github.com/notebookworrk-cyber/zoya-easy-code/discussions) for Q&A.
