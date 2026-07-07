from __future__ import annotations

from zoya.tools.docs import extract_comments, format_expr, generate_docs


class TestExtractComments:
    def test_single_line_comment(self) -> None:
        source = "// hello\nprint 1\n"
        result = extract_comments(source, 2)
        assert result == "hello"

    def test_hash_comment(self) -> None:
        source = "# hello\nprint 1\n"
        result = extract_comments(source, 2)
        assert result == "hello"

    def test_multiline_comments(self) -> None:
        source = "// line1\n// line2\nprint 1\n"
        result = extract_comments(source, 3)
        assert result == "line1\nline2"

    def test_no_comments(self) -> None:
        source = "print 1\n"
        result = extract_comments(source, 1)
        assert result == ""

    def test_blank_line_stops_at_code(self) -> None:
        source = "// comment\n\nx = 1\nprint 1\n"
        result = extract_comments(source, 3)
        assert result == ""


class TestFormatExpr:
    def test_number(self) -> None:
        from zoya.ast import Number

        result = format_expr(Number(42))
        assert result == "42"

    def test_string(self) -> None:
        from zoya.ast import String

        result = format_expr(String("hello"))
        assert result == '"hello"'

    def test_boolean(self) -> None:
        from zoya.ast import Boolean

        result = format_expr(Boolean(True))
        assert result == "true"

    def test_ident(self) -> None:
        from zoya.ast import Ident

        result = format_expr(Ident("x"))
        assert result == "x"


class TestGenerateDocs:
    def test_function_doc(self) -> None:
        source = "// Add two numbers\nfn add(a, b) {\n    return a + b\n}\n"
        result = generate_docs(source, "test.zoya")
        assert "## fn `add(a, b)`" in result
        assert "Add two numbers" in result
        assert "test.zoya" in result

    def test_empty_source(self) -> None:
        result = generate_docs("", "empty.zoya")
        assert result is not None

    def test_no_functions(self) -> None:
        result = generate_docs('print "hello"\n', "hello.zoya")
        assert "##" not in result
