from __future__ import annotations

from zoya.ast import (
    Assign,
    AssignAttr,
    AssignIndex,
    ASTNode,
    BinOp,
    Block,
    Boolean,
    Break,
    Call,
    Continue,
    Dict_,
    ForEach,
    ForLoop,
    Function,
    GetAttr,
    Ident,
    If,
    Import,
    Index,
    Input,
    InterpolatedString,
    List_,
    Loop,
    MethodCall,
    Number,
    Print,
    Return,
    Slice,
    String,
    UnaryOp,
    While,
)
from zoya.lexer import tokenize
from zoya.parser import parse

_OP_STR = {
    "PLUS": " + ",
    "MINUS": " - ",
    "MUL": " * ",
    "DIV": " / ",
    "MOD": " % ",
    "POW": " ** ",
    "GT": " > ",
    "LT": " < ",
    "GTE": " >= ",
    "LTE": " <= ",
    "EQ": " == ",
    "NE": " != ",
    "AND": " and ",
    "OR": " or ",
    "IN": " in ",
}

_UNARY_STR = {"MINUS": "-", "NOT": "not "}


def format_source(source: str) -> str:
    tokens = tokenize(source)
    ast = parse(tokens)
    if isinstance(ast, Block):
        lines = [_format_stmt(s, 0).rstrip("\n") for s in ast.statements]
        result = "\n".join(lines) + "\n"
    else:
        result = _format_stmt(ast, 0)
    result = result.replace("\r\n", "\n")
    result = result.rstrip("\n") + "\n"
    return result


def _format_expr(node: ASTNode) -> str:
    if isinstance(node, Number):
        if isinstance(node.value, float) and node.value == int(node.value):
            return str(int(node.value))
        return str(node.value)
    if isinstance(node, String):
        return _escape_string(node.value)
    if isinstance(node, Boolean):
        return "true" if node.value else "false"
    if isinstance(node, Ident):
        return node.name
    if isinstance(node, BinOp):
        op_str = _OP_STR.get(node.op, f" {node.op} ")
        return f"{_format_expr(node.left)}{op_str}{_format_expr(node.right)}"
    if isinstance(node, UnaryOp):
        op_str = _UNARY_STR.get(node.op, node.op + " ")
        inner = _format_expr(node.expr)
        if isinstance(node.expr, (BinOp, UnaryOp)):
            inner = f"({inner})"
        return f"{op_str}{inner}"
    if isinstance(node, Call):
        args = ", ".join(_format_expr(a) for a in node.args)
        return f"{_format_expr(node.callee)}({args})"
    if isinstance(node, MethodCall):
        args = ", ".join(_format_expr(a) for a in node.args)
        return f"{_format_expr(node.obj)}.{node.method}({args})"
    if isinstance(node, GetAttr):
        return f"{_format_expr(node.obj)}.{node.attr}"
    if isinstance(node, Index):
        return f"{_format_expr(node.obj)}[{_format_expr(node.index)}]"
    if isinstance(node, Slice):
        parts = []
        parts.append(_format_expr(node.start) if node.start else "")
        parts.append(_format_expr(node.stop) if node.stop else "")
        if node.step:
            parts.append(_format_expr(node.step))
        while parts and not parts[-1]:
            parts.pop()
        return f"{_format_expr(node.obj)}[{':'.join(parts)}]"
    if isinstance(node, List_):
        elems = ", ".join(_format_expr(e) for e in node.elements)
        return f"[{elems}]"
    if isinstance(node, Dict_):
        pairs = ", ".join(f"{_format_expr(k)}: {_format_expr(v)}" for k, v in node.pairs)
        return f"{{{pairs}}}"
    if isinstance(node, InterpolatedString):
        return _format_interp_string(node)
    if isinstance(node, Print):
        return f"print {_format_expr(node.expr)}"
    if isinstance(node, Input):
        if node.prompt:
            return f"input {_format_expr(node.prompt)}"
        return "input"
    if isinstance(node, Assign):
        return f"{node.name} = {_format_expr(node.expr)}"
    if isinstance(node, AssignIndex):
        return f"{_format_expr(node.obj)}[{_format_expr(node.index)}] = {_format_expr(node.expr)}"
    if isinstance(node, AssignAttr):
        return f"{_format_expr(node.obj)}.{node.attr} = {_format_expr(node.expr)}"
    if isinstance(node, Return):
        if node.expr:
            return f"return {_format_expr(node.expr)}"
        return "return"
    if isinstance(node, Import):
        result = f'import "{node.path}"'
        if node.alias:
            result += f" as {node.alias}"
        return result
    if isinstance(node, Break):
        return "break"
    if isinstance(node, Continue):
        return "continue"
    return f"/* unknown:{type(node).__name__} */"


def _format_stmt(node: ASTNode, indent: int = 0) -> str:
    prefix = "    " * indent

    if isinstance(node, (Assign, AssignIndex, AssignAttr, Break, Continue, Import)):
        return prefix + _format_expr(node) + "\n"

    if isinstance(node, Print):
        return prefix + _format_expr(node) + "\n"

    if isinstance(node, Input):
        return prefix + _format_expr(node) + "\n"

    if isinstance(node, Return):
        return prefix + _format_expr(node) + "\n"

    if isinstance(node, Function):
        params = ", ".join(node.params)
        lines = [f"{prefix}fn {node.name}({params}) {{"]
        lines.append(_format_block_body(node.body, indent + 1))
        lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(node, If):
        lines = [f"{prefix}if {_format_expr(node.cond)} {{"]
        lines.append(_format_block_body(node.body, indent + 1))
        lines.append(prefix + "}")
        if node.else_body:
            else_block = node.else_body
            if (
                isinstance(else_block, Block)
                and len(else_block.statements) == 1
                and isinstance(else_block.statements[0], If)
            ):
                lines[-1] += " else if " + _format_expr(else_block.statements[0].cond) + " {"
                lines.append(_format_block_body(else_block.statements[0].body, indent + 1))
                lines.append(prefix + "}")
            else:
                lines.append(prefix + "else {")
                lines.append(_format_block_body(else_block, indent + 1))
                lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(node, While):
        lines = [f"{prefix}while {_format_expr(node.cond)} {{"]
        lines.append(_format_block_body(node.body, indent + 1))
        lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(node, Loop):
        lines = [f"{prefix}loop {_format_expr(node.count)} {{"]
        lines.append(_format_block_body(node.body, indent + 1))
        lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(node, ForLoop):
        parts = [f"{prefix}for "]
        if node.init:
            parts.append(_format_expr(node.init).rstrip())
        parts.append("; ")
        if node.cond:
            parts.append(_format_expr(node.cond))
        parts.append("; ")
        if node.update:
            parts.append(_format_expr(node.update).rstrip())
        parts.append(" {")
        lines = ["".join(parts)]
        lines.append(_format_block_body(node.body, indent + 1))
        lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(node, ForEach):
        lines = [f"{prefix}foreach {node.var} in {_format_expr(node.iterable)} {{"]
        lines.append(_format_block_body(node.body, indent + 1))
        lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(node, Block):
        lines = [prefix + "{"]
        lines.append(_format_block_body(node, indent + 1))
        lines.append(prefix + "}")
        return "\n".join(lines) + "\n"

    if isinstance(
        node,
        (
            Number,
            String,
            Boolean,
            Ident,
            BinOp,
            UnaryOp,
            Call,
            GetAttr,
            MethodCall,
            Index,
            Slice,
            List_,
            Dict_,
            InterpolatedString,
        ),
    ):
        return prefix + _format_expr(node) + "\n"

    return prefix + _format_expr(node) + "\n"


def _format_block_body(node: ASTNode, indent: int) -> str:
    if isinstance(node, Block):
        return "\n".join(_format_stmt(s, indent).rstrip("\n") for s in node.statements)
    return _format_stmt(node, indent).rstrip("\n")


def _escape_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _format_interp_string(node: InterpolatedString) -> str:
    result = 'f"'
    for part in node.parts:
        if isinstance(part, str):
            result += part.replace('"', '\\"').replace("{", "{{").replace("}", "}}")
        elif isinstance(part, tuple):
            expr_node, fmt = part
            expr_str = _format_expr(expr_node)
            if fmt:
                result += "{" + expr_str + ":" + fmt + "}"
            else:
                result += "{" + expr_str + "}"
        else:
            result += "{" + _format_expr(part) + "}"
    result += '"'
    return result
