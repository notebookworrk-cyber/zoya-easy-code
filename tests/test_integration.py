from __future__ import annotations

import sys
from pathlib import Path

import pytest

from zoya.cli import main as cli_main
from zoya.cli import run_file


def _run_source(source: str):
    tokens = __import__("zoya.lexer", fromlist=["tokenize"]).tokenize(source)
    ast = __import__("zoya.parser", fromlist=["parse"]).parse(tokens)
    return __import__("zoya.interpreter", fromlist=["interpret"]).interpret(ast)


class TestExamplePrograms:
    EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

    def test_hello(self, capsys):
        source = (self.EXAMPLES_DIR / "hello.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "Hello, World!" in captured.out
        assert "Welcome to Zoya!" in captured.out
        assert "Sum: 30" in captured.out
        assert "Product: 200" in captured.out

    def test_fibonacci(self, capsys):
        source = (self.EXAMPLES_DIR / "fibonacci.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "Fibonacci sequence:" in captured.out
        for i in [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]:
            assert str(i) in captured.out

    def test_loops(self, capsys):
        source = (self.EXAMPLES_DIR / "loops.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "Hello from Zoya!" in captured.out

    def test_lists(self, capsys):
        source = (self.EXAMPLES_DIR / "lists.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "Sorted:" in captured.out

    def test_strings(self, capsys):
        source = (self.EXAMPLES_DIR / "strings.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "HELLO, ZOYA!" in captured.out or "HELLO, ZOYA" in captured.out.upper()

    def test_enum_demo(self, capsys):
        source = (self.EXAMPLES_DIR / "enum_demo.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "Red!" in captured.out

    def test_match_demo(self, capsys):
        source = (self.EXAMPLES_DIR / "match_demo.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "one" in captured.out

    def test_math_demo(self, capsys):
        source = (self.EXAMPLES_DIR / "math_demo.zoya").read_text()
        _run_source(source)
        captured = capsys.readouterr()
        assert "Math Module" in captured.out
        assert "sqrt" in captured.out

    def test_calculator_needs_input(self):
        source = (self.EXAMPLES_DIR / "calculator.zoya").read_text()
        tokens = __import__("zoya.lexer", fromlist=["tokenize"]).tokenize(source)
        ast = __import__("zoya.parser", fromlist=["parse"]).parse(tokens)
        assert ast is not None
        assert len(ast.statements) > 0

    def test_todo_zoya(self, capsys):
        source = (self.EXAMPLES_DIR / "todo.zoya").read_text()
        tokens = __import__("zoya.lexer", fromlist=["tokenize"]).tokenize(source)
        ast = __import__("zoya.parser", fromlist=["parse"]).parse(tokens)
        assert ast is not None

    def test_all_examples_parse_successfully(self):
        for f in sorted(self.EXAMPLES_DIR.glob("*.zoya")):
            source = f.read_text()
            try:
                tokens = __import__("zoya.lexer", fromlist=["tokenize"]).tokenize(
                    source
                )
                ast = __import__("zoya.parser", fromlist=["parse"]).parse(tokens)
                assert ast is not None
            except Exception as e:
                pytest.fail(f"Failed to parse {f.name}: {e}")


class TestCLI:
    def test_run_file(self, capsys, tmp_path):
        zoya_file = tmp_path / "test.zoya"
        zoya_file.write_text('print "cli test"\n')
        run_file(str(zoya_file))
        captured = capsys.readouterr()
        assert "cli test" in captured.out

    def test_run_file_not_found(self, capsys):
        with pytest.raises(SystemExit):
            run_file("nonexistent.zoya")
        captured = capsys.readouterr()
        assert "file not found" in captured.err.lower()

    def test_run_file_with_error(self, capsys, tmp_path):
        zoya_file = tmp_path / "error.zoya"
        zoya_file.write_text("x = @\n")
        with pytest.raises(SystemExit):
            run_file(str(zoya_file))
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_repl_flag(self):
        test_args = ["zoya", "--repl"]
        sys.argv = test_args
        try:
            cli_main()
        except SystemExit:
            pass
        except OSError:
            pass

    def test_version_flag(self, capsys):
        test_args = ["zoya", "--version"]
        try:
            sys.argv = test_args
            with pytest.raises(SystemExit) as exc:
                cli_main()
            assert exc.value.code == 0
            captured = capsys.readouterr()
            assert "Zoya v" in captured.out
        except SystemExit:
            raise

    def test_examples_flag(self, capsys):
        test_args = ["zoya", "--examples"]
        try:
            sys.argv = test_args
            with pytest.raises(SystemExit) as exc:
                cli_main()
            assert exc.value.code == 0
            captured = capsys.readouterr()
            assert "Zoya Examples" in captured.out
        except SystemExit:
            raise

    def test_inline_command(self, capsys):
        test_args = ["zoya", "-c", 'print "inline test"']
        try:
            sys.argv = test_args
            with pytest.raises(SystemExit) as exc:
                cli_main()
            assert exc.value.code == 0
            captured = capsys.readouterr()
            assert "inline test" in captured.out
        except SystemExit:
            raise

    def test_no_args_shows_help(self, capsys):
        test_args = ["zoya"]
        try:
            sys.argv = test_args
            with pytest.raises(SystemExit) as exc:
                cli_main()
            assert exc.value.code == 1
        except SystemExit:
            raise


class TestFullPipeline:
    def test_tokenize_parse_interpret(self):
        source = "x = 42\nx + 8\n"
        tokens = __import__("zoya.lexer", fromlist=["tokenize"]).tokenize(source)
        ast = __import__("zoya.parser", fromlist=["parse"]).parse(tokens)
        result = __import__("zoya.interpreter", fromlist=["interpret"]).interpret(ast)
        assert result == 50

    def test_recursive_function(self):
        source = "fn fact(n) {\n    if n <= 1 {\n        return 1\n    }\n    return n * fact(n - 1)\n}\nfact(6)\n"
        result = _run_source(source)
        assert result == 720

    def test_complex_nested_structures(self):
        source = """
fn make_accumulator(initial) {
    sum = initial
    fn add(n) {
        sum = sum + n
        return sum
    }
    return add
}
acc = make_accumulator(0)
acc(5)
acc(10)
acc(3)
"""
        result = _run_source(source)
        assert result == 18

    def test_class_with_methods(self, capsys):
        source = """
class Counter {
    fn init() {
        this.count = 0
    }
    fn increment() {
        this.count = this.count + 1
    }
    fn get() {
        return this.count
    }
}
c = Counter()
c.increment()
c.increment()
c.increment()
print c.get()
"""
        _run_source(source)
        captured = capsys.readouterr()
        assert "3" in captured.out

    def test_foreach_over_dict_keys(self):
        source = 'd = {"a": 1, "b": 2, "c": 3}\nkeys = d.keys()\nsum = 0\nfor k in keys {\n    sum = sum + d[k]\n}\nsum\n'
        result = _run_source(source)
        assert result == 6

    def test_error_propagation(self):
        source = 'fn inner() {\n    throw "inner error"\n}\nfn outer() {\n    inner()\n}\ntry {\n    outer()\n} catch e {\n    "caught: " + e\n}\n'
        result = _run_source(source)
        assert "inner error" in result

    def test_break_nested_loops(self):
        source = "result = 0\ni = 0\nwhile i < 5 {\n    j = 0\n    while j < 5 {\n        if j == 2 {\n            break\n        }\n        result = result + 1\n        j = j + 1\n    }\n    i = i + 1\n}\nresult\n"
        result = _run_source(source)
        assert result == 10

    def test_continue_in_loop(self):
        source = "result = []\nfor i in range(5) {\n    if i == 2 {\n        continue\n    }\n    result.append(i)\n}\nresult\n"
        result = _run_source(source)
        assert result == [0, 1, 3, 4]

    def test_lambda_passed_as_arg(self):
        source = "fn apply(f, x) {\n    return f(x)\n}\napply(lambda(x) -> x * 3, 7)\n"
        result = _run_source(source)
        assert result == 21

    def test_nested_list_operations(self):
        source = "matrix = [[1, 2], [3, 4]]\nmatrix[0][1]\n"
        result = _run_source(source)
        assert result == 2

    def test_in_operator_with_string(self):
        result = _run_source('"world" in "hello world"\n')
        assert result is True

    def test_boolean_negation(self):
        result = _run_source("not not true\n")
        assert result is True

    def test_truthiness(self):
        assert _run_source("if 1 {\n    1\n} else {\n    0\n}\n") == 1
        assert _run_source("if 0 {\n    1\n} else {\n    0\n}\n") == 0
        assert _run_source('if "a" {\n    1\n} else {\n    0\n}\n') == 1
        assert _run_source('if "" {\n    1\n} else {\n    0\n}\n') == 0
        assert _run_source("if [] {\n    1\n} else {\n    0\n}\n") == 0
        assert _run_source("if [1] {\n    1\n} else {\n    0\n}\n") == 1
