from __future__ import annotations

from zoya import run
from zoya.errors import ParseError


def test_hello_world():
    run('print "Hello, World!"')


def test_variables():
    run("x = 10\ny = 20\nprint x + y")


def test_if_else():
    run('x = 10\nif x > 5 {\n    print "yes"\n} else {\n    print "no"\n}')


def test_loop():
    run('loop 3 {\n    print "hello"\n}')


def test_function():
    run("fn add(a, b) {\n    return a + b\n}\nprint add(2, 3)")


def test_list():
    run("nums = [1, 2, 3]\nnums.append(4)\nprint nums[0]")


def test_dict():
    run('person = {"name": "Zoya", "age": 1}\nprint person["name"]')


def test_nested_if_else():
    run(
        'x = 15\nif x > 10 {\n    if x > 20 {\n        print ">20"\n    } else {\n        print "10-20"\n    }\n} else {\n    print "<=10"\n}'
    )


def test_while_sum():
    run(
        "sum = 0\ni = 1\nwhile i <= 10 {\n    sum = sum + i\n    i = i + 1\n}\nprint sum"
    )


def test_recursive_fib():
    code = """
fn fib(n) {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}
print fib(10)
"""
    run(code)


def test_string_methods():
    run('text = "  hello  "\nprint text.upper()\nprint text.strip()')


def test_list_sort():
    run("nums = [3, 1, 4, 1, 5]\nnums.sort()\nprint nums[0]\nprint nums.length()")


def test_class():
    code = """
class Dog {
    fn init(name) {
        this.name = name
    }
    fn speak() {
        return this.name + " says woof"
    }
}
d = Dog("Rex")
print d.speak()
"""
    run(code)


def test_enum():
    code = "enum Color { RED, GREEN, BLUE }\nc = Color.GREEN\nprint c\n"
    run(code)


def test_try_catch():
    code = """
try {
    throw "error!"
} catch msg {
    print "caught: " + msg
}
"""
    run(code)


def test_lambda():
    code = "double = lambda(x) -> x * 2\nprint double(5)\n"
    run(code)


def test_interpolated_string():
    code = 'name = "Zoya"\nprint f"Hello, {name}!"\n'
    run(code)


def test_for_loop():
    code = "for i = 0; i < 5; i = i + 1 {\n    print i\n}\n"
    run(code)


def test_for_each():
    code = 'for item in ["a", "b", "c"] {\n    print item\n}\n'
    run(code)


def test_switch():
    code = 'x = 2\nswitch x {\n    case 1 { print "one" }\n    case 2 { print "two" }\n    default { print "other" }\n}\n'
    run(code)


def test_match():
    code = 'fn f(x) {\n    match x {\n        1 -> "one",\n        default -> "other"\n    }\n}\nprint f(1)\nprint f(99)\n'
    run(code)


def test_import():
    code = 'import "math" as m\nprint m.sqrt(16)\n'
    run(code)


def test_slice():
    code = "items = [0, 1, 2, 3, 4]\nprint items[1:4]\n"
    run(code)


def test_chained_comparison():
    code = 'x = 5\nif x > 0 and x < 10 {\n    print "in range"\n}\n'
    run(code)


def test_closure():
    code = """
fn counter() {
    i = 0
    fn inc() {
        i = i + 1
        return i
    }
    return inc
}
c = counter()
print c()
print c()
"""
    run(code)


def test_default_params():
    code = """
fn greet(name = "World") {
    print "Hello, " + name
}
greet()
greet("Zoya")
"""
    run(code)


def test_foreach_on_string():
    code = 'result = ""\nfor ch in "abc" {\n    result = result + ch\n}\nprint result\n'
    run(code)


def test_math_operations():
    run("print 2 ** 10")
    run("print 10 % 3")
    run("print abs(-5)")
    run("print max(1, 2, 3)")
    run("print min(1, 2, 3)")


def test_parse_error():
    import pytest

    with pytest.raises(ParseError):
        run("x = ")


def test_type_error():
    import pytest

    with pytest.raises(Exception):  # noqa: B017
        run('"hello" - "world"')
