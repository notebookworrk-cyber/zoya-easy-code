"""Documentation generation tool for extracting and rendering Zoya module docs."""

from __future__ import annotations

import os

from zoya.ast import (
    ASTNode,
    BinOp,
    Block,
    Boolean,
    Call,
    ClassDef,
    Dict_,
    EnumDef,
    Function,
    GetAttr,
    Ident,
    Index,
    InterfaceDef,
    Lambda,
    List_,
    MethodCall,
    Number,
    String,
    UnaryOp,
)
from zoya.lexer import tokenize
from zoya.parser import parse


def extract_comments(source: str, line_num: int) -> str:
    lines = source.split("\n")
    comments: list[str] = []
    i = line_num - 2
    while i >= 0:
        stripped = lines[i].strip()
        if stripped.startswith("//"):
            comments.insert(0, stripped[2:].strip())
        elif stripped.startswith("#"):
            comments.insert(0, stripped[1:].strip())
        elif stripped == "":
            break
        else:
            break
        i -= 1
    return "\n".join(comments)


def format_expr(node: ASTNode) -> str:
    if isinstance(node, Number):
        if isinstance(node.value, float) and node.value == int(node.value):
            return str(int(node.value))
        return str(node.value)
    if isinstance(node, String):
        return f'"{node.value}"'
    if isinstance(node, Boolean):
        return "true" if node.value else "false"
    if isinstance(node, Ident):
        return node.name
    if isinstance(node, BinOp):
        return f"{format_expr(node.left)} {node.op} {format_expr(node.right)}"
    if isinstance(node, UnaryOp):
        return f"{node.op}{format_expr(node.expr)}"
    if isinstance(node, Call):
        args = ", ".join(format_expr(a) for a in node.args)
        return f"{format_expr(node.callee)}({args})"
    if isinstance(node, MethodCall):
        args = ", ".join(format_expr(a) for a in node.args)
        return f"{format_expr(node.obj)}.{node.method}({args})"
    if isinstance(node, GetAttr):
        return f"{format_expr(node.obj)}.{node.attr}"
    if isinstance(node, Index):
        return f"{format_expr(node.obj)}[{format_expr(node.index)}]"
    if isinstance(node, List_):
        elems = ", ".join(format_expr(e) for e in node.elements)
        return f"[{elems}]"
    if isinstance(node, Dict_):
        pairs = ", ".join(f"{format_expr(k)}: {format_expr(v)}" for k, v in node.pairs)
        return f"{{{pairs}}}"
    if isinstance(node, Lambda):
        params = ", ".join(node.params)
        return f"fn({params}) -> ..."
    return f"<{type(node).__name__}>"


def generate_docs(source: str, filepath: str = "") -> str:
    tokens = tokenize(source)
    ast = parse(tokens)

    filename = os.path.basename(filepath) if filepath else "source"
    out: list[str] = [f"# Module: `{filename}`\n"]

    if isinstance(ast, Block):
        for stmt in ast.statements:
            if isinstance(stmt, Function):
                doc_comment = extract_comments(source, stmt.line)
                params_str = ", ".join(
                    (
                        f"{p}"
                        if i >= len(stmt.defaults) or stmt.defaults[i] is None
                        else f"{p}={format_expr(stmt.defaults[i])}"
                    )
                    for i, p in enumerate(stmt.params)
                )
                out.append(f"## fn `{stmt.name}({params_str})`\n")
                if doc_comment:
                    out.append(f"{doc_comment}\n")
                out.append(f"- **File:** `{filepath}`, line {stmt.line}:{stmt.col}\n")
                out.append("")

            elif isinstance(stmt, ClassDef):
                doc_comment = extract_comments(source, stmt.line)
                parent_str = f" extends {stmt.parent}" if stmt.parent else ""
                out.append(f"## class `{stmt.name}{parent_str}`\n")
                if doc_comment:
                    out.append(f"{doc_comment}\n")
                out.append(f"- **File:** `{filepath}`, line {stmt.line}:{stmt.col}\n")
                if isinstance(stmt.body, Block):
                    for s in stmt.body.statements:
                        if isinstance(s, Function):
                            params_str = ", ".join(
                                (
                                    f"{p}"
                                    if i >= len(s.defaults) or s.defaults[i] is None
                                    else f"{p}={format_expr(s.defaults[i])}"
                                )
                                for i, p in enumerate(s.params)
                            )
                            method_doc = extract_comments(source, s.line)
                            out.append(f"### `{s.name}({params_str})`")
                            if method_doc:
                                out.append(f"\n{method_doc}")
                            out.append("")
                out.append("")

            elif isinstance(stmt, EnumDef):
                doc_comment = extract_comments(source, stmt.line)
                out.append(f"## enum `{stmt.name}`\n")
                if doc_comment:
                    out.append(f"{doc_comment}\n")
                out.append(f"- **File:** `{filepath}`, line {stmt.line}:{stmt.col}\n")
                out.append("### Variants\n")
                for v in stmt.variants:
                    out.append(f"- `{v}`")
                out.append("")

            elif isinstance(stmt, InterfaceDef):
                doc_comment = extract_comments(source, stmt.line)
                out.append(f"## interface `{stmt.name}`\n")
                if doc_comment:
                    out.append(f"{doc_comment}\n")
                out.append(f"- **File:** `{filepath}`, line {stmt.line}:{stmt.col}\n")
                out.append("### Required Methods\n")
                for m in stmt.methods:
                    out.append(f"- `{m}()`")
                out.append("")

    return "\n".join(out) + "\n"


def run(args: list[str]) -> None:
    import sys

    if not args:
        print("Usage: zoya docs <file.zoya> [file2.zoya ...]", file=sys.stderr)
        sys.exit(1)

    for filepath in args:
        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
            docs = generate_docs(source, filepath)
            base = os.path.splitext(os.path.basename(filepath))[0]
            out_path = os.path.join(os.getcwd(), base + ".md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(docs)
            print(f"Generated: {out_path}")
        except Exception as e:
            print(f"Error processing '{filepath}': {e}", file=sys.stderr)
