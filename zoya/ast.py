from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


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
    prompt: Optional[ASTNode] = None
    line: int = 0
    col: int = 0


@dataclass
class If(ASTNode):
    cond: ASTNode
    body: ASTNode
    else_body: Optional[ASTNode] = None
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
class Block(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Function(ASTNode):
    name: str
    params: list[str]
    body: ASTNode
    defaults: list[Optional[ASTNode]] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Lambda(ASTNode):
    params: list[str]
    body: ASTNode
    defaults: list[Optional[ASTNode]] = field(default_factory=list)
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
    expr: Optional[ASTNode] = None
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
    alias: Optional[str] = None
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
    start: Optional[ASTNode] = None
    stop: Optional[ASTNode] = None
    step: Optional[ASTNode] = None
    line: int = 0
    col: int = 0


@dataclass
class ForLoop(ASTNode):
    init: Optional[ASTNode]
    cond: Optional[ASTNode]
    update: Optional[ASTNode]
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
    default_body: Optional[ASTNode] = None
    line: int = 0
    col: int = 0


@dataclass
class Try(ASTNode):
    try_body: ASTNode
    catches: list[Catch] = field(default_factory=list)
    final_body: Optional[ASTNode] = None
    line: int = 0
    col: int = 0


@dataclass
class Catch(ASTNode):
    var: Optional[str] = None
    body: Optional[ASTNode] = None
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
    else_arm: Optional[ASTNode] = None
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
    parent: Optional[str] = None
    body: ASTNode = None
    line: int = 0
    col: int = 0


@dataclass
class InterfaceDef(ASTNode):
    name: str
    methods: list[str]
    line: int = 0
    col: int = 0
