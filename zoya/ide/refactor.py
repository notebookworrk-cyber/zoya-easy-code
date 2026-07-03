from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class RefactoringOperation:
    name: str
    description: str

    def apply(self, source: str, **params) -> str:
        return source


@dataclass
class RefactoringSuggestion:
    name: str
    description: str
    lines: Tuple[int, int]
    confidence: float


_INDENT_RE = re.compile(r"^( {4}|\t)*")
_FN_RE = re.compile(r"\bfn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
_FOR_RE = re.compile(r"\bfor\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*0\s*;\s*\1\s*<\s*([a-zA-Z_][a-zA-Z0-9_]*?)\s*;\s*\1\s*\+\+\s*\)")
_FOREACH_RE = re.compile(r"\bforeach\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in\s+")
_IF_CHAIN_RE = re.compile(r"\bif\s+(.+?)\s*\{[^}]*\}\s*else\s+if\s+")
_PRINT_RE = re.compile(r"\bprint\s+(.+)$", re.MULTILINE)
_LOGGING_TEMPLATE = 'log("{level}", {expr})'
_VAR_REF = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")
_UNREACHABLE_RE = re.compile(r"^\s*return\s+.*?\n((?:.|\n)*?)^\s*(?:[a-zA-Z_])", re.MULTILINE)
_IMPORT_RE = re.compile(r'^\s*import\s+"([^"]+)"(?:\s+as\s+([a-zA-Z_][a-zA-Z0-9_]*))?\s*$', re.MULTILINE)
_BOOL_SIMP = re.compile(r"\b(true\s+and\s+true|false\s+or\s+false|true\s+or\s+\w+|false\s+and\s+\w+|\w+\s+==\s+\w+)")


class RefactoringEngine:
    def __init__(self) -> None:
        pass

    def rename_variable(self, source: str, old_name: str, new_name: str) -> str:
        lines = source.split("\n")
        result: list[str] = []
        scope_stack: list[list[int]] = []
        current_scope_vars: set[str] = set()
        brace_depth = 0

        def in_scope(line_idx: int) -> bool:
            for scope_lines in reversed(scope_stack):
                if line_idx in scope_lines:
                    return True
            return False

        for i, line in enumerate(lines):
            stripped = line.strip()

            assign_match = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=", stripped)
            if assign_match:
                current_scope_vars.add(assign_match.group(1))

            if "{" in stripped:
                scope_stack.append(list(range(max(0, i - 5), i + 5)))
                current_scope_vars = set()

            for cb in re.findall(r"\}", stripped):
                if scope_stack:
                    scope_stack.pop()

            orig = line
            if old_name in current_scope_vars or in_scope(i):
                replaced = self._replace_ident(line, old_name, new_name)
            else:
                replaced = self._replace_ident(line, old_name, new_name)
            result.append(replaced)

        return "\n".join(result)

    def _replace_ident(self, line: str, old: str, new: str) -> str:
        return re.sub(
            rf"\b{re.escape(old)}\b(?!\s*\()",
            new,
            line,
        )

    def extract_function(self, source: str, start_line: int, end_line: int, new_name: str) -> str:
        lines = source.split("\n")
        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return source

        extracted_lines = lines[start_line - 1 : end_line]
        indent_match = _INDENT_RE.match(extracted_lines[0])
        base_indent = indent_match.group(0) if indent_match else ""
        inner_indent = base_indent + "    "

        body = []
        for line in extracted_lines:
            stripped = line.strip()
            if stripped:
                body.append(inner_indent + stripped.lstrip())
            else:
                body.append("")

        params: list[str] = []
        for line in extracted_lines:
            for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", line):
                name = m.group(1)
                if name not in params and name not in ("print", "input", "return", "if", "else",
                                                       "while", "for", "foreach", "loop", "in",
                                                       "true", "false", "and", "or", "not"):
                    params.append(name)

        fn_def = f"{base_indent}fn {new_name}({', '.join(params)}) {{\n"
        fn_def += "\n".join(body) + "\n"
        fn_def += f"{base_indent}}}"

        if params:
            call_args = ", ".join(p for p in params)
            call_line = f"{base_indent}{new_name}({call_args})"
        else:
            call_line = f"{base_indent}{new_name}()"

        before = lines[: start_line - 1]
        after = lines[end_line:]

        if before and not before[-1].strip():
            before = before[:-1]

        result = "\n".join(before)
        if result:
            result += "\n"
        result += fn_def + "\n\n"
        result += call_line + "\n"
        if after:
            result += "\n".join(after)

        return result

    def inline_function(self, source: str, function_name: str) -> str:
        lines = source.split("\n")
        fn_start = -1
        fn_end = -1
        fn_params: list[str] = []
        fn_body_lines: list[str] = []

        for i, line in enumerate(lines):
            m = re.match(r"^\s*fn\s+" + re.escape(function_name) + r"\s*\((.*?)\)\s*\{", line)
            if m:
                fn_start = i
                raw_params = m.group(1).strip()
                if raw_params:
                    fn_params = [p.strip() for p in raw_params.split(",")]
                brace_count = line.count("{") - line.count("}")
                fn_body_lines = []
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count > 0:
                        fn_body_lines.append(lines[j])
                    j += 1
                fn_end = j
                break

        if fn_start == -1:
            return source

        trimmed_body = []
        for bl in fn_body_lines:
            trimmed_body.append(re.sub(r"^    ", "", bl))

        body_text = "\n".join(trimmed_body).strip()
        if body_text.startswith("return "):
            return_line = f"    {body_text[7:]}"
        else:
            return_line = f"    {body_text}"

        call_re = re.compile(r"\b" + re.escape(function_name) + r"\s*\((.*?)\)")
        result_lines = lines[:fn_start] + lines[fn_end:]

        result_source = "\n".join(result_lines)
        result_source = call_re.sub(lambda m: self._substitute_inline(m, fn_params, return_line), result_source)

        return result_source

    def _substitute_inline(self, m: re.Match, params: list[str], body: str) -> str:
        raw_args = m.group(1).strip()
        if raw_args:
            args = [a.strip() for a in raw_args.split(",")]
        else:
            args = []
        result = body
        for p, a in zip(params, args):
            result = result.replace(p, a)
        return result.strip()

    def convert_loop_to_for_each(self, source: str) -> str:
        result = []
        for line in source.split("\n"):
            m = _FOR_RE.search(line)
            if m:
                var = m.group(1)
                container = m.group(2)
                # Adjust to foreach pattern
                result.append(re.sub(
                    r"for\s*\(.*?\)",
                    f"foreach {var} in {container}",
                    line,
                ))
            else:
                result.append(line)
        return "\n".join(result)

    def convert_if_to_switch(self, source: str) -> str:
        lines = source.split("\n")
        result: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]

            chain_match = re.match(r"^\s*if\s+(.+?)\s*\{", line)
            if not chain_match:
                result.append(line)
                i += 1
                continue

            cond = chain_match.group(1)
            # Look for == comparisons to determine switch expression
            eq_match = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*(.+?)$", cond)
            if not eq_match:
                result.append(line)
                i += 1
                continue

            switch_var = eq_match.group(1)
            first_val = eq_match.group(2)

            switch_lines: list[str] = []
            indent_match = _INDENT_RE.match(line)
            indent = indent_match.group(0) if indent_match else ""

            switch_lines.append(f"{indent}switch {switch_var} {{")
            case_indent = indent + "    "

            # Add first case
            switch_lines.append(f"{case_indent}case {first_val} {{")
            i += 1
            while i < len(lines):
                cl = lines[i]
                if re.match(r"^\s*\}\s*else\s+if\s+", cl):
                    val_match = re.search(r"==\s*(.+?)\s*\{", cl)
                    if val_match:
                        switch_lines.append(f"{case_indent}}}")
                        switch_lines.append(f"{case_indent}case {val_match.group(1)} {{")
                    i += 1
                elif re.match(r"^\s*\}\s*else\s*\{", cl):
                    switch_lines.append(f"{case_indent}}}")
                    switch_lines.append(f"{case_indent}default {{")
                    i += 1
                elif re.match(r"^\s*\}", cl):
                    switch_lines.append(f"{case_indent}}}")
                    break
                else:
                    switch_lines.append(cl)
                    i += 1
                i += 1

            switch_lines.append(f"{indent}}}")
            result.extend(switch_lines)
            i += 1

        return "\n".join(result)

    def add_type_annotations(self, source: str) -> str:
        lines = source.split("\n")
        result: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Number assignment
            m = re.match(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(\d+)", stripped)
            if m and "::" not in stripped:
                result.append(f"{m.group(1)}{m.group(2)} :: int = {m.group(3)}")
                continue
            m = re.match(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(\d+\.\d+)", stripped)
            if m and "::" not in stripped:
                result.append(f"{m.group(1)}{m.group(2)} :: float = {m.group(3)}")
                continue
            m = re.match(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]*)"', stripped)
            if m and "::" not in stripped:
                result.append(f'{m.group(1)}{m.group(2)} :: str = "{m.group(3)}"')
                continue
            m = re.match(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(true|false)", stripped)
            if m and "::" not in stripped:
                result.append(f"{m.group(1)}{m.group(2)} :: bool = {m.group(3)}")
                continue
            m = re.match(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[", stripped)
            if m and "::" not in stripped:
                result.append(f"{m.group(1)}{m.group(2)} :: list = {stripped[m.end(2) - m.start(1) + m.start(1):]}")
                continue
            m = re.match(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", stripped)
            if m and "::" not in stripped:
                result.append(f"{m.group(1)}{m.group(2)} :: dict = {stripped[m.end(2) - m.start(1) + m.start(1):]}")
                continue
            result.append(line)

        return "\n".join(result)

    def simplify_boolean_expression(self, source: str) -> str:
        replacements = [
            (r"\btrue\s+and\s+true\b", "true"),
            (r"\btrue\s+and\s+false\b", "false"),
            (r"\bfalse\s+and\s+true\b", "false"),
            (r"\bfalse\s+and\s+false\b", "false"),
            (r"\btrue\s+or\s+false\b", "true"),
            (r"\bfalse\s+or\s+true\b", "true"),
            (r"\btrue\s+or\s+true\b", "true"),
            (r"\bfalse\s+or\s+false\b", "false"),
            (r"\bnot\s+true\b", "false"),
            (r"\bnot\s+false\b", "true"),
            (r"\bnot\s+\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)", r"\1 != \2"),
            (r"\bnot\s+\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*!=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)", r"\1 == \2"),
            (r"\b(\w+)\s+==\s+true\b", r"\1"),
            (r"\b(\w+)\s+==\s+false\b", r"not \1"),
            (r"\b(\w+)\s+!=\s+true\b", r"not \1"),
            (r"\b(\w+)\s+!=\s+false\b", r"\1"),
        ]
        result = source
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)
        return result

    def remove_dead_code(self, source: str) -> str:
        lines = source.split("\n")
        result: list[str] = []
        unreachable_block = False
        brace_depth = 0

        for line in lines:
            stripped = line.strip()

            if unreachable_block:
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth <= 0:
                    unreachable_block = False
                    if not stripped.startswith("}") and stripped:
                        result.append(line)
                continue

            if re.match(r"^\s*return\s+", stripped):
                result.append(line)
                unreachable_block = True
                brace_depth = 0
                continue

            if stripped.startswith("// dead") or stripped.startswith("//dead") or stripped.startswith("# dead") or stripped.startswith("#dead"):
                continue

            result.append(line)

        return "\n".join(result)

    def sort_imports(self, source: str) -> str:
        lines = source.split("\n")
        import_lines: list[tuple[str, str, str | None, str]] = []
        other_lines: list[str] = []
        in_import_block = False

        for line in lines:
            m = _IMPORT_RE.match(line)
            if m:
                path = m.group(1)
                alias = m.group(2)
                import_lines.append((path, line, alias, line))
                in_import_block = True
            else:
                if in_import_block and line.strip() == "":
                    continue
                if in_import_block and line.strip():
                    in_import_block = False
                other_lines.append(line)

        if not import_lines:
            return source

        import_lines.sort(key=lambda x: x[0])

        result: list[str] = []
        first = True
        for _, orig, alias, _ in import_lines:
            if first:
                first = False
            else:
                pass
            result.append(orig)

        if result and other_lines:
            result.append("")
            result.extend(other_lines)
        else:
            result.extend(other_lines)

        return "\n".join(result)

    def format_code(self, source: str) -> str:
        lines = source.split("\n")
        result: list[str] = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append("")
                continue
            if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*"):
                result.append("    " * indent_level + stripped)
                continue
            if stripped.startswith("}") or stripped.startswith("])") or stripped.startswith(")") or stripped == "}":
                indent_level = max(0, indent_level - 1)

            result.append("    " * indent_level + stripped)

            open_braces = stripped.count("{") - stripped.count("}")
            open_parens = stripped.count("(") - stripped.count(")")
            if open_braces > 0:
                indent_level += open_braces
            if open_parens > 0 and not stripped.startswith("//"):
                pass

        return "\n".join(result)

    def split_large_function(self, source: str, max_lines: int = 50) -> str:
        lines = source.split("\n")
        result: list[str] = []
        i = 0
        next_id = 1

        while i < len(lines):
            fn_match = re.match(r"^(\s*)fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*\{", lines[i])
            if not fn_match:
                result.append(lines[i])
                i += 1
                continue

            indent = fn_match.group(1)
            fn_name = fn_match.group(2)
            fn_params = fn_match.group(3)

            fn_body_start = i + 1
            brace_count = 1
            j = fn_body_start
            while j < len(lines) and brace_count > 0:
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count > 0:
                    j += 1
            fn_body_end = j

            fn_body_lines = lines[fn_body_start:fn_body_end]
            if len(fn_body_lines) <= max_lines:
                result.append(lines[i])
                result.extend(fn_body_lines)
                if i < len(lines):
                    result.append(lines[fn_body_end] if fn_body_end < len(lines) else "")
                i = fn_body_end + 1
                continue

            extracted_fn: list[str] = []
            chunk_size = max_lines - 5
            for chunk_start in range(0, len(fn_body_lines), chunk_size):
                chunk = fn_body_lines[chunk_start:chunk_start + chunk_size]
                helper_name = f"_{fn_name}_part{next_id}"
                helper_line = f"    {helper_name}()"
                extracted_fn.append(helper_line)
                next_id += 1

                def_lines = [f"\n{indent}fn {helper_name}() {{"]
                def_lines.extend(chunk)
                def_lines.append(f"{indent}}}")
                result.extend(def_lines)

            for chunk_start in range(0, len(fn_body_lines), chunk_size):
                pass

            i = fn_body_end + 1

        return "\n".join(result)

    def convert_print_to_logging(self, source: str) -> str:
        lines = source.split("\n")
        result: list[str] = []

        has_log_import = any("import" in l and "logging" in l for l in lines)
        log_import_added = False

        for line in lines:
            m = re.match(r"^(\s*)print\s+(.+)$", line)
            if m:
                indent = m.group(1)
                expr = m.group(2).strip()
                if not has_log_import and not log_import_added:
                    result.append('import "logging"')
                    log_import_added = True
                result.append(f"{indent}log(\"info\", {expr})")
            else:
                result.append(line)

        return "\n".join(result)

    def wrap_in_error_handler(self, source: str, function_name: str) -> str:
        lines = source.split("\n")
        result: list[str] = []
        i = 0
        inside_fn = False
        fn_brace_count = 0
        fn_body_start = -1
        fn_body_end = -1

        for line in lines:
            m = re.match(r"^(\s*)fn\s+" + re.escape(function_name) + r"\s*\((.*?)\)\s*\{", line)
            if m:
                indent = m.group(1)
                fn_brace_count = 1
                inside_fn = True
                result.append(line)
                fn_body_start = len(result)
                result.append(f"{indent}    try {{")
                continue

            if inside_fn:
                fn_brace_count += line.count("{") - line.count("}")
                if fn_brace_count == 0:
                    indent = re.match(r"^(\s*)", line).group(1) if re.match(r"^(\s*)", line) else ""
                    result.append(f"{indent}    }} catch err {{")
                    result.append(f'{indent}        print "Error in {function_name}: " + err')
                    result.append(f"{indent}    }}")
                    result.append(line)
                    inside_fn = False
                    continue
                result.append(line)
            else:
                result.append(line)

        return "\n".join(result)


def get_available_refactorings(source: str) -> List[RefactoringSuggestion]:
    suggestions: List[RefactoringSuggestion] = []
    lines = source.split("\n")

    # for loop to foreach
    for i, line in enumerate(lines):
        if re.search(r"for\s*\(\s*[a-zA-Z_]\w*\s*=\s*0\s*;", line):
            container_match = re.search(r";\s*\1?\s*<\s*([a-zA-Z_]\w*)\.length\s*;", line)
            if container_match:
                suggestions.append(RefactoringSuggestion(
                    name="convert_loop_to_for_each",
                    description="Convert indexed for loop to foreach",
                    lines=(i + 1, i + 1),
                    confidence=0.8,
                ))
            break

    # if/elif chain to switch
    chain_count = 0
    chain_start = -1
    for i, line in enumerate(lines):
        if re.match(r"^\s*if\s+.+?==.+?\{", line):
            if chain_start == -1:
                chain_start = i + 1
            chain_count += 1
        elif re.match(r"^\s*\}\s*else\s+if\s+", line):
            chain_count += 1
        elif re.match(r"^\s*\}\s*else\s*\{", line):
            chain_count += 1
            if chain_count >= 3:
                suggestions.append(RefactoringSuggestion(
                    name="convert_if_to_switch",
                    description="Convert if/elif chain to switch statement",
                    lines=(chain_start, i + 1),
                    confidence=0.7,
                ))
            chain_start = -1
            chain_count = 0

    # print to logging
    print_count = sum(1 for line in lines if re.match(r"^\s*print\s+", line))
    if print_count >= 3:
        suggestions.append(RefactoringSuggestion(
            name="convert_print_to_logging",
            description="Replace print statements with structured logging",
            lines=(1, len(lines)),
            confidence=0.6,
        ))

    # large function split
    i = 0
    while i < len(lines):
        fn_match = re.match(r"^(\s*)fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*\{", lines[i])
        if fn_match:
            fn_name = fn_match.group(2)
            brace_count = 1
            start = i + 1
            j = start
            while j < len(lines) and brace_count > 0:
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count > 0:
                    j += 1
            fn_body_len = j - start
            if fn_body_len > 50:
                suggestions.append(RefactoringSuggestion(
                    name="split_large_function",
                    description=f"Split function '{fn_name}' ({fn_body_len} lines) into smaller functions",
                    lines=(i + 1, j + 1),
                    confidence=0.7,
                ))
            i = j + 1
        else:
            i += 1

    # type annotation
    untyped_count = 0
    for line in lines:
        m = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:\d+|'.*?'|\".*?\"|true|false|\[|\{)", line)
        if m and "::" not in line:
            untyped_count += 1
    if untyped_count >= 2:
        suggestions.append(RefactoringSuggestion(
            name="add_type_annotations",
            description=f"Add type annotations to {untyped_count} untyped variables",
            lines=(1, len(lines)),
            confidence=0.5,
        ))

    # sort imports
    import_count = len([l for l in lines if re.match(r"^\s*import\s+", l)])
    if import_count > 1:
        suggestions.append(RefactoringSuggestion(
            name="sort_imports",
            description="Sort and group imports alphabetically",
            lines=(1, len(lines)),
            confidence=0.9,
        ))

    # simplify boolean
    bool_patterns = sum(1 for line in lines if re.search(
        r"\b(true|false)\s+(and|or)\s+(true|false)\b|"
        r"\bnot\s+(true|false)\b|"
        r"\b\w+\s+==\s+(true|false)\b",
        line,
    ))
    if bool_patterns > 0:
        suggestions.append(RefactoringSuggestion(
            name="simplify_boolean_expression",
            description=f"Simplify {bool_patterns} boolean expression(s)",
            lines=(1, len(lines)),
            confidence=0.8,
        ))

    return suggestions

