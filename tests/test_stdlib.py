from __future__ import annotations

import pytest
from zoya import run
from zoya.interpreter import Interpreter, interpret
from zoya.lexer import tokenize
from zoya.parser import parse


def _run(source: str):
    tokens = tokenize(source)
    ast = parse(tokens)
    return interpret(ast)


class TestMathModule:
    def test_import_math(self):
        result = _run('import "math" as m\nm.pi\n')
        assert result > 3.14

    def test_math_e(self):
        result = _run('import "math" as m\nm.e\n')
        assert result > 2.71

    def test_math_sqrt(self):
        result = _run('import "math" as m\nm.sqrt(16)\n')
        assert result == 4.0

    def test_math_sin(self):
        result = _run('import "math" as m\nm.sin(0)\n')
        assert abs(result) < 0.001

    def test_math_cos(self):
        result = _run('import "math" as m\nm.cos(0)\n')
        assert abs(result - 1.0) < 0.001

    def test_math_tan(self):
        result = _run('import "math" as m\nm.tan(0)\n')
        assert abs(result) < 0.001

    def test_math_ceil(self):
        result = _run('import "math" as m\nm.ceil(3.14)\n')
        assert result == 4.0

    def test_math_floor(self):
        result = _run('import "math" as m\nm.floor(3.14)\n')
        assert result == 3.0

    def test_math_factorial(self):
        result = _run('import "math" as m\nm.factorial(5)\n')
        assert result == 120

    def test_math_log(self):
        result = _run('import "math" as m\nm.log(1)\n')
        assert abs(result) < 0.001

    def test_math_log10(self):
        result = _run('import "math" as m\nm.log10(100)\n')
        assert abs(result - 2.0) < 0.001

    def test_math_pow(self):
        result = _run('import "math" as m\nm.pow(2, 3)\n')
        assert result == 8.0

    def test_math_degrees(self):
        result = _run('import "math" as m\nm.degrees(3.14159)\n')
        assert abs(result - 180.0) < 0.01

    def test_math_radians(self):
        result = _run('import "math" as m\nm.radians(180)\n')
        assert abs(result - 3.14159) < 0.01

    def test_math_gcd(self):
        result = _run('import "math" as m\nm.gcd(12, 8)\n')
        assert result == 4

    def test_math_asin(self):
        result = _run('import "math" as m\nm.asin(0)\n')
        assert abs(result) < 0.001

    def test_math_acos(self):
        result = _run('import "math" as m\nm.acos(1)\n')
        assert abs(result) < 0.001

    def test_math_atan(self):
        result = _run('import "math" as m\nm.atan(0)\n')
        assert abs(result) < 0.001

    def test_math_atan2(self):
        result = _run('import "math" as m\nm.atan2(1, 1)\n')
        assert abs(result - 0.785) < 0.01

    def test_math_inf(self):
        result = _run('import "math" as m\nm.inf\n')
        import math
        assert result == math.inf

    def test_math_nan(self):
        result = _run('import "math" as m\nm.nan\n')
        import math
        assert str(result) == str(math.nan)


class TestStringModule:
    def test_import_string(self):
        result = _run('import "string" as s\ns.upper("hello")\n')
        assert result == "HELLO"

    def test_string_lower(self):
        result = _run('import "string" as s\ns.lower("HELLO")\n')
        assert result == "hello"

    def test_string_capitalize(self):
        result = _run('import "string" as s\ns.capitalize("hello")\n')
        assert result == "Hello"

    def test_string_title(self):
        result = _run('import "string" as s\ns.title("hello world")\n')
        assert result == "Hello World"

    def test_string_strip(self):
        result = _run('import "string" as s\ns.strip("  hi  ")\n')
        assert result == "hi"

    def test_string_lstrip(self):
        result = _run('import "string" as s\ns.lstrip("  hi  ")\n')
        assert result == "hi  "

    def test_string_rstrip(self):
        result = _run('import "string" as s\ns.rstrip("  hi  ")\n')
        assert result == "  hi"

    def test_string_replace(self):
        result = _run('import "string" as s\ns.replace("hello world", "world", "zoya")\n')
        assert result == "hello zoya"

    def test_string_split(self):
        result = _run('import "string" as s\ns.split("a,b,c", ",")\n')
        assert result == ["a", "b", "c"]

    def test_string_join(self):
        result = _run('import "string" as s\ns.join(", ", [1, 2, 3])\n')
        assert result == "1, 2, 3"

    def test_string_startswith(self):
        result = _run('import "string" as s\ns.startswith("hello", "he")\n')
        assert result is True

    def test_string_endswith(self):
        result = _run('import "string" as s\ns.endswith("hello", "lo")\n')
        assert result is True

    def test_string_contains(self):
        result = _run('import "string" as s\ns.contains("hello", "ell")\n')
        assert result is True

    def test_string_format(self):
        result = _run('import "string" as s\ns.format("Hello {}!", "Zoya")\n')
        assert result == "Hello Zoya!"

    def test_string_len(self):
        result = _run('import "string" as s\ns.len("hello")\n')
        assert result == 5

    def test_string_reverse(self):
        result = _run('import "string" as s\ns.reverse("hello")\n')
        assert result == "olleh"

    def test_string_count(self):
        result = _run('import "string" as s\ns.count("hello", "l")\n')
        assert result == 2

    def test_string_find(self):
        result = _run('import "string" as s\ns.find("hello", "e")\n')
        assert result == 1

    def test_string_isdigit(self):
        assert _run('import "string" as s\ns.isdigit("123")\n') is True
        assert _run('import "string" as s\ns.isdigit("abc")\n') is False

    def test_string_isalpha(self):
        assert _run('import "string" as s\ns.isalpha("abc")\n') is True
        assert _run('import "string" as s\ns.isalpha("123")\n') is False

    def test_string_isalnum(self):
        assert _run('import "string" as s\ns.isalnum("abc123")\n') is True

    def test_string_isspace(self):
        assert _run('import "string" as s\ns.isspace("   ")\n') is True
        assert _run('import "string" as s\ns.isspace("abc")\n') is False

    def test_string_islower(self):
        assert _run('import "string" as s\ns.islower("hello")\n') is True
        assert _run('import "string" as s\ns.islower("Hello")\n') is False

    def test_string_isupper(self):
        assert _run('import "string" as s\ns.isupper("HELLO")\n') is True
        assert _run('import "string" as s\ns.isupper("Hello")\n') is False


class TestCollectionsModule:
    def test_deque(self):
        result = _run('import "collections" as c\nc.deque()\n')
        from collections import deque
        assert type(result) == type(deque())

    def test_deque_with_items(self):
        result = _run('import "collections" as c\nc.deque([1, 2, 3])\n')
        assert list(result) == [1, 2, 3]

    def test_counter(self):
        result = _run('import "collections" as c\nc.counter([1, 1, 2, 3])\n')
        assert result == {1: 2, 2: 1, 3: 1}

    def test_defaultdict(self):
        result = _run('import "collections" as c\nc.defaultdict(0)\n')
        assert result[999] == 0

    def test_ordered_dict(self):
        result = _run('import "collections" as c\nc.ordered_dict()\n')
        from collections import OrderedDict
        assert type(result) == type(OrderedDict())

    def test_defaultdict_callable(self):
        result = _run('import "collections" as c\nc.defaultdict(list)\n')
        assert result[999] == []


class TestJsonModule:
    def test_dumps(self):
        result = _run('import "json" as j\nj.dumps({"a": 1, "b": 2})\n')
        assert '"a": 1' in result

    def test_loads(self):
        result = _run("import \"json\" as j\ns = '{\"a\": 1}'\nj.loads(s)\n")
        assert result == {"a": 1}


class TestRandomModule:
    def test_random(self):
        result = _run('import "random" as r\nr.random()\n')
        assert 0 <= result <= 1

    def test_randint(self):
        result = _run('import "random" as r\nr.randint(1, 10)\n')
        assert 1 <= result <= 10

    def test_choice(self):
        result = _run('import "random" as r\nr.choice([10, 20, 30])\n')
        assert result in (10, 20, 30)

    def test_uniform(self):
        result = _run('import "random" as r\nr.uniform(0, 1)\n')
        assert 0 <= result <= 1

    def test_randrange(self):
        result = _run('import "random" as r\nr.randrange(10)\n')
        assert 0 <= result < 10


class TestTimeModule:
    def test_time(self):
        result = _run('import "time" as t\nt.time()\n')
        assert result > 0

    def test_strftime(self):
        result = _run('import "time" as t\nt.strftime("%Y")\n')
        assert len(result) == 4

    def test_gmtime(self):
        result = _run('import "time" as t\nt.gmtime(0)\n')
        assert hasattr(result, "tm_year")


class TestRegexModule:
    def test_search(self):
        result = _run('import "regex" as re\nre.search("world", "hello world")\n')
        assert result == "world"

    def test_findall(self):
        result = _run("import \"regex\" as re\ns = 'ab12cd34'\nre.findall(\"12\", s)\n")
        assert result == ["12"]

    def test_compile(self):
        result = _run("import \"regex\" as re\nre.compile(\"hello\")\n")
        assert result is not None

    def test_replace(self):
        result = _run('import "regex" as r\nr.replace("world", "zoya", "hello world")\n')
        assert result == "hello zoya"


class TestFileModule:
    def test_exists(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        result = _run(f'import "file" as f\nf.exists("{f}")\n')
        assert result is True

    def test_abspath(self):
        result = _run('import "file" as f\nf.abspath(".")\n')
        assert result is not None

    def test_join(self):
        result = _run('import "file" as f\nf.join("a", "b", "c")\n')
        assert "a" in result and "b" in result

    def test_dirname(self):
        result = _run('import "file" as f\nf.dirname("/a/b/c.txt")\n')
        assert result is not None

    def test_basename(self):
        result = _run('import "file" as f\nf.basename("/a/b/c.txt")\n')
        assert result == "c.txt"


class TestSystemModule:
    def test_cwd(self):
        result = _run('import "system" as s\ns.cwd()\n')
        assert len(result) > 0

    def test_platform(self):
        result = _run('import "system" as s\ns.platform()\n')
        assert len(result) > 0

    def test_cpu_count(self):
        result = _run('import "system" as s\ns.cpu_count()\n')
        assert result > 0

    def test_pid(self):
        result = _run('import "system" as s\ns.pid()\n')
        assert result > 0


class TestIOModule:
    def test_format(self):
        result = _run('import "io" as io\nio.format("Hello %s", "Zoya")\n')
        assert result == "Hello Zoya"
