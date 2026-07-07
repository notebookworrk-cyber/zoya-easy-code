"""Abstract syntax tree node definitions for the Zoya language."""

from __future__ import annotations

from dataclasses import dataclass, field


class ASTNode:
    """Base class for all AST node types."""

    line: int = 0
    col: int = 0


@dataclass
class Number(ASTNode):
    """AST node for numeric literals (integer or float)."""

    value: int | float
    line: int = 0
    col: int = 0


@dataclass
class String(ASTNode):
    """AST node for string literals."""

    value: str
    line: int = 0
    col: int = 0


@dataclass
class Boolean(ASTNode):
    """AST node for boolean literals (true/false)."""

    value: bool
    line: int = 0
    col: int = 0


@dataclass
class Ident(ASTNode):
    """AST node for variable and identifier references."""

    name: str
    line: int = 0
    col: int = 0


@dataclass
class Assign(ASTNode):
    """AST node for variable assignment expressions."""

    name: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class AugAssign(ASTNode):
    """AST node for augmented assignment operators (+=, -=, etc.)."""

    name: str
    op: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class BinOp(ASTNode):
    """AST node for binary operations (+, -, *, /, etc.)."""

    op: str
    left: ASTNode
    right: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class UnaryOp(ASTNode):
    """AST node for unary operations (not, negation)."""

    op: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Print(ASTNode):
    """AST node for print statements."""

    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Input(ASTNode):
    """AST node for input statements."""

    prompt: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class If(ASTNode):
    """AST node for conditional if/else statements."""

    cond: ASTNode
    body: ASTNode
    else_body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class While(ASTNode):
    """AST node for while loop statements."""

    cond: ASTNode
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Loop(ASTNode):
    """AST node for counted loop statements."""

    count: ASTNode
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Break(ASTNode):
    """AST node for break statements."""

    line: int = 0
    col: int = 0


@dataclass
class Continue(ASTNode):
    """AST node for continue statements."""

    line: int = 0
    col: int = 0


@dataclass
class Pass(ASTNode):
    """AST node for pass/no-op statements."""

    line: int = 0
    col: int = 0


@dataclass
class Block(ASTNode):
    """AST node for a block of statements."""

    statements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Function(ASTNode):
    """AST node for function definitions."""

    name: str
    params: list[str]
    body: ASTNode
    defaults: list[ASTNode | None] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Lambda(ASTNode):
    """AST node for anonymous function (lambda) expressions."""

    params: list[str]
    body: ASTNode
    defaults: list[ASTNode | None] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Call(ASTNode):
    """AST node for function and method call expressions."""

    callee: ASTNode
    args: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class NamedArg(ASTNode):
    """AST node for named arguments in function calls."""

    name: str
    value: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Return(ASTNode):
    """AST node for return statements."""

    expr: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class List_(ASTNode):
    """AST node for list literal expressions."""

    elements: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Dict_(ASTNode):
    """AST node for dictionary literal expressions."""

    pairs: list[tuple[ASTNode, ASTNode]] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Index(ASTNode):
    """AST node for indexing access expressions (obj[index])."""

    obj: ASTNode
    index: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class AssignIndex(ASTNode):
    """AST node for indexed assignment expressions."""

    obj: ASTNode
    index: ASTNode
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class AssignAttr(ASTNode):
    """AST node for attribute assignment expressions."""

    obj: ASTNode
    attr: str
    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class GetAttr(ASTNode):
    """AST node for attribute access expressions."""

    obj: ASTNode
    attr: str
    line: int = 0
    col: int = 0


@dataclass
class MethodCall(ASTNode):
    """AST node for method call expressions."""

    obj: ASTNode
    method: str
    args: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0


@dataclass
class Import(ASTNode):
    """AST node for import statements."""

    path: str
    alias: str | None = None
    line: int = 0
    col: int = 0


@dataclass
class InterpolatedString(ASTNode):
    """AST node for interpolated string expressions."""

    parts: list[str | ASTNode]
    line: int = 0
    col: int = 0


@dataclass
class Slice(ASTNode):
    """AST node for slice expressions (obj[start:stop:step])."""

    obj: ASTNode
    start: ASTNode | None = None
    stop: ASTNode | None = None
    step: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class ForLoop(ASTNode):
    """AST node for C-style for loop statements."""

    init: ASTNode | None
    cond: ASTNode | None
    update: ASTNode | None
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class ForEach(ASTNode):
    """AST node for for-each loop statements."""

    var: str
    iterable: ASTNode
    body: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Switch(ASTNode):
    """AST node for switch/case statements."""

    expr: ASTNode
    cases: list[tuple[ASTNode, ASTNode]]
    default_body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class Try(ASTNode):
    """AST node for try/catch/finally statements."""

    try_body: ASTNode
    catches: list[Catch] = field(default_factory=list)
    final_body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class Catch(ASTNode):
    """AST node for catch clauses in try statements."""

    var: str | None = None
    body: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class Throw(ASTNode):
    """AST node for throw/raise statements."""

    expr: ASTNode
    line: int = 0
    col: int = 0


@dataclass
class Match(ASTNode):
    """AST node for match/pattern matching expressions."""

    expr: ASTNode
    arms: list[tuple[ASTNode, ASTNode]]
    else_arm: ASTNode | None = None
    line: int = 0
    col: int = 0


@dataclass
class EnumDef(ASTNode):
    """AST node for enum type definitions."""

    name: str
    variants: list[str]
    line: int = 0
    col: int = 0


@dataclass
class ClassDef(ASTNode):
    """AST node for class definitions."""

    name: str
    parent: str | None = None
    body: ASTNode = None
    line: int = 0
    col: int = 0


@dataclass
class InterfaceDef(ASTNode):
    """AST node for interface definitions."""

    name: str
    methods: list[str]
    line: int = 0
    col: int = 0
