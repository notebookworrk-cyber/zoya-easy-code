from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int


TOKEN_SPEC: list[tuple[str, str]] = [
    ("COMMENT", r"//[^\n]*|#[^\n]*"),
    ("MULTI_COMMENT", r"/\*[\s\S]*?\*/"),
    ("NUMBER", r"\d+(\.\d+)?"),
    ("STRING", r'"[^"]*"'),
    ("STRING2", r"'[^']*'"),
    ("INTERP_STRING", r'f"[^"]*"'),
    ("ARROW", r"->"),
    ("DOUBLE_COLON", r"::"),
    ("IDENT", r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("FN", r"\bfn\b"),
    ("RETURN", r"\breturn\b"),
    ("IF", r"\bif\b"),
    ("ELSE", r"\belse\b"),
    ("WHILE", r"\bwhile\b"),
    ("LOOP", r"\bloop\b"),
    ("FOR", r"\bfor\b"),
    ("BREAK", r"\bbreak\b"),
    ("CONTINUE", r"\bcontinue\b"),
    ("IMPORT", r"\bimport\b"),
    ("SWITCH", r"\bswitch\b"),
    ("CASE", r"\bcase\b"),
    ("DEFAULT", r"\bdefault\b"),
    ("TRY", r"\btry\b"),
    ("CATCH", r"\bcatch\b"),
    ("FINALLY", r"\bfinally\b"),
    ("THROW", r"\bthrow\b"),
    ("MATCH", r"\bmatch\b"),
    ("ENUM", r"\benum\b"),
    ("CLASS", r"\bclass\b"),
    ("INTERFACE", r"\binterface\b"),
    ("EXTENDS", r"\bextends\b"),
    ("IMPLEMENTS", r"\bimplements\b"),
    ("ABSTRACT", r"\babstract\b"),
    ("STATIC", r"\bstatic\b"),
    ("NEW", r"\bnew\b"),
    ("THIS", r"\bthis\b"),
    ("SUPER", r"\bsuper\b"),
    ("LAMBDA", r"\blambda\b"),
    ("ASYNC", r"\basync\b"),
    ("AWAIT", r"\bawait\b"),
    ("AND", r"\band\b"),
    ("OR", r"\bor\b"),
    ("NOT", r"\bnot\b"),
    ("TRUE", r"\btrue\b"),
    ("FALSE", r"\bfalse\b"),
    ("IN", r"\bin\b"),
    ("POW", r"\*\*"),
    ("EQ", r"=="),
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MUL", r"\*"),
    ("DIV", r"/"),
    ("MOD", r"%"),
    ("GTE", r">="),
    ("LTE", r"<="),
    ("NE", r"!="),
    ("GT", r">"),
    ("LT", r"<"),
    ("DOT", r"\."),
    ("COMMA", r","),
    ("COLON", r":"),
    ("SEMICOLON", r";"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t]+"),
    ("MISMATCH", r"."),
]

TOKEN_RE = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
)

KEYWORD_TOKENS: dict[str, str] = {
    "fn": "FN",
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "loop": "LOOP",
    "for": "FOR",
    "foreach": "FOREACH",
    "break": "BREAK",
    "continue": "CONTINUE",
    "import": "IMPORT",
    "switch": "SWITCH",
    "case": "CASE",
    "default": "DEFAULT",
    "try": "TRY",
    "catch": "CATCH",
    "finally": "FINALLY",
    "throw": "THROW",
    "match": "MATCH",
    "enum": "ENUM",
    "class": "CLASS",
    "interface": "INTERFACE",
    "extends": "EXTENDS",
    "implements": "IMPLEMENTS",
    "abstract": "ABSTRACT",
    "static": "STATIC",
    "new": "NEW",
    "this": "THIS",
    "super": "SUPER",
    "lambda": "LAMBDA",
    "async": "ASYNC",
    "await": "AWAIT",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "true": "TRUE",
    "false": "FALSE",
    "in": "IN",
}


def tokenize(source: str, file: str = "") -> list[Token]:
    tokens: list[Token] = []
    line = 1
    col = 1

    for m in TOKEN_RE.finditer(source):
        kind = m.lastgroup
        value = m.group()

        if not kind:
            continue

        if kind == "NEWLINE":
            tokens.append(Token("NEWLINE", "\n", line, col))
            line += 1
            col = 1
        elif kind in ("SKIP", "COMMENT", "MULTI_COMMENT"):
            if kind == "COMMENT":
                col += len(value)
            elif kind == "MULTI_COMMENT":
                col += len(value.rsplit("\n")[-1])
                line += value.count("\n")
            else:
                col += len(value)
        elif kind in ("STRING", "STRING2"):
            tokens.append(Token("STRING", value[1:-1], line, col))
            col += len(value)
        elif kind == "INTERP_STRING":
            tokens.append(Token("INTERP_STRING", value[2:-1], line, col))
            col += len(value)
        elif kind == "IDENT":
            kind = KEYWORD_TOKENS.get(value, "IDENT")
            tokens.append(Token(kind, value, line, col))
            col += len(value)
        else:
            tokens.append(Token(kind, value, line, col))
            col += len(value)

    tokens.append(Token("EOF", "", line, col))
    return tokens
