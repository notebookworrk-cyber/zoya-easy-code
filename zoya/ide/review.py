from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from zoya.ai.llm import LLMProvider, MockProvider

REVIEW_RULES: dict[str, dict[str, str]] = {
    "S001": {
        "id": "S001",
        "description": "Function names should use snake_case",
        "category": "style",
        "severity": "warning",
    },
    "S002": {
        "id": "S002",
        "description": "Constants should use UPPER_CASE naming",
        "category": "style",
        "severity": "info",
    },
    "S003": {
        "id": "S003",
        "description": "Line exceeds 100 characters",
        "category": "style",
        "severity": "warning",
    },
    "C001": {
        "id": "C001",
        "description": "Unused variable or parameter",
        "category": "correctness",
        "severity": "warning",
    },
    "C002": {
        "id": "C002",
        "description": "Function missing return type annotation",
        "category": "correctness",
        "severity": "info",
    },
    "C003": {
        "id": "C003",
        "description": "Deep nesting exceeds 4 levels",
        "category": "correctness",
        "severity": "warning",
    },
    "C004": {
        "id": "C004",
        "description": "Duplicate function name",
        "category": "correctness",
        "severity": "error",
    },
    "C005": {
        "id": "C005",
        "description": "Empty catch block",
        "category": "correctness",
        "severity": "error",
    },
    "B001": {
        "id": "B001",
        "description": "Hardcoded value in function body",
        "category": "best_practice",
        "severity": "info",
    },
    "B002": {
        "id": "B002",
        "description": "Missing error handling for potentially unsafe operation",
        "category": "best_practice",
        "severity": "info",
    },
    "P001": {
        "id": "P001",
        "description": "Inefficient loop: consider using for-each instead of index loop",
        "category": "performance",
        "severity": "info",
    },
    "P002": {
        "id": "P002",
        "description": "Unused loop variable",
        "category": "performance",
        "severity": "warning",
    },
}


@dataclass
class ReviewIssue:
    severity: str
    message: str
    line: int
    col: int
    rule_id: str
    suggestion: str | None = None
    category: str = "style"

    def __post_init__(self) -> None:
        self.severity = self.severity.lower()


@dataclass
class ReviewResult:
    issues: list[ReviewIssue] = field(default_factory=list)
    file_path: str = ""
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def __post_init__(self) -> None:
        self._recount()

    def _recount(self) -> None:
        self.error_count = sum(1 for i in self.issues if i.severity == "error")
        self.warning_count = sum(1 for i in self.issues if i.severity == "warning")
        self.info_count = sum(1 for i in self.issues if i.severity in ("info", "hint"))

    def add(self, issue: ReviewIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "error":
            self.error_count += 1
        elif issue.severity == "warning":
            self.warning_count += 1
        elif issue.severity in ("info", "hint"):
            self.info_count += 1

    @property
    def total(self) -> int:
        return len(self.issues)

    def has_errors(self) -> bool:
        return self.error_count > 0

    def summary(self) -> str:
        parts = []
        if self.error_count:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning(s)")
        if self.info_count:
            parts.append(f"{self.info_count} info(s)")
        return (
            f"{self.total} issue(s): {', '.join(parts)}" if parts else "No issues found"
        )


class CodeReviewer:
    def __init__(self, provider: LLMProvider | None = None):
        self._provider = provider or MockProvider(
            responses={
                "review": "No AI-level issues found.",
            }
        )

    def review(self, source: str, file_path: str = "") -> ReviewResult:
        result = ReviewResult(file_path=file_path)
        lines = source.split("\n")

        basic_issues = self._check_basic_rules(source, lines)
        for issue in basic_issues:
            result.add(issue)

        ai_issues = self._check_with_ai(source)
        existing = {(i.rule_id, i.line) for i in result.issues}
        for issue in ai_issues:
            if (issue.rule_id, issue.line) not in existing:
                result.add(issue)

        return result

    def _check_basic_rules(self, source: str, lines: list[str]) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []

        issues.extend(self._check_function_naming(source, lines))
        issues.extend(self._check_line_length(lines))
        issues.extend(self._check_unused_variables(source, lines))
        issues.extend(self._check_missing_return_types(source, lines))
        issues.extend(self._check_deep_nesting(lines))
        issues.extend(self._check_duplicate_functions(source, lines))
        issues.extend(self._check_empty_catches(source, lines))
        issues.extend(self._check_hardcoded_values(source, lines))
        issues.extend(self._check_missing_error_handling(source, lines))
        issues.extend(self._check_loop_inefficiency(source, lines))
        issues.extend(self._check_unused_loop_vars(source, lines))
        issues.extend(self._check_constant_naming(source, lines))

        return issues

    def _check_function_naming(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        fn_matches = re.finditer(
            r"^\s*fn\s+([A-Z][a-zA-Z0-9_]*)\s*\(", source, re.MULTILINE
        )
        for m in fn_matches:
            fn_name = m.group(1)
            pos = m.start()
            line_num = source[:pos].count("\n") + 1
            col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
            issues.append(
                ReviewIssue(
                    severity=REVIEW_RULES["S001"]["severity"],
                    message=f"Function '{fn_name}' should use snake_case naming",
                    line=line_num,
                    col=col_num,
                    rule_id="S001",
                    category=REVIEW_RULES["S001"]["category"],
                    suggestion=f"Rename '{fn_name}' to '{self._to_snake_case(fn_name)}'",
                )
            )
        return issues

    def _check_constant_naming(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        const_matches = re.finditer(
            r"^\s*const\s+([a-z][a-zA-Z0-9_]*)\s*=", source, re.MULTILINE
        )
        for m in const_matches:
            name = m.group(1)
            if not name.isupper():
                pos = m.start()
                line_num = source[:pos].count("\n") + 1
                col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
                issues.append(
                    ReviewIssue(
                        severity=REVIEW_RULES["S002"]["severity"],
                        message=f"Constant '{name}' should use UPPER_CASE naming",
                        line=line_num,
                        col=col_num,
                        rule_id="S002",
                        category=REVIEW_RULES["S002"]["category"],
                        suggestion=f"Rename '{name}' to '{name.upper()}'",
                    )
                )
        return issues

    def _check_line_length(self, lines: list[str]) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        for i, line in enumerate(lines):
            if len(line) > 100 and line.strip():
                issues.append(
                    ReviewIssue(
                        severity=REVIEW_RULES["S003"]["severity"],
                        message=f"Line exceeds 100 characters ({len(line)} chars)",
                        line=i + 1,
                        col=101,
                        rule_id="S003",
                        category=REVIEW_RULES["S003"]["category"],
                        suggestion="Break the line into multiple lines",
                    )
                )
        return issues

    def _check_unused_variables(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []

        declared: dict[str, int] = {}
        let_matches = re.finditer(
            r"^\s*(?:let|const)\s+(\w+)\s*=", source, re.MULTILINE
        )
        for m in let_matches:
            pos = m.start()
            line_num = source[:pos].count("\n") + 1
            declared[m.group(1)] = line_num

        param_matches = re.finditer(
            r"fn\s+\w+\s*\(([^)]*)\)",
            source,
        )
        for m in param_matches:
            params_str = m.group(1)
            if params_str.strip():
                for param in params_str.split(","):
                    param = param.strip()
                    param = re.sub(r"\s+.*", "", param)
                    if param and param != "_":
                        pos = m.start()
                        line_num = source[:pos].count("\n") + 1
                        declared[param] = line_num

        used: set[str] = set()
        ref_matches = re.finditer(r"\b([a-zA-Z_]\w*)\b", source)
        for m in ref_matches:
            name = m.group(1)
            if name not in (
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
            ):
                used.add(name)

        for name, line_num in declared.items():
            if name not in used:
                issues.append(
                    ReviewIssue(
                        severity=REVIEW_RULES["C001"]["severity"],
                        message=f"Unused variable '{name}'",
                        line=line_num,
                        col=1,
                        rule_id="C001",
                        category=REVIEW_RULES["C001"]["category"],
                        suggestion=f"Remove '{name}' or prefix with '_' if intentionally unused",
                    )
                )

        for name, line_num in declared.items():
            if name not in used and name != "_":
                ref_count = len(re.findall(r"\b" + re.escape(name) + r"\b", source))
                if ref_count <= 1:
                    issues.append(
                        ReviewIssue(
                            severity=REVIEW_RULES["C001"]["severity"],
                            message=f"Potentially unused variable '{name}'",
                            line=line_num,
                            col=1,
                            rule_id="C001",
                            category=REVIEW_RULES["C001"]["category"],
                            suggestion=f"Check if '{name}' is needed",
                        )
                    )

        return issues

    def _check_missing_return_types(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        fn_matches = re.finditer(
            r"^\s*fn\s+\w+\s*\(([^)]*)\)\s*(?:->\s*(\w+))?\s*\{",
            source,
            re.MULTILINE,
        )
        for m in fn_matches:
            if not m.group(2):
                pos = m.start()
                line_num = source[:pos].count("\n") + 1
                col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
                fn_name_match = re.search(r"fn\s+(\w+)", m.group(0))
                fn_name = fn_name_match.group(1) if fn_name_match else "anonymous"
                issues.append(
                    ReviewIssue(
                        severity=REVIEW_RULES["C002"]["severity"],
                        message=f"Function '{fn_name}' missing return type",
                        line=line_num,
                        col=col_num,
                        rule_id="C002",
                        category=REVIEW_RULES["C002"]["category"],
                        suggestion=f"Add return type: fn {fn_name}(...) -> type",
                    )
                )
        return issues

    def _check_deep_nesting(self, lines: list[str]) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        depth = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            open_braces = stripped.count("{")
            close_braces = stripped.count("}")
            depth += open_braces
            if stripped.startswith("}"):
                depth -= close_braces
                if depth > 4:
                    issues.append(
                        ReviewIssue(
                            severity=REVIEW_RULES["C003"]["severity"],
                            message=f"Deep nesting level ({depth}) exceeds 4",
                            line=i + 1,
                            col=len(line) - len(line.lstrip()) + 1,
                            rule_id="C003",
                            category=REVIEW_RULES["C003"]["category"],
                            suggestion="Consider extracting nested logic into a separate function",
                        )
                    )
                depth += close_braces
            depth -= close_braces
        return issues

    def _check_duplicate_functions(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        fn_names: dict[str, int] = {}
        fn_matches = re.finditer(r"^\s*fn\s+(\w+)\s*\(", source, re.MULTILINE)
        for m in fn_matches:
            name = m.group(1)
            if name in fn_names:
                pos = m.start()
                line_num = source[:pos].count("\n") + 1
                col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
                issues.append(
                    ReviewIssue(
                        severity=REVIEW_RULES["C004"]["severity"],
                        message=f"Duplicate function name '{name}' (first defined at line {fn_names[name]})",
                        line=line_num,
                        col=col_num,
                        rule_id="C004",
                        category=REVIEW_RULES["C004"]["category"],
                        suggestion=f"Rename one of the '{name}' functions",
                    )
                )
            else:
                fn_names[name] = source[: m.start()].count("\n") + 1
        return issues

    def _check_empty_catches(self, source: str, lines: list[str]) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        empty_catch_matches = re.finditer(
            r"catch\s*\((\w*)\)\s*\{\s*\}",
            source,
        )
        for m in empty_catch_matches:
            pos = m.start()
            line_num = source[:pos].count("\n") + 1
            col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
            var_name = m.group(1) or "_"
            issues.append(
                ReviewIssue(
                    severity=REVIEW_RULES["C005"]["severity"],
                    message=f"Empty catch block for '{var_name}'",
                    line=line_num,
                    col=col_num,
                    rule_id="C005",
                    category=REVIEW_RULES["C005"]["category"],
                    suggestion="Add error handling logic or at minimum a print/log statement",
                )
            )
        return issues

    def _check_hardcoded_values(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        fn_bodies: list[tuple[int, int]] = []
        current_fn_start = -1
        brace_depth = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"^\s*fn\s+\w+\s*\(", stripped):
                current_fn_start = i
            brace_depth += stripped.count("{")
            brace_depth -= stripped.count("}")
            if brace_depth == 0 and current_fn_start >= 0:
                if i > current_fn_start:
                    fn_bodies.append((current_fn_start, i))
                current_fn_start = -1

        seen_values: set[str] = set()
        for fn_start, fn_end in fn_bodies:
            body_lines = lines[fn_start : fn_end + 1]
            body_text = "\n".join(body_lines)
            hardcoded_matches = re.finditer(
                r'(?:^|\n)(\s*)(?:let|const)\s+\w+\s*=\s*(\d{4,}|"[^"]{20,}")\s*$',
                body_text,
            )
            for m in hardcoded_matches:
                value = m.group(2)
                if value not in seen_values:
                    seen_values.add(value)
                    line_num = fn_start + body_text[: m.start()].count("\n") + 1
                    col_num = len(m.group(1)) + 1
                    issues.append(
                        ReviewIssue(
                            severity=REVIEW_RULES["B001"]["severity"],
                            message=f"Hardcoded value in function: {value[:40]}",
                            line=line_num,
                            col=col_num,
                            rule_id="B001",
                            category=REVIEW_RULES["B001"]["category"],
                            suggestion="Consider making this a parameter or constant",
                        )
                    )

        return issues

    def _check_missing_error_handling(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []

        has_try = "try" in source
        has_catch = "catch" in source

        potentially_unsafe = [
            r"\binput\s*\(",
            r"\bprint\s*\(",
            r"\bint\s*\(",
            r"\bfloat\s*\(",
        ]

        if not has_try or not has_catch:
            for pattern in potentially_unsafe:
                for m in re.finditer(pattern, source):
                    if not self._is_in_try_block(source, m.start()):
                        line_num = source[: m.start()].count("\n") + 1
                        col_num = len(source[: m.start()].rsplit("\n", 1)[-1])
                        unsafe_name = re.search(r"\w+", m.group(0))
                        name = unsafe_name.group(0) if unsafe_name else "operation"
                        issues.append(
                            ReviewIssue(
                                severity=REVIEW_RULES["B002"]["severity"],
                                message=f"'{name}()' may throw — consider wrapping in try/catch",
                                line=line_num,
                                col=col_num,
                                rule_id="B002",
                                category=REVIEW_RULES["B002"]["category"],
                                suggestion=f"Wrap '{name}()' in a try/catch block",
                            )
                        )

        return issues

    def _check_loop_inefficiency(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        for_match = re.finditer(
            r"for\s+\(\s*(let\s+)?(\w+)\s*=\s*0\s*;\s*\2\s*<\s*(\w+)\.(?:length|count)\s*;\s*\2\s*\+\+\s*\)",
            source,
        )
        for m in for_match:
            pos = m.start()
            line_num = source[:pos].count("\n") + 1
            col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
            collection = m.group(3)
            issues.append(
                ReviewIssue(
                    severity=REVIEW_RULES["P001"]["severity"],
                    message=f"Consider using 'for item in {collection}' instead of index loop",
                    line=line_num,
                    col=col_num,
                    rule_id="P001",
                    category=REVIEW_RULES["P001"]["category"],
                    suggestion=f"for item in {collection} {{ ... }}",
                )
            )
        return issues

    def _check_unused_loop_vars(
        self, source: str, lines: list[str]
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        for_each_matches = re.finditer(
            r"for\s+(\w+)\s+in\s+(\w+)",
            source,
        )
        for m in for_each_matches:
            var = m.group(1)
            m.group(2)

            block_start = m.end()
            open_idx = source.find("{", block_start)
            if open_idx == -1:
                continue

            brace_depth = 0
            block_end = -1
            for j in range(open_idx, len(source)):
                if source[j] == "{":
                    brace_depth += 1
                elif source[j] == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        block_end = j
                        break

            if block_end == -1:
                continue

            block_text = source[open_idx + 1 : block_end]

            var_refs = [
                r.start()
                for r in re.finditer(r"\b" + re.escape(var) + r"\b", block_text)
            ]

            if not var_refs:
                pos = m.start()
                line_num = source[:pos].count("\n") + 1
                col_num = len(source[:pos].rsplit("\n", 1)[-1]) + 1
                issues.append(
                    ReviewIssue(
                        severity=REVIEW_RULES["P002"]["severity"],
                        message=f"Loop variable '{var}' is never used in the loop body",
                        line=line_num,
                        col=col_num,
                        rule_id="P002",
                        category=REVIEW_RULES["P002"]["category"],
                        suggestion=f"Replace '{var}' with '_' if intentionally unused",
                    )
                )

        return issues

    def _check_with_ai(self, source: str) -> list[ReviewIssue]:
        try:
            lines = source.split("\n")
            line_count = len(lines)
            fn_count = len(re.findall(r"^\s*fn\s+\w+\s*\(", source, re.MULTILINE))

            prompt = (
                "You are a Zoya code reviewer. Analyze the following Zoya code and return a JSON array of issues.\n"
                "Each issue should have: 'severity' (error/warning/info/hint), 'message', 'line', 'col', 'rule_id', 'suggestion', 'category'.\n"
                "Only return the JSON array, nothing else.\n\n"
                f"Code ({line_count} lines, {fn_count} functions):\n"
                f"```\n{source}\n```\n"
            )

            response = self._provider.chat(
                [
                    {
                        "role": "system",
                        "content": "You are a Zoya code review AI. Return only JSON arrays.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            content = response.get("content", "")
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0]
                content = content.strip()

            import json

            issues_data = json.loads(content)
            results: list[ReviewIssue] = []
            for item in issues_data:
                results.append(
                    ReviewIssue(
                        severity=item.get("severity", "info"),
                        message=item.get("message", ""),
                        line=item.get("line", 1),
                        col=item.get("col", 1),
                        rule_id=item.get("rule_id", "AI001"),
                        suggestion=item.get("suggestion"),
                        category=item.get("category", "best_practice"),
                    )
                )
            return results
        except Exception:
            return []

    def _is_in_try_block(self, source: str, pos: int) -> bool:
        before = source[:pos]
        try_positions = [m.start() for m in re.finditer(r"\btry\b", before)]
        catch_positions = [m.start() for m in re.finditer(r"\bcatch\b", before)]

        for try_pos in reversed(try_positions):
            matching_catch = None
            for catch_pos in catch_positions:
                if catch_pos > try_pos:
                    matching_catch = catch_pos
                    break
            if matching_catch:
                if pos > try_pos and pos < matching_catch:
                    return True
            else:
                if pos > try_pos:
                    return True

        return False

    def _parse_zoya_source(self, source: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "functions": [],
            "classes": [],
            "interfaces": [],
            "enums": [],
            "variables": [],
            "imports": [],
        }

        fn_matches = re.finditer(
            r"^\s*fn\s+(\w+)\s*\(([^)]*)\)\s*(->\s*(\w+))?\s*\{",
            source,
            re.MULTILINE,
        )
        for m in fn_matches:
            name = m.group(1)
            params_str = m.group(2).strip()
            params = [p.strip() for p in params_str.split(",") if p.strip()]
            return_type = m.group(4) if m.group(3) else None
            result["functions"].append(
                {
                    "name": name,
                    "params": params,
                    "return_type": return_type,
                }
            )

        class_matches = re.finditer(
            r"^\s*class\s+(\w+)(?:\s*:\s*(\w+))?\s*\{",
            source,
            re.MULTILINE,
        )
        for m in class_matches:
            name = m.group(1)
            parent = m.group(2) if m.group(2) else None
            result["classes"].append(
                {
                    "name": name,
                    "parent": parent,
                }
            )

        interface_matches = re.finditer(
            r"^\s*interface\s+(\w+)\s*\{",
            source,
            re.MULTILINE,
        )
        for m in interface_matches:
            result["interfaces"].append({"name": m.group(1)})

        enum_matches = re.finditer(
            r"^\s*enum\s+(\w+)\s*\{",
            source,
            re.MULTILINE,
        )
        for m in enum_matches:
            result["enums"].append({"name": m.group(1)})

        let_matches = re.finditer(
            r"^\s*(?:let|const)\s+(\w+)\s*=",
            source,
            re.MULTILINE,
        )
        for m in let_matches:
            result["variables"].append(m.group(1))

        import_matches = re.finditer(
            r'^\s*import\s+"([^"]+)"(?:\s+as\s+(\w+))?',
            source,
            re.MULTILINE,
        )
        for m in import_matches:
            result["imports"].append(
                {
                    "path": m.group(1),
                    "alias": m.group(2),
                }
            )

        return result

    @staticmethod
    def _to_snake_case(name: str) -> str:
        s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()
