from __future__ import annotations

from typing import Optional

from .ast import (
    ASTNode,
    Assign,
    AssignAttr,
    AssignIndex,
    BinOp,
    Block,
    Boolean,
    Break,
    Call,
    Continue,
    Dict_,
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
from .errors import ParseError
from .lexer import Token


class Parser:
    def __init__(self, tokens: list[Token], file: str = "") -> None:
        self.tokens = tokens
        self.pos = 0
        self.file = file

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, kind: Optional[str] = None) -> Token:
        tok = self.peek()
        if kind is not None and tok.kind != kind:
            raise ParseError(
                f"Expected '{kind}', got '{tok.kind}'",
                line=tok.line,
                col=tok.col,
                file=self.file,
            )
        self.pos += 1
        return tok

    def check(self, kind: str) -> bool:
        return self.peek().kind == kind

    def parse(self) -> Block:
        statements: list[ASTNode] = []
        while self.peek().kind != "EOF":
            stmt = self.parse_stmt()
            if stmt is not None:
                statements.append(stmt)
        return Block(statements)

    def parse_stmt(self) -> Optional[ASTNode]:
        tok = self.peek()
        kind = tok.kind

        if kind == "NEWLINE":
            self.consume("NEWLINE")
            return None
        if kind == "EOF":
            return None
        if kind == "FN":
            return self.parse_fn_def()
        if kind == "RETURN":
            return self.parse_return()
        if kind == "IF":
            return self.parse_if()
        if kind == "WHILE":
            return self.parse_while()
        if kind == "LOOP":
            return self.parse_loop()
        if kind == "BREAK":
            return self.parse_break()
        if kind == "CONTINUE":
            return self.parse_continue()
        if kind == "IMPORT":
            return self.parse_import()
        if kind == "LBRACE":
            return self.parse_block()

        return self.parse_assign_or_expr()

    def parse_fn_def(self) -> Function:
        tok = self.consume("FN")
        name_tok = self.consume("IDENT")
        self.consume("LPAREN")
        params: list[str] = []
        if self.peek().kind != "RPAREN":
            params.append(self.consume("IDENT").value)
            while self.check("COMMA"):
                self.consume("COMMA")
                params.append(self.consume("IDENT").value)
        self.consume("RPAREN")
        self.skip_newlines()
        body = self.parse_block()
        return Function(
            name=name_tok.value,
            params=params,
            body=body,
        )

    def parse_return(self) -> Return:
        tok = self.consume("RETURN")
        if self.peek().kind in ("NEWLINE", "RBRACE", "EOF"):
            return Return(expr=None, line=tok.line, col=tok.col)
        expr = self.parse_expr()
        self.expect_newline()
        return Return(expr=expr, line=tok.line, col=tok.col)

    def parse_if(self) -> If:
        tok = self.consume("IF")
        cond = self.parse_expr()
        self.skip_newlines()
        body = self.parse_block()
        else_body: Optional[Block] = None
        if self.check("ELSE"):
            self.consume("ELSE")
            self.skip_newlines()
            if self.check("IF"):
                single = self.parse_if()
                else_body = Block([single])
            else:
                else_body = self.parse_block()
        return If(cond=cond, body=body, else_body=else_body, line=tok.line, col=tok.col)

    def parse_while(self) -> While:
        tok = self.consume("WHILE")
        cond = self.parse_expr()
        self.skip_newlines()
        body = self.parse_block()
        return While(cond=cond, body=body, line=tok.line, col=tok.col)

    def parse_loop(self) -> Loop:
        tok = self.consume("LOOP")
        count = self.parse_expr()
        self.skip_newlines()
        body = self.parse_block()
        return Loop(count=count, body=body, line=tok.line, col=tok.col)

    def parse_break(self) -> Break:
        tok = self.consume("BREAK")
        self.expect_newline()
        return Break(line=tok.line, col=tok.col)

    def parse_continue(self) -> Continue:
        tok = self.consume("CONTINUE")
        self.expect_newline()
        return Continue(line=tok.line, col=tok.col)

    def parse_import(self) -> Import:
        tok = self.consume("IMPORT")
        path_tok = self.consume("STRING")
        path = path_tok.value
        alias: Optional[str] = None
        if self.check("IDENT") and self.peek().value == "as":
            self.consume("IDENT")
            alias = self.consume("IDENT").value
        self.expect_newline()
        return Import(path=path, alias=alias, line=tok.line, col=tok.col)

    def parse_block(self) -> Block:
        self.consume("LBRACE")
        statements: list[ASTNode] = []
        while self.peek().kind not in ("RBRACE", "EOF"):
            stmt = self.parse_stmt()
            if stmt is not None:
                statements.append(stmt)
        self.consume("RBRACE")
        return Block(statements)

    def parse_assign_or_expr(self) -> ASTNode:
        if (self.check("IDENT")
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].kind == "ASSIGN"):
            tok = self.consume("IDENT")
            self.consume("ASSIGN")
            expr = self.parse_expr()
            self.expect_newline()
            return Assign(name=tok.value, expr=expr, line=tok.line, col=tok.col)

        expr = self.parse_expr()
        if isinstance(expr, Ident) and self.check("ASSIGN"):
            self.consume("ASSIGN")
            value = self.parse_expr()
            self.expect_newline()
            return Assign(name=expr.name, expr=value, line=expr.line, col=expr.col)

        if (isinstance(expr, Index) and self.check("ASSIGN")):
            self.consume("ASSIGN")
            value = self.parse_expr()
            self.expect_newline()
            return AssignIndex(obj=expr.obj, index=expr.index, expr=value, line=expr.line, col=expr.col)

        if (isinstance(expr, GetAttr) and self.check("ASSIGN")):
            self.consume("ASSIGN")
            value = self.parse_expr()
            self.expect_newline()
            from .ast import AssignAttr
            return AssignAttr(obj=expr.obj, attr=expr.attr, expr=value, line=expr.line, col=expr.col)

        if (isinstance(expr, Ident) and expr.name == "print"):
            val = self.parse_expr()
            self.expect_newline()
            return Print(expr=val, line=expr.line, col=expr.col)

        if (isinstance(expr, Ident) and expr.name == "input"):
            prompt: Optional[ASTNode] = None
            if self.check("STRING") or self.check("INTERP_STRING"):
                prompt = String(self.consume().value)
            self.expect_newline()
            return Input(prompt=prompt, line=expr.line, col=expr.col)

        self.expect_newline()
        return expr

    def parse_expr(self) -> ASTNode:
        return self.parse_logical_or()

    def parse_logical_or(self) -> ASTNode:
        left = self.parse_logical_and()
        while self.check("OR"):
            tok = self.consume()
            right = self.parse_logical_and()
            left = BinOp(op="OR", left=left, right=right, line=tok.line, col=tok.col)
        return left

    def parse_logical_and(self) -> ASTNode:
        left = self.parse_comparison()
        while self.check("AND"):
            tok = self.consume()
            right = self.parse_comparison()
            left = BinOp(op="AND", left=left, right=right, line=tok.line, col=tok.col)
        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_term()
        while self.peek().kind in ("EQ", "NE", "GT", "LT", "GTE", "LTE", "IN"):
            tok = self.consume()
            right = self.parse_term()
            left = BinOp(op=tok.kind, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def parse_term(self) -> ASTNode:
        left = self.parse_factor()
        while self.peek().kind in ("PLUS", "MINUS"):
            tok = self.consume()
            right = self.parse_factor()
            op = "PLUS" if tok.kind == "PLUS" else "MINUS"
            left = BinOp(op=op, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def parse_factor(self) -> ASTNode:
        left = self.parse_power()
        while self.peek().kind in ("MUL", "DIV", "MOD"):
            tok = self.consume()
            right = self.parse_power()
            left = BinOp(op=tok.kind, left=left, right=right, line=tok.line, col=tok.col)
        return left

    def parse_power(self) -> ASTNode:
        left = self.parse_unary()
        if self.check("POW"):
            tok = self.consume()
            right = self.parse_unary()
            left = BinOp(op="POW", left=left, right=right, line=tok.line, col=tok.col)
        return left

    def parse_unary(self) -> ASTNode:
        tok = self.peek()
        if tok.kind in ("NOT", "MINUS"):
            self.consume()
            expr = self.parse_unary()
            return UnaryOp(op=tok.kind, expr=expr, line=tok.line, col=tok.col)
        return self.parse_call()

    def parse_call(self) -> ASTNode:
        expr = self.parse_primary()
        while True:
            if self.check("LPAREN"):
                self.consume("LPAREN")
                args: list[ASTNode] = []
                if self.peek().kind != "RPAREN":
                    args.append(self.parse_expr())
                    while self.check("COMMA"):
                        self.consume("COMMA")
                        args.append(self.parse_expr())
                self.consume("RPAREN")
                expr = Call(callee=expr, args=args, line=expr.line, col=expr.col)
            elif self.check("DOT"):
                self.consume("DOT")
                attr = self.consume("IDENT").value
                if self.check("LPAREN"):
                    self.consume("LPAREN")
                    method_args: list[ASTNode] = []
                    if self.peek().kind != "RPAREN":
                        method_args.append(self.parse_expr())
                        while self.check("COMMA"):
                            self.consume("COMMA")
                            method_args.append(self.parse_expr())
                    self.consume("RPAREN")
                    expr = MethodCall(obj=expr, method=attr, args=method_args, line=expr.line, col=expr.col)
                else:
                    expr = GetAttr(obj=expr, attr=attr, line=expr.line, col=expr.col)
            elif self.check("LBRACKET"):
                self.consume("LBRACKET")
                if self.check("COLON"):
                    start: Optional[ASTNode] = None
                    self.consume("COLON")
                    stop: Optional[ASTNode] = None
                    step: Optional[ASTNode] = None
                    if self.peek().kind != "RBRACKET":
                        stop = self.parse_expr()
                        if self.check("COLON"):
                            self.consume("COLON")
                            step = self.parse_expr()
                    self.consume("RBRACKET")
                    expr = Slice(obj=expr, start=start, stop=stop, step=step, line=expr.line, col=expr.col)
                else:
                    index = self.parse_expr()
                    if self.check("COLON"):
                        self.consume("COLON")
                        stop = self.parse_expr()
                        step: Optional[ASTNode] = None
                        if self.check("COLON"):
                            self.consume("COLON")
                            step = self.parse_expr()
                        self.consume("RBRACKET")
                        expr = Slice(obj=expr, start=index, stop=stop, step=step, line=expr.line, col=expr.col)
                    else:
                        self.consume("RBRACKET")
                        expr = Index(obj=expr, index=index, line=expr.line, col=expr.col)
            else:
                break
        return expr

    def parse_primary(self) -> ASTNode:
        tok = self.peek()

        if tok.kind == "NUMBER":
            self.consume()
            value: int | float = float(tok.value) if "." in tok.value else int(tok.value)
            return Number(value=value, line=tok.line, col=tok.col)
        if tok.kind == "STRING":
            self.consume()
            return String(value=tok.value, line=tok.line, col=tok.col)
        if tok.kind == "INTERP_STRING":
            self.consume()
            parts: list[str | ASTNode] = []
            current: list[str] = []
            i = 0
            text = tok.value
            while i < len(text):
                if text[i] == "{" and i + 1 < len(text) and text[i + 1] != "{":
                    if current:
                        parts.append("".join(current))
                        current = []
                    depth = 1
                    j = i + 1
                    while j < len(text) and depth > 0:
                        if text[j] == "{":
                            depth += 1
                        elif text[j] == "}":
                            depth -= 1
                        j += 1
                    expr_text = text[i + 1 : j - 1]
                    format_spec = ""
                    if ":" in expr_text and not expr_text.startswith(":"):
                        colon_depth = 0
                        for idx, ch in enumerate(expr_text):
                            if ch in ("(", "[", "{"):
                                colon_depth += 1
                            elif ch in (")", "]", "}"):
                                colon_depth -= 1
                            elif ch == ":" and colon_depth == 0:
                                format_spec = expr_text[idx + 1:]
                                expr_text = expr_text[:idx]
                                break
                    expr_tokens = __import__("zoya.lexer", fromlist=["tokenize"]).tokenize(expr_text)
                    expr_ast = Parser(expr_tokens).parse()
                    if expr_ast.statements:
                        parts.append(expr_ast.statements[0])
                    if format_spec:
                        if parts and isinstance(parts[-1], tuple):
                            parts[-1] = (parts[-1][0], parts[-1][1] + format_spec)
                        elif parts and not isinstance(parts[-1], str):
                            parts[-1] = (parts[-1], format_spec)
                    i = j
                else:
                    current.append(text[i])
                    i += 1
            if current:
                parts.append("".join(current))
            return InterpolatedString(parts=parts, line=tok.line, col=tok.col)
        if tok.kind == "TRUE":
            self.consume()
            return Boolean(value=True, line=tok.line, col=tok.col)
        if tok.kind == "FALSE":
            self.consume()
            return Boolean(value=False, line=tok.line, col=tok.col)
        if tok.kind == "IDENT":
            self.consume()
            return Ident(name=tok.value, line=tok.line, col=tok.col)
        if tok.kind == "LPAREN":
            self.consume()
            expr = self.parse_expr()
            self.consume("RPAREN")
            return expr
        if tok.kind == "LBRACKET":
            self.consume()
            self.skip_newlines()
            elements: list[ASTNode] = []
            if self.peek().kind != "RBRACKET":
                elements.append(self.parse_expr())
                self.skip_newlines()
                while self.check("COMMA"):
                    self.consume("COMMA")
                    self.skip_newlines()
                    elements.append(self.parse_expr())
                    self.skip_newlines()
            self.consume("RBRACKET")
            return List_(elements=elements, line=tok.line, col=tok.col)
        if tok.kind == "LBRACE":
            self.consume()
            self.skip_newlines()
            pairs: list[tuple[ASTNode, ASTNode]] = []
            if self.peek().kind != "RBRACE":
                key = self.parse_expr()
                self.skip_newlines()
                self.consume("COLON")
                self.skip_newlines()
                value = self.parse_expr()
                self.skip_newlines()
                pairs.append((key, value))
                while self.check("COMMA"):
                    self.consume("COMMA")
                    self.skip_newlines()
                    key = self.parse_expr()
                    self.skip_newlines()
                    self.consume("COLON")
                    self.skip_newlines()
                    value = self.parse_expr()
                    self.skip_newlines()
                    pairs.append((key, value))
            self.consume("RBRACE")
            return Dict_(pairs=pairs, line=tok.line, col=tok.col)

        raise ParseError(
            f"Unexpected token '{tok.kind}' ({tok.value!r})",
            line=tok.line,
            col=tok.col,
            file=self.file,
        )

    def skip_newlines(self) -> None:
        while self.check("NEWLINE"):
            self.consume()

    def expect_newline(self) -> None:
        if self.check("NEWLINE"):
            self.consume()
        elif self.check("EOF"):
            pass
        else:
            raise ParseError(
                f"Expected newline after statement",
                line=self.peek().line,
                col=self.peek().col,
                file=self.file,
            )


def parse(tokens: list[Token], file: str = "") -> Block:
    return Parser(tokens, file).parse()
