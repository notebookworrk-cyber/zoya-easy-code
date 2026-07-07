from __future__ import annotations

from zoya.tools.linter import lint


class TestLintLineLength:
    def test_short_line(self) -> None:
        issues = lint("print 1\n")
        assert all(i["message"] != "Line too long" for i in issues)

    def test_long_line(self) -> None:
        source = "x = " + "a" * 100 + "\n"
        issues = lint(source)
        assert any("Line too long" in i["message"] for i in issues)
        assert any(i["severity"] == "warning" for i in issues)


class TestLintTrailingNewline:
    def test_trailing_newline_ok(self) -> None:
        issues = lint("print 1\n")
        assert all("No newline at end" not in i["message"] for i in issues)

    def test_missing_trailing_newline(self) -> None:
        issues = lint("print 1")
        assert any("No newline at end" in i["message"] for i in issues)
        assert any(i["severity"] == "style" for i in issues)


class TestLintIndentation:
    def test_spaces_ok(self) -> None:
        source = "if x {\n    print 1\n}\n"
        issues = lint(source)
        assert all("Indentation" not in i["message"] for i in issues)
        assert all("Tab character" not in i["message"] for i in issues)

    def test_tab_indentation(self) -> None:
        source = "if x {\n\tprint 1\n}\n"
        issues = lint(source)
        assert any("Tab character" in i["message"] for i in issues)

    def test_inconsistent_spaces(self) -> None:
        source = "if x {\n   print 1\n}\n"
        issues = lint(source)
        assert any("Inconsistent indentation" in i["message"] for i in issues)


class TestLintUnusedVars:
    def test_unused_variable(self) -> None:
        source = "x = 10\nprint 1\n"
        issues = lint(source)
        assert any("Unused variable" in i["message"] for i in issues)

    def test_used_variable(self) -> None:
        source = "x = 10\nprint x\n"
        issues = lint(source)
        assert all("Unused variable" not in i["message"] for i in issues)

    def test_ignore_underscore(self) -> None:
        source = "_ = 10\nprint 1\n"
        issues = lint(source)
        assert all("Unused variable" not in i["message"] for i in issues)

    def test_builtin_not_reported(self) -> None:
        source = "print 1\n"
        issues = lint(source)
        assert all("Unused variable" not in i["message"] for i in issues)

    def test_function_param_no_report(self) -> None:
        source = "fn add(a, b) {\n    return a + b\n}\nprint add(1, 2)\n"
        issues = lint(source)
        assert all("Unused variable" not in i["message"] for i in issues)

    def test_foreach_var_no_report(self) -> None:
        source = "for item in [1, 2, 3] {\n    print item\n}\n"
        issues = lint(source)
        assert all("Unused variable" not in i["message"] for i in issues)

    def test_parse_error_does_not_crash(self) -> None:
        issues = lint("x = \n")
        assert isinstance(issues, list)


class TestLintSorting:
    def test_issues_sorted_by_line_then_col(self) -> None:
        source = "    x = " + "a" * 100 + "\n"
        issues = lint(source)
        for i in range(1, len(issues)):
            assert (issues[i]["line"], issues[i]["col"]) >= (
                issues[i - 1]["line"],
                issues[i - 1]["col"],
            )
