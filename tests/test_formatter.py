from __future__ import annotations

from zoya.tools.formatter import format_source


class TestFormatSource:
    def test_empty_source(self) -> None:
        result = format_source("")
        assert result == "\n"

    def test_print_statement(self) -> None:
        result = format_source('print "hello"\n')
        assert 'print "hello"' in result

    def test_variable_assignment(self) -> None:
        result = format_source("x = 42\n")
        assert "x = 42" in result

    def test_function_def(self) -> None:
        source = "fn greet(name) {\n    print name\n}\n"
        result = format_source(source)
        assert "fn greet(name) {" in result
        assert "    print name" in result
        assert "}" in result

    def test_if_else(self) -> None:
        source = 'if x > 5 {\n    print "big"\n} else {\n    print "small"\n}\n'
        result = format_source(source)
        assert "if x > 5 {" in result
        assert "else {" in result

    def test_while_loop(self) -> None:
        source = "while x < 5 {\n    x = x + 1\n}\n"
        result = format_source(source)
        assert "while x < 5 {" in result

    def test_loop_stmt(self) -> None:
        source = 'loop 3 {\n    print "hi"\n}\n'
        result = format_source(source)
        assert "loop 3 {" in result

    def test_for_loop(self) -> None:
        source = "for i = 0; i < 5; i = i + 1 {\n    print i\n}\n"
        result = format_source(source)
        assert "for i = 0; i < 5; i = i + 1 {" in result

    def test_foreach_loop(self) -> None:
        source = "for item in [1, 2] {\n    print item\n}\n"
        result = format_source(source)
        assert "foreach" in result or "for item in" in result

    def test_list_literal(self) -> None:
        result = format_source("x = [1, 2, 3]\n")
        assert "[1, 2, 3]" in result

    def test_dict_literal(self) -> None:
        result = format_source('x = {"a": 1}\n')
        assert '{"a": 1}' in result

    def test_return_stmt(self) -> None:
        result = format_source("fn f() {\n    return 42\n}\n")
        assert "return 42" in result

    def test_break_continue(self) -> None:
        result = format_source("loop 5 {\n    break\n    continue\n}\n")
        assert "break" in result
        assert "continue" in result

    def test_binop_format(self) -> None:
        result = format_source("x = 1 + 2\n")
        assert "1 + 2" in result

    def test_call_format(self) -> None:
        result = format_source("print(1, 2)\n")
        assert "print(1, 2)" in result

    def test_method_call(self) -> None:
        result = format_source('"hello".upper()\n')
        assert '"hello".upper()' in result

    def test_index_and_slice(self) -> None:
        result = format_source("x = a[1]\ny = a[1:3]\n")
        assert "a[1]" in result
        assert "a[1:3]" in result

    def test_interpolated_string(self) -> None:
        source = 'name = "Zoya"\nresult = f"Hello, {name}!"\n'
        result = format_source(source)
        assert 'f"' in result

    def test_import_stmt(self) -> None:
        result = format_source('import "math" as m\n')
        assert 'import "math" as m' in result

    def test_trailing_newline(self) -> None:
        source = 'print "hello"\n'
        result = format_source(source)
        assert result.endswith("\n")
