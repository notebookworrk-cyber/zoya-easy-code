from __future__ import annotations

import re
from dataclasses import dataclass, field

from zoya.ai.llm import LLMProvider, MockProvider

ZOYA_KEYWORDS: list[str] = [
    "let",
    "const",
    "fn",
    "if",
    "else",
    "while",
    "for",
    "in",
    "loop",
    "return",
    "break",
    "continue",
    "print",
    "input",
    "import",
    "from",
    "class",
    "interface",
    "enum",
    "match",
    "switch",
    "case",
    "default",
    "try",
    "catch",
    "throw",
    "true",
    "false",
    "null",
    "and",
    "or",
    "not",
    "this",
    "super",
]

ZOYA_BUILTINS: list[str] = [
    "print",
    "input",
    "len",
    "type",
    "int",
    "float",
    "str",
    "bool",
    "range",
    "abs",
    "round",
    "min",
    "max",
    "random",
    "sleep",
    "list",
    "dict",
    "sum",
    "hex",
    "bin",
]

ZOYA_SNIPPETS: list[dict[str, str]] = [
    {
        "label": "fn",
        "insert": "fn $1($2) {\n    $3\n}",
        "detail": "Function declaration",
    },
    {"label": "if", "insert": "if ($1) {\n    $2\n}", "detail": "If statement"},
    {
        "label": "ifelse",
        "insert": "if ($1) {\n    $2\n} else {\n    $3\n}",
        "detail": "If-else statement",
    },
    {"label": "while", "insert": "while ($1) {\n    $2\n}", "detail": "While loop"},
    {"label": "for", "insert": "for ($1; $2; $3) {\n    $4\n}", "detail": "For loop"},
    {
        "label": "foreach",
        "insert": "for $1 in $2 {\n    $3\n}",
        "detail": "For-each loop",
    },
    {"label": "loop", "insert": "loop $1 {\n    $2\n}", "detail": "Loop statement"},
    {"label": "fnmain", "insert": "fn main() {\n    $1\n}", "detail": "Main function"},
    {"label": "class", "insert": "class $1 {\n    $2\n}", "detail": "Class definition"},
    {
        "label": "interface",
        "insert": "interface $1 {\n    $2\n}",
        "detail": "Interface definition",
    },
    {"label": "enum", "insert": "enum $1 {\n    $2\n}", "detail": "Enum definition"},
    {
        "label": "match",
        "insert": "match $1 {\n    $2 => $3\n}",
        "detail": "Match expression",
    },
    {
        "label": "switch",
        "insert": "switch ($1) {\n    case $2 {\n        $3\n    }\n    default {\n        $4\n    }\n}",
        "detail": "Switch statement",
    },
    {
        "label": "try",
        "insert": "try {\n    $1\n} catch ($2) {\n    $3\n}",
        "detail": "Try-catch block",
    },
    {"label": "import", "insert": 'import "$1"', "detail": "Import statement"},
    {"label": "print", "insert": "print($1)", "detail": "Print statement"},
    {
        "label": "let",
        "insert": "let $1 = $2",
        "detail": "Variable declaration (mutable)",
    },
    {"label": "const", "insert": "const $1 = $2", "detail": "Constant declaration"},
]

STRING_METHODS: list[str] = [
    "upper",
    "lower",
    "strip",
    "replace",
    "split",
    "startswith",
    "endswith",
    "contains",
]
LIST_METHODS: list[str] = [
    "append",
    "remove",
    "pop",
    "clear",
    "insert",
    "sort",
    "reverse",
    "length",
    "copy",
]
DICT_METHODS: list[str] = [
    "keys",
    "values",
    "items",
    "contains",
    "get",
    "copy",
    "clear",
]


@dataclass
class CompletionContext:
    file_path: str
    source: str
    line: int
    col: int
    prefix: str = ""
    scope: list[str] = field(default_factory=list)


@dataclass
class CompletionItem:
    label: str
    kind: str
    detail: str = ""
    insert_text: str = ""
    documentation: str | None = None


class CompletionEngine:
    def __init__(self, provider: LLMProvider | None = None):
        self._provider = provider or MockProvider(
            responses={
                "complete": "suggestion",
            }
        )

    def get_completions(self, context: CompletionContext) -> list[CompletionItem]:
        results: list[CompletionItem] = []
        prefix = context.prefix.strip()

        if not context.prefix and not context.source:
            return results

        stripped = context.prefix.rstrip()
        if stripped and stripped[-1] == ".":
            results.extend(
                self._get_dot_completions(context.source, context.line, context.col)
            )
            return results

        results.extend(self._get_keyword_completions(prefix))
        results.extend(self._get_scope_completions(context.source, context.scope))
        results.extend(self._get_snippet_completions(prefix))

        ai_results = self._get_ai_completions(context)
        existing_labels = {r.label for r in results}
        for item in ai_results:
            if item.label not in existing_labels:
                results.append(item)
                existing_labels.add(item.label)

        if prefix:
            results = [
                r
                for r in results
                if r.label.startswith(prefix)
                or r.label.lower().startswith(prefix.lower())
            ]

        seen: set[str] = set()
        unique: list[CompletionItem] = []
        for item in results:
            if item.label not in seen:
                seen.add(item.label)
                unique.append(item)

        return unique

    def _get_keyword_completions(self, prefix: str) -> list[CompletionItem]:
        results: list[CompletionItem] = []
        for kw in ZOYA_KEYWORDS:
            if not prefix or kw.startswith(prefix):
                results.append(
                    CompletionItem(
                        label=kw,
                        kind="keyword",
                        detail="Zoya keyword",
                        insert_text=kw,
                    )
                )
        for b in ZOYA_BUILTINS:
            if not prefix or b.startswith(prefix):
                results.append(
                    CompletionItem(
                        label=b,
                        kind="function",
                        detail="Built-in function",
                        insert_text=b,
                    )
                )
        return results

    def _get_snippet_completions(self, prefix: str) -> list[CompletionItem]:
        results: list[CompletionItem] = []
        for snippet in ZOYA_SNIPPETS:
            if not prefix or snippet["label"].startswith(prefix):
                results.append(
                    CompletionItem(
                        label=snippet["label"],
                        kind="snippet",
                        detail=snippet["detail"],
                        insert_text=snippet["insert"],
                    )
                )
        return results

    def _get_scope_completions(
        self, source: str, scope: list[str]
    ) -> list[CompletionItem]:
        variables = self._parse_source_variables(source)
        results: list[CompletionItem] = []
        for name, kind in variables.items():
            results.append(
                CompletionItem(
                    label=name,
                    kind=kind,
                    detail="Defined in current scope",
                    insert_text=name,
                )
            )
        return results

    def _get_dot_completions(
        self, source: str, line: int, col: int
    ) -> list[CompletionItem]:
        results: list[CompletionItem] = []
        lines = source.splitlines()
        if line - 1 >= len(lines):
            return results

        current_line = lines[line - 1]
        before_dot = current_line[: col - 1].rstrip()

        obj_match = re.search(r"(\w+)\s*\.\s*$", before_dot)
        if not obj_match:
            return results

        obj_name = obj_match.group(1)
        variables = self._parse_source_variables(source)
        var_type = variables.get(obj_name, "")

        methods: list[str] = []
        if var_type == "string":
            methods = STRING_METHODS
        elif var_type == "list":
            methods = LIST_METHODS
        elif var_type == "dict":
            methods = DICT_METHODS
        elif var_type in ("int", "float", "number") or var_type == "class":
            methods = []
        else:
            methods = list(set(STRING_METHODS + LIST_METHODS + DICT_METHODS))

        for method in methods:
            results.append(
                CompletionItem(
                    label=method,
                    kind="method",
                    detail=f"Method of {var_type or 'unknown'}",
                    insert_text=method,
                )
            )

        if not var_type:
            results.append(
                CompletionItem(
                    label="length",
                    kind="property",
                    detail="Collection length property",
                    insert_text="length",
                )
            )

        return results

    def _get_ai_completions(self, context: CompletionContext) -> list[CompletionItem]:
        try:
            lines = context.source.splitlines()
            surrounding = []
            start = max(0, context.line - 6)
            end = min(len(lines), context.line + 2)
            for i in range(start, end):
                prefix = ">" if i == context.line - 1 else " "
                surrounding.append(f"{prefix} {lines[i]}")

            source_context = "\n".join(surrounding)
            prompt = (
                "You are completing Zoya code at the cursor position marked by <CURSOR>.\n"
                "Respond with a JSON array of completion suggestions, each with 'label', 'kind', and 'detail'.\n"
                "Only return the JSON array, nothing else.\n\n"
                f"Code context:\n{source_context}\n\n"
                f"Current scope: {' -> '.join(context.scope) if context.scope else 'global'}\n"
                f"Prefix: '{context.prefix}'\n"
            )
            response = self._provider.chat(
                [
                    {
                        "role": "system",
                        "content": "You are a Zoya code completion engine. Return only JSON arrays.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            content = response.get("content", "")
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0]

            import json

            suggestions = json.loads(content)
            results: list[CompletionItem] = []
            for s in suggestions:
                results.append(
                    CompletionItem(
                        label=s.get("label", ""),
                        kind=s.get("kind", "snippet"),
                        detail=s.get("detail", ""),
                        insert_text=s.get("insert_text", s.get("label", "")),
                    )
                )
            return results
        except Exception:
            return []

    def _parse_source_variables(self, source: str) -> dict[str, str]:
        variables: dict[str, str] = {}

        let_matches = re.finditer(
            r"(?:^|\n)\s*(let|const)\s+(\w+)\s*=\s*([^;\n]+)",
            source,
        )
        for m in let_matches:
            name = m.group(2)
            val = m.group(3).strip()
            var_type = self._infer_type(val)
            variables[name] = var_type

        fn_matches = re.finditer(
            r"(?:^|\n)\s*fn\s+(\w+)\s*\(([^)]*)\)",
            source,
        )
        for m in fn_matches:
            variables[m.group(1)] = "function"

        class_matches = re.finditer(
            r"(?:^|\n)\s*class\s+(\w+)",
            source,
        )
        for m in class_matches:
            variables[m.group(1)] = "class"

        param_matches = re.finditer(
            r"fn\s+\w+\s*\(([^)]*)\)",
            source,
        )
        for m in param_matches:
            params_str = m.group(1)
            if params_str.strip():
                for param in params_str.split(","):
                    param = param.strip()
                    if param:
                        variables[param] = "variable"

        for_loop_matches = re.finditer(
            r"for\s+(\w+)\s+in\s+",
            source,
        )
        for m in for_loop_matches:
            variables[m.group(1)] = "variable"

        catch_matches = re.finditer(
            r"catch\s+\((\w+)\)",
            source,
        )
        for m in catch_matches:
            variables[m.group(1)] = "variable"

        return variables

    @staticmethod
    def _infer_type(value: str) -> str:
        if not value:
            return "variable"
        if value.startswith('"') or value.startswith("'") or value.startswith('"'):
            return "string"
        if re.match(r"^-?\d+\.\d+$", value):
            return "float"
        if re.match(r"^-?\d+$", value):
            return "int"
        if value in ("true", "false"):
            return "bool"
        if value == "null":
            return "null"
        if value.startswith("[") or value.startswith("list("):
            return "list"
        if value.startswith("{") or value.startswith("dict("):
            return "dict"
        if value.startswith("fn ") or value.startswith("function"):
            return "function"
        return "variable"
