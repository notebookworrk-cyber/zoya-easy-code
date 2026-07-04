from __future__ import annotations

import pytest

from zoya.interpreter import interpret
from zoya.lexer import tokenize
from zoya.parser import parse


@pytest.fixture
def run_zoya():
    def _run(code: str):
        tokens = tokenize(code)
        ast = parse(tokens)
        return interpret(ast)

    return _run


@pytest.fixture
def capture_output(run_zoya, capsys):
    def _run(code: str):
        result = run_zoya(code)
        captured = capsys.readouterr()
        return result, captured.out, captured.err

    return _run
