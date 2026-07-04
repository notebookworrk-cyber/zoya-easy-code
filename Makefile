.PHONY: test lint format clean install build

test:
	pytest --cov=zoya tests/

test-v:
	pytest -v --cov=zoya tests/

lint:
	ruff check .

format:
	ruff format .

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .ruff_cache/
	rm -rf .coverage coverage/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

install:
	pip install -e ".[test]"

build:
	python -m build
