from __future__ import annotations

import pytest

from zoya.errors import RuntimeError_
from zoya.interpreter import interpret
from zoya.lexer import tokenize
from zoya.parser import parse


def _run(source: str):
    tokens = tokenize(source)
    ast = parse(tokens)
    return interpret(ast)


def test_number_literal():
    result = _run("42\n")
    assert result == 42


def test_float_literal():
    result = _run("3.14\n")
    assert isinstance(result, float)
    assert abs(result - 3.14) < 0.001


def test_string_literal():
    result = _run('"hello"\n')
    assert result == "hello"


def test_boolean_true():
    result = _run("true\n")
    assert result is True


def test_boolean_false():
    result = _run("false\n")
    assert result is False


def test_ident_undefined():
    with pytest.raises(RuntimeError_) as exc:
        _run("undefined_var\n")
    assert "is not defined" in str(exc.value)


def test_assign_and_lookup():
    result = _run("x = 10\nx\n")
    assert result == 10


def test_assign_reassign():
    result = _run("x = 10\nx = 20\nx\n")
    assert result == 20


def test_add():
    result = _run("1 + 2\n")
    assert result == 3


def test_subtract():
    result = _run("10 - 3\n")
    assert result == 7


def test_multiply():
    result = _run("4 * 5\n")
    assert result == 20


def test_divide():
    result = _run("10 / 2\n")
    assert result == 5.0


def test_power():
    result = _run("2 ** 3\n")
    assert result == 8


def test_modulo():
    result = _run("10 % 3\n")
    assert result == 1


def test_gt():
    result = _run("5 > 3\n")
    assert result is True


def test_lt():
    result = _run("5 < 3\n")
    assert result is False


def test_eq():
    result = _run("5 == 5\n")
    assert result is True


def test_ne():
    result = _run("5 != 3\n")
    assert result is True


def test_gte():
    assert _run("5 >= 5\n") is True
    assert _run("6 >= 5\n") is True
    assert _run("4 >= 5\n") is False


def test_lte():
    assert _run("5 <= 5\n") is True
    assert _run("4 <= 5\n") is True
    assert _run("6 <= 5\n") is False


def test_not():
    assert _run("not true\n") is False
    assert _run("not false\n") is True


def test_and():
    assert _run("true and true\n") is True
    assert _run("true and false\n") is False


def test_or():
    assert _run("true or false\n") is True
    assert _run("false or false\n") is False


def test_string_concat():
    result = _run('"hello " + "world"\n')
    assert result == "hello world"


def test_string_concat_with_number():
    result = _run('"count: " + 42\n')
    assert result == "count: 42"


def test_precedence():
    result = _run("1 + 2 * 3\n")
    assert result == 7


def test_parentheses():
    result = _run("(1 + 2) * 3\n")
    assert result == 9


def test_if_true():
    result = _run("if true {\n    42\n}\n")
    assert result == 42


def test_if_false():
    result = _run("if false {\n    42\n}\n")
    assert result is None


def test_if_else_true():
    result = _run("if true {\n    1\n} else {\n    2\n}\n")
    assert result == 1


def test_if_else_false():
    result = _run("if false {\n    1\n} else {\n    2\n}\n")
    assert result == 2


def test_if_else_if():
    result = _run(
        "x = 5\nif x > 10 {\n    1\n} else if x > 3 {\n    2\n} else {\n    3\n}\n"
    )
    assert result == 2


def test_while_loop():
    result = _run("x = 0\nwhile x < 3 {\n    x = x + 1\n}\nx\n")
    assert result == 3


def test_loop():
    result = _run("x = 0\nloop 5 {\n    x = x + 1\n}\nx\n")
    assert result == 5


def test_for_loop():
    result = _run("for i = 0; i < 3; i = i + 1 {\n    x = i\n}\nx\n")
    assert result == 2


def test_foreach_iterable():
    result = _run(
        "items = [10, 20, 30]\nsum = 0\nforeach item in items {\n    sum = sum + item\n}\nsum\n"
    )
    assert result == 60


def test_for_in():
    result = _run(
        "items = [1, 2, 3]\nsum = 0\nfor item in items {\n    sum = sum + item\n}\nsum\n"
    )
    assert result == 6


def test_break():
    result = _run(
        "x = 0\nloop 10 {\n    if x == 3 {\n        break\n    }\n    x = x + 1\n}\nx\n"
    )
    assert result == 3


def test_continue():
    result = _run(
        "items = []\nloop 5 {\n    i = 0\n    if i == 2 {\n        continue\n    }\n    items.append(i)\n}\n"
        + "items\n"
    )
    result = _run(
        "x = 0\nloop 5 {\n    x = x + 1\n    if x == 3 {\n        continue\n    }\n    y = x\n}\ny\n"
    )
    assert result == 5


def test_function_no_params():
    result = _run("fn f() {\n    return 42\n}\nf()\n")
    assert result == 42


def test_function_with_params():
    result = _run("fn add(a, b) {\n    return a + b\n}\nadd(3, 4)\n")
    assert result == 7


def test_function_recursion():
    result = _run(
        "fn fact(n) {\n    if n <= 1 {\n        return 1\n    }\n    return n * fact(n - 1)\n}\nfact(5)\n"
    )
    assert result == 120


def test_function_default_param():
    result = _run("fn f(x = 10) {\n    return x\n}\nf()\n")
    assert result == 10


def test_function_default_param_override():
    result = _run("fn f(x = 10) {\n    return x\n}\nf(20)\n")
    assert result == 20


def test_closure():
    result = _run(
        "fn make_counter() {\n    count = 0\n    fn increment() {\n        count = count + 1\n        return count\n    }\n    return increment\n}\nc = make_counter()\nc()\nc()\n"
    )
    assert result == 2


def test_nested_function():
    result = _run(
        "fn outer() {\n    fn inner() {\n        return 42\n    }\n    return inner()\n}\nouter()\n"
    )
    assert result == 42


def test_list_creation():
    result = _run("[1, 2, 3]\n")
    assert result == [1, 2, 3]


def test_list_index():
    result = _run("items = [10, 20, 30]\nitems[1]\n")
    assert result == 20


def test_list_assign_index():
    result = _run("items = [1, 2, 3]\nitems[0] = 99\nitems[0]\n")
    assert result == 99


def test_list_append():
    result = _run("items = [1, 2]\nitems.append(3)\nitems\n")
    assert result == [1, 2, 3]


def test_list_pop():
    result = _run("items = [1, 2, 3]\nitems.pop()\n")
    assert result == 3


def test_list_length():
    result = _run("[1, 2, 3].length()\n")
    assert result == 3


def test_list_sort():
    result = _run("items = [3, 1, 2]\nitems.sort()\nitems\n")
    assert result == [1, 2, 3]


def test_list_reverse():
    result = _run("items = [1, 2, 3]\nitems.reverse()\nitems\n")
    assert result == [3, 2, 1]


def test_list_remove():
    result = _run("items = [1, 2, 3]\nitems.remove(2)\nitems\n")
    assert result == [1, 3]


def test_list_insert():
    result = _run("items = [1, 3]\nitems.insert(1, 2)\nitems\n")
    assert result == [1, 2, 3]


def test_list_clear():
    result = _run("items = [1, 2, 3]\nitems.clear()\nitems\n")
    assert result == []


def test_list_copy():
    result = _run("items = [1, 2]\na = items.copy()\na\n")
    assert result == [1, 2]


def test_dict_creation():
    result = _run('d = {"a": 1, "b": 2}\nd\n')
    assert result == {"a": 1, "b": 2}


def test_dict_key_access():
    result = _run('d = {"a": 1}\nd["a"]\n')
    assert result == 1


def test_dict_assign():
    result = _run('d = {"a": 1}\nd["b"] = 2\nd["b"]\n')
    assert result == 2


def test_dict_keys():
    result = _run('d = {"a": 1, "b": 2}\nd.keys()\n')
    assert sorted(result) == ["a", "b"]


def test_dict_values():
    result = _run('d = {"a": 1, "b": 2}\nd.values()\n')
    assert sorted(result) == [1, 2]


def test_dict_contains():
    result = _run('d = {"a": 1}\nd.contains("a")\n')
    assert result is True


def test_dict_get():
    result = _run('d = {"a": 1}\nd.get("b", 42)\n')
    assert result == 42


def test_slice():
    result = _run("items = [0, 1, 2, 3, 4]\nitems[1:4]\n")
    assert result == [1, 2, 3]


def test_slice_no_start():
    result = _run("items = [0, 1, 2, 3]\nitems[:2]\n")
    assert result == [0, 1]


def test_slice_step():
    result = _run("items = [0, 1, 2, 3, 4]\nitems[0:5:2]\n")
    assert result == [0, 2, 4]


def test_eq_on_strings():
    assert _run('"hello" == "hello"\n') is True
    assert _run('"hello" == "world"\n') is False


def test_ne_on_strings():
    assert _run('"hello" != "world"\n') is True


def test_in_operator_list():
    assert _run("3 in [1, 2, 3]\n") is True
    assert _run("4 in [1, 2, 3]\n") is False


def test_in_operator_string():
    assert _run('"ello" in "hello"\n') is True


def test_boolean_truethy():
    assert _run("if 1 {\n    true\n} else {\n    false\n}\n") is True
    assert _run("if 0 {\n    true\n} else {\n    false\n}\n") is False
    assert _run('if "" {\n    true\n} else {\n    false\n}\n') is False
    assert _run('if "x" {\n    true\n} else {\n    false\n}\n') is True


def test_block_returns_last():
    result = _run("{\n    1\n    2\n    3\n}\n")
    assert result == 3


def test_string_methods():
    assert _run('"hello".upper()\n') == "HELLO"
    assert _run('"HELLO".lower()\n') == "hello"
    assert _run('"  hi  ".strip()\n') == "hi"
    assert _run('"a,b,c".split(",")\n') == ["a", "b", "c"]


def test_string_startswith():
    result = _run('"hello".startswith("he")\n')
    assert result is True


def test_string_endswith():
    result = _run('"hello".endswith("lo")\n')
    assert result is True


def test_string_contains():
    result = _run('"hello".contains("ell")\n')
    assert result is True


def test_string_replace():
    result = _run('"hello world".replace("world", "zoya")\n')
    assert result == "hello zoya"


def test_len():
    result = _run('len("hello")\n')
    assert result == 5
    result = _run("len([1, 2, 3])\n")
    assert result == 3


def test_int():
    result = _run('int("42")\n')
    assert result == 42
    assert isinstance(result, int)


def test_float():
    result = _run('float("3.14")\n')
    assert isinstance(result, float)


def test_str():
    result = _run("str(42)\n")
    assert result == "42"
    assert isinstance(result, str)


def test_bool():
    result = _run("bool(1)\n")
    assert result is True
    result = _run("bool(0)\n")
    assert result is False


def test_type():
    result = _run("type(42)\n")
    assert result == "int"
    result = _run('type("hi")\n')
    assert result == "str"


def test_range():
    result = _run("range(5)\n")
    assert result == [0, 1, 2, 3, 4]


def test_abs():
    result = _run("abs(-5)\n")
    assert result == 5


def test_min():
    result = _run("min(3, 1, 2)\n")
    assert result == 1


def test_max():
    result = _run("max(3, 1, 2)\n")
    assert result == 3


def test_round():
    result = _run("round(3.14159, 2)\n")
    assert abs(result - 3.14) < 0.01


def test_sum():
    result = _run("sum([1, 2, 3, 4, 5])\n")
    assert result == 15


def test_hex():
    result = _run("hex(255)\n")
    assert result == "0xff"


def test_bin():
    result = _run("bin(10)\n")
    assert result == "0b1010"


def test_list_builtin():
    result = _run("list(1, 2, 3)\n")
    assert result == [1, 2, 3]


def test_true_constant():
    result = _run("True\n")
    assert result is True


def test_false_constant():
    result = _run("False\n")
    assert result is False


def test_none_constant():
    result = _run("None\n")
    assert result is None


def test_lambda_call():
    result = _run("fn(x, y) { return x + y }(3, 4)\n")
    assert result == 7


def test_lambda_arrow():
    result = _run("(lambda(x) -> x * 2)(5)\n")
    assert result == 10


def test_lambda_closure():
    result = _run(
        "fn make_mult(n) {\n    return lambda(x) -> x * n\n}\ndouble = make_mult(2)\ndouble(5)\n"
    )
    assert result == 10


def test_class_instantiation():
    source = 'class Greeter {\n    fn init(name) {\n        this.name = name\n    }\n    fn greet() {\n        return "Hello, " + this.name\n    }\n}\ng = Greeter("Zoya")\ng.greet()\n'
    result = _run(source)
    assert result == "Hello, Zoya"


def test_class_no_init():
    source = "class Empty {\n}\ne = Empty()\n"
    result = _run(source)
    from zoya.interpreter import ZoyaInstance

    assert isinstance(result, ZoyaInstance)


def test_class_inheritance():
    source = 'class Animal {\n    fn speak() {\n        return "sound"\n    }\n}\nclass Dog extends Animal {\n    fn bark() {\n        return "woof"\n    }\n}\nd = Dog()\nd.speak()\n'
    result = _run(source)
    assert result == "sound"


def test_class_inheritance_super_call():
    source = 'class Animal {\n    fn init(name) {\n        this.name = name\n    }\n}\nclass Dog extends Animal {\n    fn init(name) {\n        super.init(name)\n    }\n    fn get_name() {\n        return this.name\n    }\n}\nd = Dog("Rex")\nd.get_name()\n'
    result = _run(source)
    assert result == "Rex"


def test_class_field_access():
    source = "class Point {\n    fn init(x, y) {\n        this.x = x\n        this.y = y\n    }\n}\np = Point(3, 4)\np.x\n"
    result = _run(source)
    assert result == 3


def test_enum():
    source = "enum Color { RED, GREEN, BLUE }\nc = Color.RED\nc\n"
    result = _run(source)
    assert result == 0


def test_enum_green():
    source = "enum Color { RED, GREEN, BLUE }\nColor.GREEN\n"
    result = _run(source)
    assert result == 1


def test_throw_catch():
    source = 'try {\n    throw "something broke"\n} catch e {\n    "caught: " + e\n}\n'
    result = _run(source)
    assert "caught:" in result


def test_try_no_throw():
    result = _run("try {\n    42\n} catch e {\n    0\n}\n")
    assert result == 42


def test_try_finally():
    source = "x = 0\ntry {\n    x = 1\n} finally {\n    x = 2\n}\nx\n"
    result = _run(source)
    assert result == 2


def test_try_throw_finally():
    source = 'x = 0\ntry {\n    throw "err"\n} catch e {\n    x = 1\n} finally {\n    x = 2\n}\nx\n'
    result = _run(source)
    assert result == 2


def test_switch_match():
    source = 'x = 2\nswitch x {\n    case 1 {\n        result = "one"\n    }\n    case 2 {\n        result = "two"\n    }\n}\nresult\n'
    result = _run(source)
    assert result == "two"


def test_switch_default():
    source = 'x = 99\nswitch x {\n    case 1 {\n        result = "one"\n    }\n    default {\n        result = "other"\n    }\n}\nresult\n'
    result = _run(source)
    assert result == "other"


def test_match():
    source = 'fn describe(x) {\n    match x {\n        1 -> "one",\n        2 -> "two",\n        default -> "other"\n    }\n}\ndescribe(1)\n'
    result = _run(source)
    assert result == "one"


def test_match_default():
    source = 'fn describe(x) {\n    match x {\n        1 -> "one",\n        default -> "other"\n    }\n}\ndescribe(99)\n'
    result = _run(source)
    assert result == "other"


def test_print_statement(capsys):
    _run('print "hello world"\n')
    captured = capsys.readouterr()
    assert "hello world" in captured.out


def test_print_with_expression(capsys):
    _run("print 1 + 2\n")
    captured = capsys.readouterr()
    assert "3" in captured.out


def test_interpolated_string():
    result = _run('name = "Zoya"\nf"Hello, {name}!"\n')
    assert result == "Hello, Zoya!"


def test_interpolated_string_expression():
    result = _run('f"Sum: {1 + 2}"\n')
    assert result == "Sum: 3"


def test_unary_minus():
    result = _run("-42\n")
    assert result == -42


def test_unary_minus_expression():
    result = _run("-(1 + 2)\n")
    assert result == -3


def test_complex_expression():
    result = _run("(1 + 2) * (3 + 4) - 5\n")
    assert result == 16


def test_division_by_number():
    result = _run("10 / 3\n")
    assert abs(result - 3.33333) < 0.001


def test_error_undefined_variable():
    with pytest.raises(RuntimeError_):
        _run("z\n")


def test_foreach_string():
    result = _run('s = ""\nfor ch in "abc" {\n    s = s + ch\n}\ns\n')
    assert result == "abc"


def test_nested_if():
    result = _run(
        'x = 10\nif x > 0 {\n    if x > 5 {\n        result = "big"\n    } else {\n        result = "small"\n    }\n}\nresult\n'
    )
    assert result == "big"


def test_return_from_loop():
    result = _run(
        "fn find(items, target) {\n    for item in items {\n        if item == target {\n            return item\n        }\n    }\n    return -1\n}\nfind([1, 2, 3], 2)\n"
    )
    assert result == 2


def test_modified_in_loop():
    result = _run(
        "items = [1, 2, 3]\ni = 0\nwhile i < len(items) {\n    items[i] = items[i] * 10\n    i = i + 1\n}\nitems\n"
    )
    assert result == [10, 20, 30]


def test_dict_clear():
    result = _run('d = {"a": 1}\nd.clear()\nd\n')
    assert result == {}


def test_dict_copy():
    result = _run('d = {"a": 1}\nc = d.copy()\nc\n')
    assert result == {"a": 1}


def test_string_method_chain():
    result = _run('"  Hello  ".strip().upper()\n')
    assert result == "HELLO"


def test_index_out_of_range():
    with pytest.raises(Exception):  # noqa: B017
        _run("items = [1]\nitems[5]\n")


def test_slice_string():
    result = _run('"hello world"[:5]\n')
    assert result == "hello"


def test_neg_index():
    result = _run("items = [10, 20, 30]\nitems[-1]\n")
    assert result == 30


def test_empty_dict():
    result = _run("items = []\nitems\n")
    assert result == []
    result = _run('d = {"a": 1}\nd.clear()\nd\n')
    assert result == {}


def test_import_via_run(capsys):
    result = _run('import "math" as math\nmath.pi\n')
    assert result > 3.14


def test_repr_functions():
    result = _run("fn f() {\n    return 1\n}\nf\n")
    assert "function" in str(result).lower()


def test_class_repr():
    result = _run("class C {\n}\nC\n")
    assert "class" in str(result).lower()


def test_enum_repr():
    result = _run("enum E { A, B }\nE\n")
    assert "enum" in str(result).lower()


def test_instance_repr():
    result = _run("class C {\n}\nc = C()\nc\n")
    assert "instance" in str(result).lower()


def test_module_repr():
    result = _run('import "math" as m\nm\n')
    assert "module" in str(result).lower()


def test_named_args():
    result = _run("fn f(a, b) {\n    return a * 10 + b\n}\nf(b = 3, a = 2)\n")
    assert result == 23


def test_truthiness_none():
    assert _run("if None {\n    true\n} else {\n    false\n}\n") is False


def test_loop_non_number():
    import pytest

    with pytest.raises(Exception):  # noqa: B017
        _run('loop "a" {\n    print 1\n}\n')


def test_error_unknown_op():
    result = _run("5 in 3\n")
    assert result is False


def test_class_parent_not_class():
    import pytest

    with pytest.raises(Exception):  # noqa: B017
        _run("class A {\n}\nclass B extends A {\n}\nclass C extends 42 {\n}\n")


def test_index_non_indexable():
    import pytest

    with pytest.raises(Exception):  # noqa: B017
        _run("42[0]\n")


def test_method_on_non_object():
    import pytest

    with pytest.raises(Exception):  # noqa: B017
        _run("42.unknown()\n")


def test_lambda_defaults():
    result = _run("fn(x = 5) { return x }()\n")
    assert result == 5


def test_none_truthiness():
    assert _run("not None\n") is True


def test_assign_index_with_list():
    result = _run("items = [1, 2, 3]\nitems[1] = 99\nitems\n")
    assert result == [1, 99, 3]


def test_assign_index_with_dict():
    result = _run("d = {'a': 1}\nd['b'] = 2\nd['b']\n")
    assert result == 2


def test_interface_in_env():
    result = _run("interface I {\n    fn foo()\n}\nI\n")
    assert "interface" in str(result).lower()


def test_error_division_non_number():
    import pytest

    with pytest.raises(Exception):  # noqa: B017
        _run('"hello" / 2\n')


def test_while_false_body():
    result = _run("while false {\n    42\n}\n")
    assert result is None


def test_for_empty_iterable():
    result = _run("items = []\nfor item in items {\n    item\n}\n")
    assert result is None
