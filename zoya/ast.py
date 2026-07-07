"""Abstract syntax tree node definitions for the Zoya language."""

from __future__ import annotations

from dataclasses import dataclass, field


class ASTNode:
    line: int = 0
    col: int = 0


@dataclass
class Number(ASTNode):
    value: int | float
    line: int = 0
    col: int = 0


@dataclass
class String(ASTNode):
    value: str
    line: int = 0
    col: int = 0


@dataclass
class Boolean(ASTNode):
    value: bool
    line: int = 0
    col: int = 0


@dataclass
class Ident(ASTNode):
    name: str
    line: int = 0
    col: int = 0


@dataclass
class Assign(ASTNode):
    name: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class UnaryOp(ASTNode):
    op: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Print(ASTNode):
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Input(ASTNode):
    prompt: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class If(ASTNode):
    cond: ASTNode
    body: ASTNode
    else_body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class While(ASTNode):
    cond: ASTNode
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Loop(ASTNode):
    count: ASTNode
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Break(ASTNode):
    line: int = 0
    col: int = 0


@dataclass
class Continue(ASTNode):
    line: int = 0
    col: int = 0


@dataclass
class Pass(ASTNode):
    line: int = 0
    col: int = 0


@dataclass
class Block(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Function(ASTNode):
    name: str
    params: list[str]
    body: ASTNode
    defaults: list[ASTNode | None] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Lambda(ASTNode):
    params: list[str]
    body: ASTNode
    defaults: list[ASTNode | None] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Call(ASTNode):
    callee: ASTNode
    args: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class NamedArg(ASTNode):
    name: str
    value: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Return(ASTNode):
    expr: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class List_(ASTNode):
    elements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Dict_(ASTNode):
    pairs: list[tuple[ASTNode, ASTNode]] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Index(ASTNode):
    obj: ASTNode
    index: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class AssignIndex(ASTNode):
    obj: ASTNode
    index: ASTNode
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class AssignAttr(ASTNode):
    obj: ASTNode
    attr: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class GetAttr(ASTNode):
    obj: ASTNode
    attr: str
    line: int = 0
    col: int = 0


@dataclass
class MethodCall(ASTNode):
    obj: ASTNode
    method: str
    args: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Import(ASTNode):
    path: str
    alias: str | None = None
    line: int = 0
    col: int = 0


@dataclass
class InterpolatedString(ASTNode):
    parts: list[str | ASTNode]
    line: int = 0
    col: int = 0


@dataclass
class Slice(ASTNode):
    obj: ASTNode
    start: ASTNode | None = None
    stop: ASTNode | None = None
    step: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class ForLoop(ASTNode):
    init: ASTNode | None
    cond: ASTNode | None
    update: ASTNode | None
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class ForEach(ASTNode):
    var: str
    iterable: ASTNode
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Switch(ASTNode):
    expr: ASTNode
    cases: list[tuple[ASTNode, ASTNode]]
    default_body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class Try(ASTNode):
    try_body: ASTNode
    catches: list[Catch] = field(default_factory=list)
    final_body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class Catch(ASTNode):
    var: str | None = None
    body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class Throw(ASTNode):
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Match(ASTNode):
    expr: ASTNode
    arms: list[tuple[ASTNode, ASTNode]]
    else_arm: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class EnumDef(ASTNode):
    name: str
    variants: list[str]
    line: int = 0
    col: int = 0


@dataclass
class ClassDef(ASTNode):
    name: str
    parent: str | None = None
    body: ASTNode = None
    line: int = 0
    col: int = 0


@dataclass
class InterfaceDef(ASTNode):
    name: str
    methods: list[str]
    line: int = 0
    col: int = 0
