from __future__ import annotations

from zoya.tools.profiler import profile_source


class TestProfileSource:
    def test_basic_script(self) -> None:
        result = profile_source("print 1 + 2\n")
        assert "total_time" in result
        assert isinstance(result["total_time"], float)
        assert result["total_time"] >= 0

    def test_function_profiling(self) -> None:
        source = "fn add(a, b) {\n    return a + b\n}\nprint add(1, 2)\n"
        result = profile_source(source)
        assert "function_stats" in result
        assert isinstance(result["function_stats"], dict)

    def test_line_counts(self) -> None:
        source = "x = 1\ny = 2\nprint x + y\n"
        result = profile_source(source)
        assert "line_counts" in result
        assert isinstance(result["line_counts"], dict)

    def test_script_with_loop(self) -> None:
        source = "sum = 0\nloop 3 {\n    sum = sum + 1\n}\nprint sum\n"
        result = profile_source(source)
        assert result["total_time"] >= 0

    def test_error_does_not_crash(self) -> None:
        result = profile_source("x = \n")
        assert "total_time" in result

    def test_empty_source(self) -> None:
        result = profile_source("\n")
        assert "total_time" in result
        assert result["line_counts"] == {}
