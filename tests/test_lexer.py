from __future__ import annotations

import pytest
from zoya.lexer import Token, tokenize
from zoya.errors import LexError


def _check_token(tok: Token, kind: str, value: str, line: int = 1, col: int = 1):
    assert tok.kind == kind, f"Expected kind={kind}, got {tok.kind}"
    assert tok.value == value, f"Expected value={value!r}, got {tok.value!r}"
    assert tok.line == line
    assert tok.col == col


def test_empty_source():
    tokens = tokenize("")
    assert len(tokens) == 1
    assert tokens[0].kind == "EOF"


def test_newline_only():
    tokens = tokenize("\n")
    assert len(tokens) == 2
    _check_token(tokens[0], "NEWLINE", "\n")
    _check_token(tokens[1], "EOF", "", 2, 1)


def test_number_int():
    tokens = tokenize("42")
    assert len(tokens) == 2
    _check_token(tokens[0], "NUMBER", "42")
    assert tokens[0].kind == "NUMBER"


def test_number_float():
    tokens = tokenize("3.14")
    assert len(tokens) == 2
    _check_token(tokens[0], "NUMBER", "3.14")


def test_number_multiple():
    tokens = tokenize("1 2.5 100")
    kinds = [t.kind for t in tokens]
    assert kinds == ["NUMBER", "NUMBER", "NUMBER", "EOF"]
    values = [t.value for t in tokens]
    assert values == ["1", "2.5", "100", ""]


def test_string_double():
    tokens = tokenize('"hello"')
    assert len(tokens) == 2
    _check_token(tokens[0], "STRING", "hello")


def test_string_single():
    tokens = tokenize("'hello'")
    assert len(tokens) == 2
    _check_token(tokens[0], "STRING", "hello")


def test_string_empty():
    tokens = tokenize('""')
    assert len(tokens) == 2
    _check_token(tokens[0], "STRING", "")


def test_interpolated_string():
    tokens = tokenize('f"hello {name}"')
    assert len(tokens) == 2
    _check_token(tokens[0], "INTERP_STRING", "hello {name}")


def test_ident():
    tokens = tokenize("hello")
    assert len(tokens) == 2
    _check_token(tokens[0], "IDENT", "hello")


def test_keywords():
    keywords = [
        ("fn", "FN"), ("return", "RETURN"), ("if", "IF"), ("else", "ELSE"),
        ("while", "WHILE"), ("loop", "LOOP"), ("for", "FOR"), ("break", "BREAK"),
        ("continue", "CONTINUE"), ("import", "IMPORT"), ("switch", "SWITCH"),
        ("case", "CASE"), ("default", "DEFAULT"), ("try", "TRY"), ("catch", "CATCH"),
        ("finally", "FINALLY"), ("throw", "THROW"), ("match", "MATCH"),
        ("enum", "ENUM"), ("class", "CLASS"), ("interface", "INTERFACE"),
        ("extends", "EXTENDS"), ("implements", "IMPLEMENTS"), ("abstract", "ABSTRACT"),
        ("static", "STATIC"), ("new", "NEW"), ("this", "THIS"), ("super", "SUPER"),
        ("lambda", "LAMBDA"), ("async", "ASYNC"), ("await", "AWAIT"),
        ("and", "AND"), ("or", "OR"), ("not", "NOT"),
        ("true", "TRUE"), ("false", "FALSE"), ("in", "IN"),
    ]
    for keyword, expected_kind in keywords:
        tokens = tokenize(keyword)
        _check_token(tokens[0], expected_kind, keyword)


def test_operators():
    ops = [
        ("+", "PLUS"), ("-", "MINUS"), ("*", "MUL"), ("/", "DIV"),
        (">", "GT"), ("<", "LT"), ("==", "EQ"), ("!=", "NE"),
        (">=", "GTE"), ("<=", "LTE"), ("**", "POW"), ("%", "MOD"),
    ]
    for op_str, expected_kind in ops:
        tokens = tokenize(op_str)
        _check_token(tokens[0], expected_kind, op_str)


def test_delimiters():
    delims = [
        ("(", "LPAREN"), (")", "RPAREN"), ("{", "LBRACE"), ("}", "RBRACE"),
        ("[", "LBRACKET"), ("]", "RBRACKET"), (",", "COMMA"), (":", "COLON"),
        (";", "SEMICOLON"), (".", "DOT"), ("->", "ARROW"), ("::", "DOUBLE_COLON"),
    ]
    for delim_str, expected_kind in delims:
        tokens = tokenize(delim_str)
        _check_token(tokens[0], expected_kind, delim_str)


def test_assign():
    tokens = tokenize("=")
    _check_token(tokens[0], "ASSIGN", "=")


def test_whitespace_skipped():
    tokens = tokenize("  \t  ")
    assert len(tokens) == 1
    assert tokens[0].kind == "EOF"


def test_comment_line_skipped():
    tokens = tokenize("// this is a comment")
    assert len(tokens) == 1
    assert tokens[0].kind == "EOF"


def test_comment_hash_skipped():
    tokens = tokenize("# this is a comment")
    assert len(tokens) == 1
    assert tokens[0].kind == "EOF"


def test_multi_comment_skipped():
    tokens = tokenize("/* multi\nline */")
    assert len(tokens) == 1
    assert tokens[0].kind == "EOF"


def test_mismatch_token():
    tokens = tokenize("@")
    assert len(tokens) == 2
    assert tokens[0].kind == "MISMATCH"
    assert tokens[0].value == "@"

    tokens = tokenize("`")
    assert tokens[0].kind == "MISMATCH"
    assert tokens[0].value == "`"


def test_multi_line_program():
    source = 'fn add(a, b) {\n    return a + b\n}\n'
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert kinds == [
        "FN", "IDENT", "LPAREN", "IDENT", "COMMA", "IDENT", "RPAREN",
        "LBRACE", "NEWLINE",
        "RETURN", "IDENT", "PLUS", "IDENT", "NEWLINE",
        "RBRACE", "NEWLINE",
        "EOF",
    ]


def test_program_with_if_else():
    source = 'if x > 5 {\n    print "big"\n} else {\n    print "small"\n}\n'
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "IF" in kinds
    assert "ELSE" in kinds
    assert "LBRACE" in kinds
    assert "RBRACE" in kinds


def test_list_literal():
    source = "[1, 2, 3]"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind != "SKIP"]
    assert kinds == ["LBRACKET", "NUMBER", "COMMA", "NUMBER", "COMMA", "NUMBER", "RBRACKET", "EOF"]


def test_dict_literal():
    source = '{"key": "val"}'
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind != "SKIP"]
    assert kinds == ["LBRACE", "STRING", "COLON", "STRING", "RBRACE", "EOF"]


def test_class_definition():
    source = 'class Animal {\n    fn speak() {\n        print "sound"\n    }\n}\n'
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "CLASS" in kinds
    assert "IDENT" in kinds
    assert "FN" in kinds


def test_enum_definition():
    source = "enum Color { RED, GREEN, BLUE }\n"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "ENUM" in kinds
    ident_count = sum(1 for k in kinds if k == "IDENT")
    assert ident_count > 0


def test_try_catch():
    source = 'try {\n    throw "err"\n} catch e {\n    print e\n}\n'
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "TRY" in kinds
    assert "CATCH" in kinds
    assert "THROW" in kinds


def test_switch_statement():
    source = "switch x {\n    case 1 {\n        print \"one\"\n    }\n}\n"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "SWITCH" in kinds
    assert "CASE" in kinds


def test_not_operator():
    tokens = tokenize("not true")
    assert len(tokens) == 3
    _check_token(tokens[0], "NOT", "not", col=1)
    _check_token(tokens[1], "TRUE", "true", col=5)


def test_and_or():
    source = "x and y or z"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind != "SKIP"]
    assert "AND" in kinds
    assert "OR" in kinds


def test_lambda():
    source = "lambda(x, y) { return x + y }"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "LAMBDA" in kinds
    assert "IDENT" in kinds


def test_import_statement():
    source = 'import "math" as m\n'
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "IMPORT" in kinds
    assert "STRING" in kinds


def test_interpolated_string_marker():
    tokens = tokenize('f"hello"')
    assert tokens[0].kind == "INTERP_STRING"


def test_class_extends():
    source = "class Dog extends Animal {\n}\n"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "CLASS" in kinds
    assert "EXTENDS" in kinds


def test_interface():
    source = "interface Speaker {\n    fn speak()\n}\n"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "INTERFACE" in kinds


def test_foreach():
    source = "foreach item in items {\n}\n"
    tokens = tokenize(source)
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "FOREACH" in kinds


def test_async_await():
    tokens = tokenize("async fn fetch() {\n    await result\n}\n")
    kinds = [t.kind for t in tokens if t.kind not in ("SKIP",)]
    assert "ASYNC" in kinds
    assert "AWAIT" in kinds


def test_ident_underscore():
    tokens = tokenize("_myVar _ __")
    kinds = [t.kind for t in tokens if t.kind != "SKIP"]
    assert all(k == "IDENT" for k in kinds[:-1])


def test_ident_numbers_allowed():
    tokens = tokenize("var1 var2_3")
    kinds = [t.kind for t in tokens if t.kind != "SKIP"]
    assert all(k == "IDENT" for k in kinds[:-1])


def test_multi_comment_with_newlines():
    source = "/* line1\nline2\nline3 */\n"
    tokens = tokenize(source)
    _check_token(tokens[0], "NEWLINE", "\n", 3, 9)


def test_mismatch_dollar():
    tokens = tokenize("$invalid")
    assert tokens[0].kind == "MISMATCH"
    assert tokens[0].value == "$"


def test_mismatch_backslash():
    tokens = tokenize("\\invalid")
    assert tokens[0].kind == "MISMATCH"
