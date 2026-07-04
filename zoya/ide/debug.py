from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebugContext:
    source: str
    error_message: str
    error_type: str
    traceback: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)


@dataclass
class DebugAnalysis:
    root_cause: str
    fix_suggestion: str
    confidence: float
    related_lines: list[int] = field(default_factory=list)
    similar_bugs: list[str] = field(default_factory=list)


@dataclass
class BugPattern:
    name: str
    description: str
    pattern: str
    severity: str
    fix: str


COMMON_BUG_PATTERNS: list[BugPattern] = [
    BugPattern(
        name="division_by_zero",
        description="Division or modulo by zero will cause a runtime error",
        pattern=r"/\s*0\b|%\s*0\b|/\s*\([^)]*\)\s*$",
        severity="error",
        fix="Add a check to ensure the divisor is not zero before division",
    ),
    BugPattern(
        name="infinite_while_loop",
        description="While loop condition never changes, causing infinite loop",
        pattern=r"while\s+true\s*\{",
        severity="error",
        fix="Ensure the loop body contains a break condition or the loop variable is modified",
    ),
    BugPattern(
        name="string_concatenation_with_number",
        description="Concatenating string and number without explicit conversion",
        pattern=r'"\s*\+\s*[a-zA-Z_]\w*(?!\s*\()|\b\w+\s*\+\s*"\s*',
        severity="warning",
        fix="Use str() to convert numbers before concatenation",
    ),
    BugPattern(
        name="unused_variable",
        description="Variable is assigned but never used",
        pattern=r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*",
        severity="warning",
        fix="Remove the unused variable or prefix with '_' to indicate intentional disuse",
    ),
    BugPattern(
        name="missing_return",
        description="Non-void function may not return a value in all paths",
        pattern=r"fn\s+\w+\s*\([^)]*\)\s*\{",
        severity="warning",
        fix="Ensure all code paths in the function return a value",
    ),
    BugPattern(
        name="off_by_one",
        description="Loop condition may cause off-by-one error",
        pattern=r"<=\s+[a-zA-Z_]\w*\.length|<=\s+len\(",
        severity="warning",
        fix="Use '<' instead of '<=' for zero-indexed collections",
    ),
    BugPattern(
        name="reassigning_loop_var",
        description="Loop variable is being modified inside the loop body",
        pattern=r"\b\w+\s*\+\+|\b\w+\s*--",
        severity="warning",
        fix="Use a separate variable instead of modifying the loop counter",
    ),
    BugPattern(
        name="none_null_access",
        description="Potential access on null/undefined value",
        pattern=r"(\w+)\.(\w+)\s*\(|\w+\[",
        severity="warning",
        fix="Check that the value is not null before accessing methods or indices",
    ),
    BugPattern(
        name="recursive_no_base_case",
        description="Recursive function without a base case may cause stack overflow",
        pattern=r"fn\s+(\w+)[^}]*\b\1\s*\(",  # function that calls itself
        severity="error",
        fix="Add a base case condition to stop recursion",
    ),
    BugPattern(
        name="variable_shadowing",
        description="Local variable shadows a parameter or outer variable",
        pattern=r"fn\s+\w+\s*\([^)]*\)\s*\{[^}]*\b\w+\b\s*=",
        severity="warning",
        fix="Rename the local variable to avoid shadowing",
    ),
]


class DebugAssistant:
    def __init__(self, provider=None) -> None:
        self.provider = provider

    def analyze_error(self, context: DebugContext) -> DebugAnalysis:
        if self.provider is not None:
            return self._analyze_with_ai(context)
        return self.analyze_error_no_ai(context)

    def _analyze_with_ai(self, context: DebugContext) -> DebugAnalysis:
        return DebugAnalysis(
            root_cause="AI analysis not yet implemented",
            fix_suggestion="Use analyze_error_no_ai for rule-based analysis",
            confidence=0.0,
            related_lines=[],
            similar_bugs=[],
        )

    def analyze_error_no_ai(self, context: DebugContext) -> DebugAnalysis:
        source = context.source
        error_msg = context.error_message
        error_type = context.error_type
        lines = source.split("\n")
        related_lines: list[int] = []
        similar_bugs: list[str] = []

        line_num = self._extract_line_from_error(error_msg)
        root_cause = ""
        fix_suggestion = ""

        if (
            "TypeError" in error_type
            or "ZoyaTypeError" in error_type
            or "type" in error_type.lower()
        ):
            root_cause = self._analyze_type_error(source, error_msg, line_num)
            fix_suggestion = "Check the types of operands and ensure they are compatible for the operation"
            related_lines = self._find_related_type_lines(lines, line_num)
            similar_bugs = ["type_mismatch_in_operation", "incompatible_types"]

        elif "ZeroDivision" in error_msg or "division by zero" in error_msg.lower():
            root_cause = f"Division by zero at line {line_num}"
            fix_suggestion = (
                "Check that the divisor is not zero before performing the division"
            )
            related_lines = [line_num] if line_num > 0 else []
            similar_bugs = ["division_by_zero"]

        elif "IndexError" in error_type or "index" in error_msg.lower():
            root_cause = f"Index out of bounds at line {line_num}"
            fix_suggestion = "Ensure the index is within the valid range (0 to length-1) before accessing"
            related_lines = self._find_related_index_lines(lines, line_num)
            similar_bugs = ["index_out_of_bounds", "off_by_one"]

        elif (
            "NameError" in error_type
            or "not defined" in error_msg.lower()
            or "undefined" in error_msg.lower()
        ):
            var_name = self._extract_var_from_error(error_msg)
            root_cause = (
                f"Variable '{var_name}' used before definition at line {line_num}"
            )
            fix_suggestion = f"Define '{var_name}' before use, or check for typos in the variable name"
            related_lines = self._find_related_var_lines(lines, var_name, line_num)
            similar_bugs = ["undefined_variable", "typo_in_variable_name"]

        elif "KeyError" in error_type or "key" in error_msg.lower():
            key = self._extract_var_from_error(error_msg)
            root_cause = f"Missing key '{key}' in dictionary at line {line_num}"
            fix_suggestion = f"Ensure the key '{key}' exists in the dictionary before accessing it, or use a default value"
            related_lines = [line_num] if line_num > 0 else []
            similar_bugs = ["missing_dict_key"]

        elif (
            "RecursionError" in error_type
            or "maximum recursion" in error_msg.lower()
            or "stack overflow" in error_msg.lower()
        ):
            root_cause = "Recursion depth exceeded — possible missing base case or infinite recursion"
            fix_suggestion = (
                "Add a base case to stop recursion, or increase recursion limit"
            )
            related_lines = self._find_recursive_functions(lines)
            similar_bugs = ["recursive_no_base_case", "stack_overflow"]

        elif "AttributeError" in error_type or "has no attribute" in error_msg.lower():
            attr = self._extract_attr_from_error(error_msg)
            root_cause = (
                f"Attempt to access non-existent attribute '{attr}' at line {line_num}"
            )
            fix_suggestion = (
                "Check that the object has the attribute before accessing it"
            )
            related_lines = [line_num] if line_num > 0 else []
            similar_bugs = ["none_null_access", "missing_attribute"]

        else:
            root_cause = f"Runtime error at line {line_num}: {error_msg}"
            fix_suggestion = (
                "Review the error and check the surrounding code for logical issues"
            )
            related_lines = self._find_context_lines(lines, line_num)

        for pattern in COMMON_BUG_PATTERNS:
            for i, line in enumerate(lines):
                if re.search(pattern.pattern, line):
                    if pattern.name not in similar_bugs:
                        similar_bugs.append(pattern.name)
                    if i + 1 not in related_lines:
                        related_lines.append(i + 1)
                    break

        confidence = 0.7 if error_type else 0.4
        related_lines = sorted(set(related_lines))

        return DebugAnalysis(
            root_cause=root_cause,
            fix_suggestion=fix_suggestion,
            confidence=confidence,
            related_lines=related_lines[:10],
            similar_bugs=similar_bugs[:5],
        )

    def suggest_fix(self, source: str, error_line: int, error_message: str) -> str:
        lines = source.split("\n")
        if error_line < 1 or error_line > len(lines):
            return "// Could not locate the error line"

        target_line = lines[error_line - 1]
        stripped = target_line.strip()
        indent_match = re.match(r"^(\s*)", target_line)
        indent = indent_match.group(1) if indent_match else ""

        if "/" in stripped and "0" in stripped:
            return self._gen_fix_text(
                lines,
                error_line,
                indent,
                f'if divisor != 0 {{\n    {stripped}\n}} else {{\n    {indent}    print "Error: division by zero"\n{indent}}}',
            )

        if re.search(r"\b\w+\s*\[\s*\w+\s*\]", stripped):
            return self._gen_fix_text(
                lines,
                error_line,
                indent,
                f'if index >= 0 and index < len(collection) {{\n    {stripped}\n}} else {{\n    {indent}    print "Error: index out of bounds"\n{indent}}}',
            )

        return self._gen_fix_text(
            lines,
            error_line,
            indent,
            f'try {{\n    {stripped}\n}} catch err {{\n    {indent}    print "Error: " + err\n{indent}}}',
        )

    def _gen_fix_text(
        self, lines: list[str], error_line: int, indent: str, wrapped: str
    ) -> str:
        result: list[str] = []
        for i, line in enumerate(lines):
            if i + 1 == error_line:
                result.append(wrapped)
            else:
                result.append(line)
        return "\n".join(result)

    def find_null_pointer_sources(self, source: str) -> list[int]:
        lines = source.split("\n")
        null_lines: list[int] = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(
                r"=\s*null\b|=\s*none\b|=\s*undefined\b", stripped, re.IGNORECASE
            ):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.search(
                        r"\b" + re.escape(stripped.split("=")[0].strip()) + r"\b",
                        next_line,
                    ):
                        null_lines.append(i + 1)

            if re.search(r"\.\s*\w+\s*\(\)", stripped):
                obj = re.match(r"^\s*([a-zA-Z_]\w*)\s*\.", stripped)
                if obj:
                    var = obj.group(1)
                    assign_match = None
                    for j in range(max(0, i - 10), i):
                        am = re.match(rf"^\s*{re.escape(var)}\s*=", lines[j])
                        if am:
                            assign_match = lines[j]
                            break
                    if assign_match and re.search(
                        r"=\s*(null|none|undefined)\s*$", assign_match, re.IGNORECASE
                    ):
                        null_lines.append(i + 1)

        return sorted(set(null_lines))

    def find_type_errors(self, source: str) -> list[tuple[int, str]]:
        lines = source.split("\n")
        type_issues: list[tuple[int, str]] = []

        patterns = [
            (r'"([^"]*)"\s*\+\s*(\d+)', "String concatenation with number"),
            (r'"([^"]*)"\s*-\s*', "Subtraction on string"),
            (r'"([^"]*)"\s*\*\s*', "Multiplication on string"),
            (r'"([^"]*)"\s*/\s*', "Division on string"),
            (r"\blen\s*\(\s*(\d+)\s*\)", "len() called on a number"),
            (r'\blen\s*\(\s*("[^"]*")\s*\)', "len() called on a string (valid)"),
            (r"// [^/]", "Comment after expression"),
            (r"(\d+)\s*\[\s*(\d+)\s*\]", "Index access on a number"),
        ]

        for i, line in enumerate(lines):
            stripped = line.strip()
            for pat, desc in patterns:
                if re.search(pat, stripped):
                    type_issues.append((i + 1, desc))

        return type_issues

    def find_infinite_loop_risks(self, source: str) -> list[int]:
        lines = source.split("\n")
        risks: list[int] = []

        i = 0
        while i < len(lines):
            stripped = lines[i].strip()

            while_match = re.match(r"^while\s+true\s*\{", stripped)
            if while_match:
                brace_count = 1
                body_has_break = False
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count > 0:
                        if "break" in lines[j]:
                            body_has_break = True
                    j += 1

                if not body_has_break:
                    risks.append(i + 1)
                i = j
                continue

            while_match = re.match(
                r"^while\s+([a-zA-Z_]\w*)\s*(<|>|<=|>=|!=|==)\s*(.+?)\s*\{", stripped
            )
            if while_match:
                var = while_match.group(1)
                brace_count = 1
                body_modifies_var = False
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count > 0:
                        if re.search(
                            rf"\b{re.escape(var)}\s*(?:\+\+|--|\+=|-=|\*=|/=)", lines[j]
                        ):
                            body_modifies_var = True
                    j += 1

                if not body_modifies_var:
                    risks.append(i + 1)
                i = j
                continue

            i += 1

        return sorted(set(risks))

    def analyze_stack_trace(self, traceback: list[str]) -> str:
        if not traceback:
            return "No stack trace available"

        lines: list[str] = ["Stack Trace Analysis:"]

        for tb_line in traceback:
            tb_line = tb_line.strip()
            if not tb_line:
                continue

            frame_match = re.match(
                r"^\s*(?:at\s+)?(\w+)\s*(?:at|\(|\:)\s*(?:line\s*)?(\d+)(?:\s*:\s*(\d+))?",
                tb_line,
            )
            if frame_match:
                func = frame_match.group(1)
                line_num = frame_match.group(2)
                col_num = frame_match.group(3) or "?"
                lines.append(f"  - In function `{func}` at line {line_num}:{col_num}")

            elif re.match(r"^\s*(?:File|file):", tb_line):
                file_match = re.match(
                    r"^\s*(?:File|file):\s*(.+?)(?:,\s*line\s*(\d+))?", tb_line
                )
                if file_match:
                    fname = file_match.group(1)
                    fline = file_match.group(2) or "?"
                    lines.append(f"  - File: {fname}, line {fline}")

            else:
                if "Error" in tb_line or "error" in tb_line.lower():
                    lines.append(f"  - {tb_line}")

        if len(lines) == 1:
            lines.append("  (unable to parse traceback format)")

        return "\n".join(lines)

    def _extract_line_from_error(self, error_msg: str) -> int:
        m = re.search(r"line\s*(\d+)", error_msg, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    def _extract_var_from_error(self, error_msg: str) -> str:
        patterns = [
            r"'([^']+)'(?:\s+is\s+not\s+defined|\s+not\s+defined)",
            r"'([^']+)'(?:\s+not\s+found|\s+missing)",
            r"name\s+'([^']+)'\s+is\s+not\s+defined",
            r"undefined\s+(?:variable\s+)?'?([a-zA-Z_]\w*)'?",
            r"key\s+'?([a-zA-Z_]\w*)'?",
        ]
        for pat in patterns:
            m = re.search(pat, error_msg)
            if m:
                return m.group(1)
        m = re.search(r"'(\w+)'", error_msg)
        return m.group(1) if m else "unknown"

    def _extract_attr_from_error(self, error_msg: str) -> str:
        m = re.search(
            r"attribute\s+'(\w+)'|'(\w+)'\s+has\s+no\s+attribute|has\s+no\s+attribute\s+'(\w+)'",
            error_msg,
            re.IGNORECASE,
        )
        if m:
            return next(g for g in m.groups() if g is not None)
        return "unknown"

    def _find_related_type_lines(self, lines: list[str], line_num: int) -> list[int]:
        related = []
        if line_num > 0:
            related.append(line_num)
            start = max(0, line_num - 3)
            for i in range(start, min(len(lines), line_num + 2)):
                if i + 1 != line_num:
                    related.append(i + 1)
        return related

    def _find_related_index_lines(self, lines: list[str], line_num: int) -> list[int]:
        related = []
        if line_num > 0 and line_num <= len(lines):
            related.append(line_num)
            line = lines[line_num - 1]
            m = re.search(r"\[(\w+|\d+)\]", line)
            if m:
                idx = m.group(1)
                for i, l in enumerate(lines):
                    if re.search(rf"\b{re.escape(idx)}\s*=\s*", l) or re.search(
                        rf"\b{re.escape(idx)}\s*\+\+|--{re.escape(idx)}", l
                    ):
                        related.append(i + 1)
        return related

    def _find_related_var_lines(
        self, lines: list[str], var: str, line_num: int
    ) -> list[int]:
        related = []
        if line_num > 0:
            related.append(line_num)
        for i, line in enumerate(lines):
            if re.search(rf"\b{re.escape(var)}\s*=", line):
                related.append(i + 1)
            if re.search(rf"\bfn\s+\w+\s*\(.*\b{re.escape(var)}\b", line):
                related.append(i + 1)
            if re.search(rf"\b{re.escape(var)}\s*::", line):
                related.append(i + 1)
        return sorted(set(related))

    def _find_recursive_functions(self, lines: list[str]) -> list[int]:
        recursive_lines: list[int] = []
        i = 0
        while i < len(lines):
            m = re.match(r"^\s*fn\s+(\w+)\s*\(", lines[i])
            if m:
                fn_name = m.group(1)
                brace_count = 1
                j = i + 1
                body_has_recursion = False
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count > 0 and re.search(
                        rf"\b{re.escape(fn_name)}\s*\(", lines[j]
                    ):
                        body_has_recursion = True
                    j += 1

                if body_has_recursion:
                    has_base_case = False
                    for k in range(i + 1, j):
                        if re.search(r"\bif\s+", lines[k]) and re.search(
                            r"\breturn\b", lines[k]
                        ):
                            has_base_case = True
                            break
                    if not has_base_case:
                        recursive_lines.append(i + 1)
                i = j
            else:
                i += 1
        return recursive_lines

    def _find_context_lines(self, lines: list[str], line_num: int) -> list[int]:
        if line_num <= 0:
            return []
        start = max(0, line_num - 3)
        end = min(len(lines), line_num + 2)
        return list(range(start + 1, end + 1))
