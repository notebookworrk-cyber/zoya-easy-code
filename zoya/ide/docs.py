from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DocConfig:
    include_private: bool = False
    format: str = "markdown"
    include_source: bool = False
    ai_enhance: bool = False


@dataclass
class DocSection:
    title: str
    content: str = ""
    level: int = 1
    children: List[DocSection] = field(default_factory=list)

    def to_markdown(self) -> str:
        result: list[str] = []
        prefix = "#" * self.level
        result.append(f"{prefix} {self.title}")
        result.append("")
        if self.content:
            result.append(self.content)
            result.append("")
        for child in self.children:
            result.append(child.to_markdown())
        return "\n".join(result)

    def to_html(self) -> str:
        tag = f"h{min(self.level, 6)}"
        html: list[str] = [f"<{tag}>{_escape_html(self.title)}</{tag}>"]
        if self.content:
            html.append(f"<p>{_escape_html(self.content)}</p>")
        for child in self.children:
            html.append(child.to_html())
        return "\n".join(html)


class ApiReference:
    def __init__(self) -> None:
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.modules: List[Dict[str, Any]] = []

    def to_markdown(self) -> str:
        out: list[str] = ["# API Reference\n"]
        if self.modules:
            out.append("## Modules\n")
            for mod in self.modules:
                out.append(f"- `{mod['name']}`: {mod.get('doc', 'No description')}")
            out.append("")

        if self.functions:
            out.append("## Functions\n")
            for fn in self.functions:
                sig = _format_fn_signature(fn)
                out.append(f"### `{sig}`")
                if fn.get("doc"):
                    out.append("")
                    out.append(fn["doc"])
                if fn.get("params"):
                    out.append("")
                    out.append("**Parameters:**")
                    for p in fn["params"]:
                        pname = p["name"]
                        ptype = f": {p['type']}" if p.get("type") else ""
                        pdefault = f" = {p['default']}" if p.get("default") is not None else ""
                        pdoc = f" — {p['doc']}" if p.get("doc") else ""
                        out.append(f"- `{pname}{ptype}{pdefault}`{pdoc}")
                if fn.get("return_type"):
                    out.append("")
                    out.append(f"**Returns:** `{fn['return_type']}`")
                if fn.get("source") and fn.get("include_source"):
                    out.append("")
                    out.append("```zoya")
                    out.append(fn["source"])
                    out.append("```")
                out.append("")

        if self.classes:
            out.append("## Classes\n")
            for cls in self.classes:
                parent = f" extends {cls['parent']}" if cls.get("parent") else ""
                out.append(f"### class `{cls['name']}{parent}`")
                if cls.get("doc"):
                    out.append("")
                    out.append(cls["doc"])
                if cls.get("methods"):
                    out.append("")
                    out.append("**Methods:**")
                    for m in cls["methods"]:
                        sig = _format_fn_signature(m)
                        mdoc = f" — {m['doc']}" if m.get("doc") else ""
                        out.append(f"- `{sig}`{mdoc}")
                if cls.get("fields"):
                    out.append("")
                    out.append("**Fields:**")
                    for f in cls["fields"]:
                        ftype = f": {f['type']}" if f.get("type") else ""
                        fdoc = f" — {f['doc']}" if f.get("doc") else ""
                        out.append(f"- `{f['name']}{ftype}`{fdoc}")
                out.append("")

        return "\n".join(out)

    def to_html(self) -> str:
        sections: list[str] = ["<h1>API Reference</h1>"]

        if self.modules:
            sections.append("<h2>Modules</h2><ul>")
            for mod in self.modules:
                sections.append(f'<li><code>{_escape_html(mod["name"])}</code>: {_escape_html(mod.get("doc", "No description"))}</li>')
            sections.append("</ul>")

        if self.functions:
            sections.append("<h2>Functions</h2>")
            for fn in self.functions:
                sig = _format_fn_signature(fn)
                sections.append(f"<h3><code>{_escape_html(sig)}</code></h3>")
                if fn.get("doc"):
                    sections.append(f"<p>{_escape_html(fn['doc'])}</p>")
                if fn.get("params"):
                    sections.append("<p><strong>Parameters:</strong></p><ul>")
                    for p in fn["params"]:
                        pname = p["name"]
                        ptype = f": {p['type']}" if p.get("type") else ""
                        pdoc = f" \u2014 {p['doc']}" if p.get("doc") else ""
                        sections.append(f"<li><code>{_escape_html(pname)}{_escape_html(ptype)}</code>{_escape_html(pdoc)}</li>")
                    sections.append("</ul>")

        if self.classes:
            sections.append("<h2>Classes</h2>")
            for cls in self.classes:
                parent = f" extends {cls['parent']}" if cls.get("parent") else ""
                sections.append(f'<h3>class <code>{_escape_html(cls["name"])}{_escape_html(parent)}</code></h3>')
                if cls.get("doc"):
                    sections.append(f"<p>{_escape_html(cls['doc'])}</p>")

        return "\n".join(sections)

    def to_json(self) -> str:
        return json.dumps({
            "functions": self.functions,
            "classes": self.classes,
            "modules": self.modules,
        }, indent=2)


class DocGenerator:
    def __init__(self, config: Optional[DocConfig] = None, provider=None) -> None:
        self.config = config or DocConfig()
        self.provider = provider

    def generate(self, source: str, file_path: str = "") -> str:
        sections = self._build_sections(source, file_path)
        if self.config.format == "html":
            return "\n".join(s.to_html() for s in sections)
        if self.config.format == "json":
            return self._to_json(sections)
        return "\n".join(s.to_markdown() for s in sections)

    def generate_module_doc(self, source: str, module_name: str) -> str:
        doc_comments = parse_doc_comments(source)
        functions = _extract_functions(source, self.config.include_private)
        classes = _extract_classes(source)
        enums = _extract_enums(source)
        interfaces = _extract_interfaces(source)

        sections: list[str] = [f"# Module: `{module_name}`\n"]
        if module_name in doc_comments:
            sections.append(f"{doc_comments[module_name]}\n")

        if functions:
            sections.append("## Functions\n")
            for fn in functions:
                sig = _format_fn_signature(fn)
                doc = doc_comments.get(fn["name"], "")
                sections.append(f"### `{sig}`")
                if doc:
                    sections.append(f"\n{doc}")
                sections.append("")

        if classes:
            sections.append("## Classes\n")
            for cls in classes:
                parent = f" extends {cls['parent']}" if cls.get("parent") else ""
                doc = doc_comments.get(cls["name"], "")
                sections.append(f"### class `{cls['name']}{parent}`")
                if doc:
                    sections.append(f"\n{doc}")
                if cls.get("methods"):
                    sections.append("\n**Methods:**")
                    for m in cls["methods"]:
                        sig = _format_fn_signature(m)
                        mdoc = doc_comments.get(m["name"], "")
                        md = f" — {mdoc}" if mdoc else ""
                        sections.append(f"- `{sig}`{md}")
                sections.append("")

        if enums:
            sections.append("## Enums\n")
            for en in enums:
                sections.append(f"### enum `{en['name']}`")
                sections.append(f"\n**Variants:** {', '.join(en['variants'])}")
                sections.append("")

        if interfaces:
            sections.append("## Interfaces\n")
            for iface in interfaces:
                sections.append(f"### interface `{iface['name']}`")
                if iface.get("methods"):
                    sections.append("\n**Methods:**")
                    for m in iface["methods"]:
                        sections.append(f"- `{m}()`")
                sections.append("")

        return "\n".join(sections)

    def generate_function_doc(self, source: str, function_name: str, include_body: bool = False) -> str:
        functions = _extract_functions(source, True)
        doc_comments = parse_doc_comments(source)

        for fn in functions:
            if fn["name"] == function_name:
                sig = _format_fn_signature(fn)
                doc = doc_comments.get(fn["name"], "")
                out: list[str] = [f"# Function: `{sig}`\n"]
                if doc:
                    out.append(f"{doc}\n")
                if fn.get("params"):
                    out.append("## Parameters\n")
                    for p in fn["params"]:
                        pname = p["name"]
                        ptype = f": {p['type']}" if p.get("type") else ""
                        pdefault = f" = {p['default']}" if p.get("default") is not None else ""
                        pdoc = p.get("doc", "")
                        pd = f" — {pdoc}" if pdoc else ""
                        out.append(f"- `{pname}{ptype}{pdefault}`{pd}")
                    out.append("")
                if include_body and fn.get("body"):
                    out.append("## Body\n")
                    out.append("```zoya")
                    out.append(fn["body"])
                    out.append("```\n")
                return "\n".join(out)

        return f"Function '{function_name}' not found"

    def generate_class_doc(self, source: str, class_name: str) -> str:
        classes = _extract_classes(source)
        doc_comments = parse_doc_comments(source)

        for cls in classes:
            if cls["name"] == class_name:
                parent = f" extends {cls['parent']}" if cls.get("parent") else ""
                doc = doc_comments.get(cls["name"], "")
                out: list[str] = [f"# Class: `{cls['name']}{parent}`\n"]
                if doc:
                    out.append(f"{doc}\n")
                if cls.get("methods"):
                    out.append("## Methods\n")
                    for m in cls["methods"]:
                        sig = _format_fn_signature(m)
                        mdoc = doc_comments.get(m["name"], "")
                        md = f" — {mdoc}" if mdoc else ""
                        out.append(f"- `{sig}`{md}")
                    out.append("")
                if cls.get("fields"):
                    out.append("## Fields\n")
                    for f in cls["fields"]:
                        ftype = f": {f['type']}" if f.get("type") else ""
                        fdoc = f.get("doc", "")
                        fd = f" — {fdoc}" if fdoc else ""
                        out.append(f"- `{f['name']}{ftype}`{fd}")
                    out.append("")
                if self.config.include_source and cls.get("source_lines"):
                    out.append("## Source\n")
                    out.append("```zoya")
                    out.append("\n".join(cls["source_lines"]))
                    out.append("```\n")
                return "\n".join(out)

        return f"Class '{class_name}' not found"

    def generate_api_docs(self, sources: Dict[str, str]) -> str:
        api = ApiReference()

        for file_path, source in sources.items():
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            doc_comments = parse_doc_comments(source)
            functions = _extract_functions(source, self.config.include_private)
            classes = _extract_classes(source)

            mod_entry: Dict[str, Any] = {
                "name": module_name,
                "doc": doc_comments.get(module_name, ""),
                "path": file_path,
            }
            api.modules.append(mod_entry)

            for fn in functions:
                fn_entry: Dict[str, Any] = {
                    "name": fn["name"],
                    "params": fn.get("params", []),
                    "return_type": fn.get("return_type", ""),
                    "doc": doc_comments.get(fn["name"], ""),
                    "module": module_name,
                    "source": fn.get("body", ""),
                }
                api.functions.append(fn_entry)

            for cls in classes:
                cls_entry: Dict[str, Any] = cls.copy()
                cls_entry["doc"] = doc_comments.get(cls["name"], "")
                cls_entry["module"] = module_name
                if cls.get("methods"):
                    for m in cls["methods"]:
                        m["doc"] = doc_comments.get(m["name"], "")
                api.classes.append(cls_entry)

        if self.config.format == "html":
            return api.to_html()
        if self.config.format == "json":
            return api.to_json()
        return api.to_markdown()

    def generate_readme(self, sources: Dict[str, str], project_name: str) -> str:
        functions: list[dict] = []
        classes: list[dict] = []

        for file_path, source in sources.items():
            functions.extend(_extract_functions(source, False))
            classes.extend(_extract_classes(source))

        out: list[str] = [
            f"# {project_name}\n",
            "## Overview\n",
            "This project is built with **Zoya** — a beginner-friendly programming language for AI, automation, and game development.\n",
        ]

        if functions:
            out.append("## Functions\n")
            for fn in functions:
                sig = _format_fn_signature(fn)
                out.append(f"- `{sig}`")
            out.append("")

        if classes:
            out.append("## Classes\n")
            for cls in classes:
                parent = f" extends {cls['parent']}" if cls.get("parent") else ""
                out.append(f"- **`{cls['name']}{parent}`**")
                if cls.get("methods"):
                    for m in cls["methods"]:
                        sig = _format_fn_signature(m)
                        out.append(f"  - `{sig}`")
            out.append("")

        total_files = len(sources)
        total_fns = len(functions)
        total_classes = len(classes)
        out.append("## Stats\n")
        out.append(f"- Files: {total_files}")
        out.append(f"- Functions: {total_fns}")
        out.append(f"- Classes: {total_classes}")
        out.append("")

        out.append("## Getting Started\n")
        out.append("```bash")
        out.append("zoya main.zoya")
        out.append("```\n")

        out.append("---\n")
        out.append(f"*Generated by Zoya Documentation Generator*\n")

        return "\n".join(out)

    def generate_changelog(self, version: str, changes: List[str]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        out: list[str] = [
            "# Changelog\n",
            f"## [{version}] - {today}\n",
        ]

        feat: list[str] = []
        fix: list[str] = []
        chore: list[str] = []

        for change in changes:
            if change.lower().startswith("fix") or change.lower().startswith("bug"):
                fix.append(f"- {change}")
            elif change.lower().startswith("chore") or change.lower().startswith("docs") or change.lower().startswith("test"):
                chore.append(f"- {change}")
            else:
                feat.append(f"- {change}")

        if feat:
            out.append("### Added\n")
            out.extend(feat)
            out.append("")

        if fix:
            out.append("### Fixed\n")
            out.extend(fix)
            out.append("")

        if chore:
            out.append("### Changed\n")
            out.extend(chore)
            out.append("")

        return "\n".join(out)

    def _build_sections(self, source: str, file_path: str) -> List[DocSection]:
        doc_comments = parse_doc_comments(source)
        functions = _extract_functions(source, self.config.include_private)
        classes = _extract_classes(source)
        enums = _extract_enums(source)
        interfaces = _extract_interfaces(source)

        sections: List[DocSection] = []
        file_name = os.path.basename(file_path) if file_path else "source"
        mod_section = DocSection(title=f"Module: `{file_name}`", level=1)
        sections.append(mod_section)

        if functions:
            fn_section = DocSection(title="Functions", level=2, content="")
            for fn in functions:
                sig = _format_fn_signature(fn)
                doc = doc_comments.get(fn["name"], "")
                fn_section.children.append(
                    DocSection(title=f"`{sig}`", level=3, content=doc)
                )
            sections.append(fn_section)

        if classes:
            cls_section = DocSection(title="Classes", level=2, content="")
            for cls in classes:
                parent = f" extends {cls['parent']}" if cls.get("parent") else ""
                doc = doc_comments.get(cls["name"], "")
                cls_node = DocSection(
                    title=f"class `{cls['name']}{parent}`",
                    level=3,
                    content=doc,
                )
                if cls.get("methods"):
                    for m in cls["methods"]:
                        sig = _format_fn_signature(m)
                        mdoc = doc_comments.get(m["name"], "")
                        cls_node.children.append(
                            DocSection(title=f"`{sig}`", level=4, content=mdoc)
                        )
                cls_section.children.append(cls_node)
            sections.append(cls_section)

        if enums:
            enum_section = DocSection(title="Enums", level=2, content="")
            for en in enums:
                variants = ", ".join(en["variants"])
                enum_section.children.append(
                    DocSection(
                        title=f"enum `{en['name']}`",
                        level=3,
                        content=f"Variants: {variants}",
                    )
                )
            sections.append(enum_section)

        if interfaces:
            iface_section = DocSection(title="Interfaces", level=2, content="")
            for iface in interfaces:
                methods = ", ".join(iface.get("methods", []))
                iface_section.children.append(
                    DocSection(
                        title=f"interface `{iface['name']}`",
                        level=3,
                        content=f"Methods: {methods}",
                    )
                )
            sections.append(iface_section)

        return sections

    def _to_json(self, sections: List[DocSection]) -> str:
        def section_to_dict(s: DocSection) -> dict:
            return {
                "title": s.title,
                "content": s.content,
                "level": s.level,
                "children": [section_to_dict(c) for c in s.children],
            }
        return json.dumps([section_to_dict(s) for s in sections], indent=2)


def parse_doc_comments(source: str) -> Dict[str, str]:
    lines = source.split("\n")
    docs: Dict[str, str] = {}
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        comment_lines: list[str] = []
        j = i
        while j < len(lines):
            cl = lines[j].strip()
            if cl.startswith("//") or cl.startswith("#"):
                comment_lines.append(cl[2:].strip() if cl.startswith("//") else cl[1:].strip())
                j += 1
            elif cl == "":
                j += 1
            else:
                break

        if comment_lines:
            # Check for block comments
            if j < len(lines):
                next_line = lines[j].strip()
                fn_match = re.match(r"^fn\s+([a-zA-Z_][a-zA-Z0-9_]*)", next_line)
                cls_match = re.match(r"^class\s+([a-zA-Z_][a-zA-Z0-9_]*)", next_line)
                enum_match = re.match(r"^enum\s+([a-zA-Z_][a-zA-Z0-9_]*)", next_line)
                iface_match = re.match(r"^interface\s+([a-zA-Z_][a-zA-Z0-9_]*)", next_line)
                import_match = re.match(r'^import\s+"([^"]+)"', next_line)

                target = None
                if fn_match:
                    target = fn_match.group(1)
                elif cls_match:
                    target = cls_match.group(1)
                elif enum_match:
                    target = enum_match.group(1)
                elif iface_match:
                    target = iface_match.group(1)
                elif import_match:
                    target = import_match.group(1)

                if target:
                    docs[target] = "\n".join(comment_lines)
                    i = j
                    continue

        i += 1

    return docs


def _extract_functions(source: str, include_private: bool = False) -> List[Dict[str, Any]]:
    lines = source.split("\n")
    functions: List[Dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\s*fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{", line)
        if not m:
            i += 1
            continue

        name = m.group(1)
        raw_params = m.group(2).strip()

        if not include_private and name.startswith("_"):
            i += 1
            continue

        params: list[dict] = []
        if raw_params:
            for p in raw_params.split(","):
                p = p.strip()
                if not p:
                    continue
                pname = p
                ptype = ""
                pdefault: Optional[str] = None
                if "::" in p:
                    parts = p.split("::")
                    pname = parts[0].strip()
                    remaining = parts[1].strip()
                    if "=" in remaining:
                        type_parts = remaining.split("=")
                        ptype = type_parts[0].strip()
                        pdefault = type_parts[1].strip()
                    else:
                        ptype = remaining
                elif "=" in p:
                    eq_parts = p.split("=")
                    pname = eq_parts[0].strip()
                    pdefault = eq_parts[1].strip()
                params.append({
                    "name": pname,
                    "type": ptype,
                    "default": pdefault,
                })

        brace_count = 1
        body_lines: list[str] = []
        j = i + 1
        while j < len(lines) and brace_count > 0:
            brace_count += lines[j].count("{") - lines[j].count("}")
            if brace_count > 0:
                body_lines.append(lines[j])
            j += 1

        return_type = ""
        if body_lines:
            last_stmt = body_lines[-1].strip() if body_lines else ""
            ret_m = re.match(r"return\s+(.+)", last_stmt)
            if ret_m:
                ret_expr = ret_m.group(1)
                if re.match(r"^\d+$", ret_expr):
                    return_type = "int"
                elif re.match(r"^\d+\.\d+$", ret_expr):
                    return_type = "float"
                elif ret_expr.startswith('"'):
                    return_type = "str"
                elif ret_expr in ("true", "false"):
                    return_type = "bool"
                else:
                    return_type = "?"

        functions.append({
            "name": name,
            "params": params,
            "return_type": return_type,
            "body": "\n".join(body_lines),
            "line": i + 1,
            "doc": "",
        })

        i = j

    return functions


def _extract_classes(source: str) -> List[Dict[str, Any]]:
    lines = source.split("\n")
    classes: List[Dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+extends\s+([a-zA-Z_][a-zA-Z0-9_]*))?\s*\{", line)
        if not m:
            i += 1
            continue

        name = m.group(1)
        parent = m.group(2)

        brace_count = 1
        body_lines: list[str] = []
        methods: list[dict] = []
        fields: list[dict] = []
        j = i + 1

        while j < len(lines) and brace_count > 0:
            bl = lines[j]
            brace_count += bl.count("{") - bl.count("}")
            if brace_count > 0:
                body_lines.append(bl)

                field_m = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*::?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*;?\s*$", bl)
                if field_m:
                    fields.append({
                        "name": field_m.group(1),
                        "type": field_m.group(2),
                    })

                method_m = re.match(r"^\s*fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)", bl)
                if method_m:
                    mn = method_m.group(1)
                    raw_params = method_m.group(2).strip()
                    mparams: list[dict] = []
                    if raw_params:
                        for p in raw_params.split(","):
                            p = p.strip()
                            if p:
                                mparams.append({"name": p, "type": "", "default": None})
                    methods.append({"name": mn, "params": mparams, "return_type": ""})
            j += 1

        classes.append({
            "name": name,
            "parent": parent,
            "methods": methods,
            "fields": fields,
            "body": "\n".join(body_lines),
            "source_lines": [line] + body_lines,
        })

        i = j

    return classes


def _extract_enums(source: str) -> List[Dict[str, Any]]:
    lines = source.split("\n")
    enums: List[Dict[str, Any]] = []
    i = 0

    while i < len(lines):
        m = re.match(r"^\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{", lines[i])
        if m:
            name = m.group(1)
            brace_count = 1
            variants: list[str] = []
            j = i + 1
            while j < len(lines) and brace_count > 0:
                bl = lines[j]
                brace_count += bl.count("{") - bl.count("}")
                if brace_count > 0:
                    for v in re.findall(r"\b([A-Z][a-zA-Z0-9_]*)\b", bl):
                        if v not in variants:
                            variants.append(v)
                j += 1
            enums.append({"name": name, "variants": variants})
            i = j
        else:
            i += 1

    return enums


def _extract_interfaces(source: str) -> List[Dict[str, Any]]:
    lines = source.split("\n")
    interfaces: List[Dict[str, Any]] = []
    i = 0

    while i < len(lines):
        m = re.match(r"^\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{", lines[i])
        if m:
            name = m.group(1)
            brace_count = 1
            methods: list[str] = []
            j = i + 1
            while j < len(lines) and brace_count > 0:
                bl = lines[j]
                brace_count += bl.count("{") - bl.count("}")
                if brace_count > 0:
                    fn_m = re.search(r"fn\s+([a-zA-Z_][a-zA-Z0-9_]*)", bl)
                    if fn_m:
                        methods.append(fn_m.group(1))
                j += 1
            interfaces.append({"name": name, "methods": methods})
            i = j
        else:
            i += 1

    return interfaces


def _format_fn_signature(fn: dict) -> str:
    params = []
    for p in fn.get("params", []):
        pname = p["name"]
        ptype = f" :: {p['type']}" if p.get("type") else ""
        pdefault = f" = {p['default']}" if p.get("default") is not None else ""
        params.append(f"{pname}{ptype}{pdefault}")
    ret = f" -> {fn['return_type']}" if fn.get("return_type") else ""
    return f"{fn['name']}({', '.join(params)}){ret}"


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

