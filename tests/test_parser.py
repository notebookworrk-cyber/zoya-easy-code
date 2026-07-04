from __future__ import annotations

import pytest

from zoya.ast import (
    Assign,
    BinOp,
    Block,
    Boolean,
    Break,
    Call,
    ClassDef,
    Continue,
    Dict_,
    EnumDef,
    ForEach,
    ForLoop,
    Function,
    GetAttr,
    Ident,
    If,
    Import,
    Index,
    InterpolatedString,
    Lambda,
    List_,
    Loop,
    Match,
    MethodCall,
    Number,
    Print,
    Return,
    Slice,
    String,
    Switch,
    Throw,
    Try,
    UnaryOp,
    While,
)
from zoya.lexer import tokenize
from zoya.parser import parse


def _get_ast(source: str):
    tokens = tokenize(source)
    return parse(tokens)


def _first_stmt(source: str):
    block = _get_ast(source)
    assert len(block.statements) > 0
    return block.statements[0]


def test_number():
    node = _first_stmt("42")
    assert isinstance(node, Number)
    assert node.value == 42


def test_number_float():
    node = _first_stmt("3.14")
    assert isinstance(node, Number)
    assert node.value == 3.14


def test_string():
    node = _first_stmt('"hello"')
    assert isinstance(node, String)
    assert node.value == "hello"


def test_empty_string():
    node = _first_stmt('""')
    assert isinstance(node, String)
    assert node.value == ""


def test_boolean_true():
    node = _first_stmt("true")
    assert isinstance(node, Boolean)
    assert node.value is True


def test_boolean_false():
    node = _first_stmt("false")
    assert isinstance(node, Boolean)
    assert node.value is False


def test_ident():
    node = _first_stmt("x")
    assert isinstance(node, Ident)
    assert node.name == "x"


def test_assign():
    node = _first_stmt("x = 10")
    assert isinstance(node, Assign)
    assert node.name == "x"
    assert isinstance(node.expr, Number)
    assert node.expr.value == 10


def test_binop():
    node = _first_stmt("x + y")
    assert isinstance(node, BinOp) or (isinstance(node, Ident) and False)


def test_binop_plus():
    node = _first_stmt("1 + 2")
    assert isinstance(node, BinOp)
    assert node.op == "PLUS"


def test_binop_minus():
    node = _first_stmt("10 - 3")
    assert isinstance(node, BinOp)
    assert node.op == "MINUS"


def test_binop_mul():
    node = _first_stmt("4 * 5")
    assert isinstance(node, BinOp)
    assert node.op == "MUL"


def test_binop_div():
    node = _first_stmt("10 / 2")
    assert isinstance(node, BinOp)
    assert node.op == "DIV"


def test_binop_pow():
    node = _first_stmt("2 ** 3")
    assert isinstance(node, BinOp)
    assert node.op == "POW"


def test_binop_mod():
    node = _first_stmt("10 % 3")
    assert isinstance(node, BinOp)
    assert node.op == "MOD"


def test_comparison_gt():
    node = _first_stmt("x > 5")
    assert isinstance(node, BinOp)
    assert node.op == "GT"


def test_comparison_lt():
    node = _first_stmt("x < 5")
    assert isinstance(node, BinOp)
    assert node.op == "LT"


def test_comparison_eq():
    node = _first_stmt("x == 5")
    assert isinstance(node, BinOp)
    assert node.op == "EQ"


def test_comparison_ne():
    node = _first_stmt("x != 5")
    assert isinstance(node, BinOp)
    assert node.op == "NE"


def test_comparison_gte():
    node = _first_stmt("x >= 5")
    assert isinstance(node, BinOp)
    assert node.op == "GTE"


def test_comparison_lte():
    node = _first_stmt("x <= 5")
    assert isinstance(node, BinOp)
    assert node.op == "LTE"


def test_and():
    node = _first_stmt("x and y")
    assert isinstance(node, BinOp)
    assert node.op == "AND"


def test_or():
    node = _first_stmt("x or y")
    assert isinstance(node, BinOp)
    assert node.op == "OR"


def test_not():
    node = _first_stmt("not x")
    assert isinstance(node, UnaryOp)
    assert node.op == "NOT"


def test_unary_minus():
    node = _first_stmt("-5")
    assert isinstance(node, UnaryOp)
    assert node.op == "MINUS"


def test_precedence():
    node = _first_stmt("1 + 2 * 3")
    assert isinstance(node, BinOp)
    assert node.op == "PLUS"
    assert isinstance(node.right, BinOp)
    assert node.right.op == "MUL"


def test_parentheses():
    node = _first_stmt("(1 + 2) * 3")
    assert isinstance(node, BinOp)
    assert node.op == "MUL"
    assert isinstance(node.left, BinOp)
    assert node.left.op == "PLUS"


def test_block():
    source = "{\n    x = 1\n    y = 2\n}\n"
    block = _first_stmt(source)
    assert isinstance(block, Block)
    assert len(block.statements) == 2


def test_if():
    source = 'if x > 5 {\n    print "big"\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, If)
    assert isinstance(node.cond, BinOp)
    assert isinstance(node.body, Block)


def test_if_else():
    source = 'if x > 5 {\n    print "big"\n} else {\n    print "small"\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, If)
    assert node.else_body is not None
    assert isinstance(node.else_body, Block)


def test_if_else_if():
    source = 'if x > 5 {\n    print "big"\n} else if x > 0 {\n    print "medium"\n} else {\n    print "small"\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, If)
    assert node.else_body is not None
    else_block = node.else_body
    assert isinstance(else_block, Block)
    assert len(else_block.statements) == 1
    assert isinstance(else_block.statements[0], If)


def test_while():
    source = "while x < 10 {\n    x = x + 1\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, While)
    assert isinstance(node.cond, BinOp)
    assert isinstance(node.body, Block)


def test_loop():
    source = 'loop 5 {\n    print "hi"\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Loop)
    assert isinstance(node.count, Number)
    assert node.count.value == 5
    assert isinstance(node.body, Block)


def test_for_loop_style():
    source = "for i = 0; i < 10; i = i + 1 {\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, ForLoop)
    assert node.init is not None
    assert node.cond is not None
    assert node.update is not None


def test_foreach():
    source = "foreach item in items {\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, ForEach)
    assert node.var == "item"


def test_for_in():
    source = "for item in items {\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, ForEach)
    assert node.var == "item"


def test_function_def():
    source = "fn add(a, b) {\n    return a + b\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, Function)
    assert node.name == "add"
    assert node.params == ["a", "b"]
    assert isinstance(node.body, Block)


def test_function_default_params():
    source = 'fn greet(name = "World") {\n    print name\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Function)
    assert node.params == ["name"]
    assert len(node.defaults) == 1
    assert node.defaults[0] is not None


def test_function_call():
    source = "add(1, 2)\n"
    node = _first_stmt(source)
    assert isinstance(node, Call)
    assert isinstance(node.callee, Ident)
    assert node.callee.name == "add"
    assert len(node.args) == 2


def test_nested_function_call():
    source = "add(sub(1), 2)\n"
    node = _first_stmt(source)
    assert isinstance(node, Call)
    assert len(node.args) == 2


def test_return():
    source = "return 42\n"
    node = _first_stmt(source)
    assert isinstance(node, Return)
    assert node.expr is not None
    assert isinstance(node.expr, Number)
    assert node.expr.value == 42


def test_return_void():
    source = "return\n"
    node = _first_stmt(source)
    assert isinstance(node, Return)
    assert node.expr is None


def test_break():
    source = "break\n"
    node = _first_stmt(source)
    assert isinstance(node, Break)


def test_continue():
    source = "continue\n"
    node = _first_stmt(source)
    assert isinstance(node, Continue)


def test_list_literal():
    source = "nums = [1, 2, 3]\n"
    node = _first_stmt(source)
    assert isinstance(node, Assign)
    assert isinstance(node.expr, List_)
    assert len(node.expr.elements) == 3


def test_empty_list():
    source = "x = []\n"
    node = _first_stmt(source)
    assert isinstance(node, Assign)
    assert isinstance(node.expr, List_)
    assert len(node.expr.elements) == 0


def test_dict_literal():
    source = 'person = {"name": "Alice", "age": 30}\n'
    node = _first_stmt(source)
    assert isinstance(node, Assign)
    assert isinstance(node.expr, Dict_)
    assert len(node.expr.pairs) == 2


def test_index():
    source = "items[0]\n"
    node = _first_stmt(source)
    assert isinstance(node, Index)
    assert isinstance(node.index, Number)
    assert node.index.value == 0


def test_assign_index():
    source = "items[0] = 42\n"
    node = _first_stmt(source)
    from zoya.ast import AssignIndex

    assert isinstance(node, AssignIndex)
    assert isinstance(node.index, Number)
    assert node.index.value == 0


def test_method_call():
    source = "items.append(4)\n"
    node = _first_stmt(source)
    assert isinstance(node, MethodCall)
    assert node.method == "append"
    assert len(node.args) == 1


def test_get_attr():
    source = "obj.attr\n"
    node = _first_stmt(source)
    assert isinstance(node, GetAttr)
    assert node.attr == "attr"


def test_assign_attr():
    source = "obj.attr = 42\n"
    node = _first_stmt(source)
    from zoya.ast import AssignAttr

    assert isinstance(node, AssignAttr)
    assert node.attr == "attr"


def test_class_def():
    source = 'class Animal {\n    fn speak() {\n        print "sound"\n    }\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, ClassDef)
    assert node.name == "Animal"
    assert node.parent is None
    assert isinstance(node.body, Block)


def test_class_def_with_parent():
    source = (
        'class Dog extends Animal {\n    fn bark() {\n        print "woof"\n    }\n}\n'
    )
    node = _first_stmt(source)
    assert isinstance(node, ClassDef)
    assert node.name == "Dog"
    assert node.parent == "Animal"


def test_class_def_with_colon_parent():
    source = "class Dog: Animal {\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, ClassDef)
    assert node.name == "Dog"
    assert node.parent == "Animal"


def test_enum_def():
    source = "enum Color { RED, GREEN, BLUE }\n"
    node = _first_stmt(source)
    assert isinstance(node, EnumDef)
    assert node.name == "Color"
    assert node.variants == ["RED", "GREEN", "BLUE"]


def test_enum_empty():
    source = "enum Empty {}\n"
    node = _first_stmt(source)
    assert isinstance(node, EnumDef)
    assert node.name == "Empty"
    assert node.variants == []


def test_switch():
    source = 'switch x {\n    case 1 {\n        print "one"\n    }\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Switch)
    assert len(node.cases) == 1


def test_switch_with_default():
    source = 'switch x {\n    case 1 {\n        print "one"\n    }\n    default {\n        print "other"\n    }\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Switch)
    assert node.default_body is not None


def test_try_catch():
    source = 'try {\n    throw "err"\n} catch e {\n    print e\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Try)
    assert len(node.catches) == 1
    assert node.catches[0].var == "e"


def test_try_finally():
    source = 'try {\n    print "try"\n} finally {\n    print "finally"\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Try)
    assert len(node.catches) == 0
    assert node.final_body is not None


def test_try_catch_finally():
    source = 'try {\n    throw "err"\n} catch e {\n    print e\n} finally {\n    print "done"\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Try)
    assert len(node.catches) == 1
    assert node.final_body is not None


def test_throw():
    source = 'throw "error"\n'
    node = _first_stmt(source)
    assert isinstance(node, Throw)
    assert isinstance(node.expr, String)


def test_import():
    source = 'import "math"\n'
    node = _first_stmt(source)
    assert isinstance(node, Import)
    assert node.path == "math"
    assert node.alias is None


def test_import_with_alias():
    source = 'import "math" as m\n'
    node = _first_stmt(source)
    assert isinstance(node, Import)
    assert node.path == "math"
    assert node.alias == "m"


def test_lambda():
    source = "fn(x, y) { return x + y }\n"
    node = _first_stmt(source)
    assert isinstance(node, Lambda)
    assert node.params == ["x", "y"]


def test_lambda_with_arrow():
    source = "lambda(x) -> x + 1\n"
    node = _first_stmt(source)
    assert isinstance(node, Lambda)
    assert node.params == ["x"]


def test_match():
    source = 'match x {\n    1 -> print("one"),\n    2 -> print("two")\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Match)
    assert len(node.arms) == 2


def test_match_with_default():
    source = 'match x {\n    1 -> print("one"),\n    default -> print("other")\n}\n'
    node = _first_stmt(source)
    assert isinstance(node, Match)
    assert len(node.arms) == 1
    assert node.else_arm is not None


def test_print():
    source = 'print "hello"\n'
    node = _first_stmt(source)
    assert isinstance(node, Print)


def test_interpolated_string():
    source = 'f"hello {name}"\n'
    node = _first_stmt(source)
    assert isinstance(node, InterpolatedString)


def test_slice():
    source = "items[1:3]\n"
    node = _first_stmt(source)
    assert isinstance(node, Slice)
    assert node.start is not None
    assert node.stop is not None


def test_slice_no_start():
    source = "items[:5]\n"
    node = _first_stmt(source)
    assert isinstance(node, Slice)
    assert node.start is None
    assert node.stop is not None


def test_slice_step():
    source = "items[0:10:2]\n"
    node = _first_stmt(source)
    assert isinstance(node, Slice)
    assert node.step is not None


def test_chained_method_call():
    source = "data.strip().upper()\n"
    node = _first_stmt(source)
    assert isinstance(node, MethodCall)
    assert node.method == "upper"


def test_named_arguments():
    source = "fn f(a, b) {\n    return a + b\n}\nf(b = 2, a = 1)\n"
    block = _get_ast(source)
    call_node = block.statements[1]
    assert isinstance(call_node, Call)
    from zoya.ast import NamedArg

    assert any(isinstance(a, NamedArg) for a in call_node.args)


def test_chained_comparison():
    node = _first_stmt("x < y and y < z")
    assert isinstance(node, BinOp)
    assert node.op == "AND"


def test_unexpected_token():
    source = "x = @\n"
    with pytest.raises(Exception):  # noqa: B017
        _first_stmt(source)


def test_empty_block():
    source = "{\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, Block)
    assert len(node.statements) == 0


def test_interface_def():
    source = "interface Speaker {\n    fn speak()\n}\n"
    node = _first_stmt(source)
    assert isinstance(
        node, __import__("zoya.ast", fromlist=["InterfaceDef"]).InterfaceDef
    )


def test_block_as_statement():
    source = "{\n    print 1\n    print 2\n}\n"
    node = _first_stmt(source)
    assert isinstance(node, Block)
    assert len(node.statements) == 2


def test_expression_statement():
    source = "1 + 2\n"
    node = _first_stmt(source)
    assert isinstance(node, BinOp)


def test_semicolon_separator():
    source = "x = 1; y = 2\n"
    block = _get_ast(source)
    assert len(block.statements) == 2


def test_line_continuation():
    source = "x = 1\n\ny = 2\n"
    block = _get_ast(source)
    assert len(block.statements) == 2


def test_comment_in_code():
    source = "// comment\nx = 1\n"
    block = _get_ast(source)
    assert len(block.statements) == 1
    assert isinstance(block.statements[0], Assign)
