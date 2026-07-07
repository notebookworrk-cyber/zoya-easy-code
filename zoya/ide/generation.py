"""Code generation engine for auto-creating boilerplate and templates in the IDE."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from zoya.ai.llm import LLMProvider, MockProvider


@dataclass
class GenerationConfig:
    provider: LLMProvider | None = None
    temperature: float = 0.3
    max_tokens: int = 500
    style: str = "standard"


class CodeGenerator:
    def __init__(self, config: GenerationConfig | None = None):
        self.config = config or GenerationConfig()
        if self.config.provider is None:
            self.config.provider = MockProvider(
                responses={
                    "generate": self._default_generate_response(),
                    "function": self._default_function_response(),
                    "class": self._default_class_response(),
                    "test": self._default_test_response(),
                    "explain": self._default_explain_response(),
                    "translate": self._default_translate_response(),
                    "complete": self._default_complete_response(),
                }
            )

    def generate(self, description: str, context: str = "") -> str:
        prompt = (
            "You are a Zoya code generator. Generate valid Zoya code for the following description.\n"
            "Zoya is a Python-like language with syntax such as:\n"
            "- fn name(params) { body } for functions\n"
            "- let x = value for mutable variables, const x = value for constants\n"
            "- print(expr) for output, input(prompt) for input\n"
            "- if (cond) { ... } else { ... } for conditionals\n"
            "- while (cond) { ... }, for (init; cond; update) { ... }, for var in iterable { ... }\n"
            "- loop count { ... } for fixed iteration loops\n"
            "- class Name { ... }, interface Name { ... }, enum Name { Variant1, Variant2 }\n"
            "- match expr { pattern => result }, switch (expr) { case val { ... } default { ... } }\n"
            "- try { ... } catch (var) { ... }, throw expr\n"
            '- import "path", import "path" as alias\n'
            "- return expr, break, continue\n"
            "Return only the code, no explanation.\n\n"
        )
        if context:
            prompt += f"Context:\n{context}\n\n"
        prompt += f"Description: {description}\n\nGenerate Zoya code:"

        if isinstance(self.config.provider, MockProvider):
            mock_response = self._mock_code(f"fn generated() {{\n    // {description}\n}}")
            self.config.provider.responses["generate"] = mock_response

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        code = response.get("content", "")
        code = self._clean_code(code)
        return self._apply_style(code)

    def generate_function(
        self, description: str, name: str | None = None, params: list[str] | None = None
    ) -> str:
        param_str = ", ".join(params) if params else "..."
        name_str = name or "generated_function"
        prompt = (
            f"Generate a Zoya function named '{name_str}' with parameters ({param_str}).\n"
            f"Description: {description}\n"
            f"Return only the function code.\n"
        )

        if isinstance(self.config.provider, MockProvider):
            mock_code = f"fn {name_str}({param_str}) {{\n    // {description}\n    return null\n}}"
            self.config.provider.responses["function"] = mock_code

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        code = response.get("content", "")
        code = self._clean_code(code)
        return self._apply_style(code)

    def generate_class(self, description: str, name: str | None = None) -> str:
        name_str = name or "GeneratedClass"
        prompt = (
            f"Generate a Zoya class named '{name_str}'.\n"
            f"Description: {description}\n"
            f"Return only the class code.\n"
        )

        if isinstance(self.config.provider, MockProvider):
            mock_code = (
                f"class {name_str} {{\n"
                f"    fn init() {{\n"
                f"        // constructor\n"
                f"    }}\n"
                f"\n"
                f"    fn {name_str[0].lower() + name_str[1:] if len(name_str) > 1 else 'x'}() {{\n"
                f"        // {description}\n"
                f"        return null\n"
                f"    }}\n"
                f"}}"
            )
            self.config.provider.responses["class"] = mock_code

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        code = response.get("content", "")
        code = self._clean_code(code)
        return self._apply_style(code)

    def generate_test(self, description: str, code: str = "") -> str:
        prompt = f"Generate Zoya test code for the following:\n{description}\n"
        if code:
            prompt += f"\nCode under test:\n{code}\n"

        if isinstance(self.config.provider, MockProvider):
            mock_code = (
                f"fn test_{description.split()[0].lower() if description else 'feature'}() {{\n"
                f"    // Test: {description}\n"
                f"    let result = true\n"
                f"    if (result == false) {{\n"
                f'        print("FAIL: {description}")\n'
                f"    }} else {{\n"
                f'        print("PASS: {description}")\n'
                f"    }}\n"
                f"}}\n"
                f"\n"
                f"fn main() {{\n"
                f"    test_{description.split()[0].lower() if description else 'feature'}()\n"
                f"}}"
            )
            self.config.provider.responses["test"] = mock_code

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        code_out = response.get("content", "")
        return self._clean_code(code_out)

    def explain_code(self, code: str) -> str:
        prompt = (
            "Explain the following Zoya code. Be concise but thorough.\n"
            "Describe what each part does, the control flow, and any potential issues.\n\n"
            f"```\n{code}\n```\n"
        )

        if isinstance(self.config.provider, MockProvider):
            lines = code.strip().split("\n")
            explanation = self._mock_explain(lines)
            self.config.provider.responses["explain"] = explanation

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}], temperature=0.5, max_tokens=800
        )

        return response.get("content", "No explanation generated.")

    def translate_code(self, code: str, target_language: str = "python") -> str:
        prompt = (
            f"Translate the following Zoya code to {target_language}.\n"
            f"Maintain the same logic and structure.\n"
            f"Return only the translated code.\n\n"
            f"```\n{code}\n```\n"
        )

        if isinstance(self.config.provider, MockProvider):
            mock_translation = self._mock_translate(code, target_language)
            self.config.provider.responses["translate"] = mock_translation

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=self.config.max_tokens,
        )

        return self._clean_code(response.get("content", ""))

    def complete_code(self, code: str, cursor_pos: int) -> str:
        prompt = (
            "Complete the following partial Zoya code. "
            "The cursor is at position {cursor_pos} (0-indexed). "
            "Return only the completed code.\n\n"
            f"```\n{code}\n```\n"
            f"\nComplete from position {cursor_pos}:"
        )

        if isinstance(self.config.provider, MockProvider):
            self.config.provider.responses["complete"] = code

        response = self.config.provider.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=self.config.max_tokens,
        )

        return self._clean_code(response.get("content", code))

    def _clean_code(self, code: str) -> str:
        code = code.strip()
        if code.startswith("```"):
            first_newline = code.find("\n")
            code = code[first_newline + 1 :] if first_newline != -1 else code[3:]
        if code.endswith("```"):
            code = code[:-3]
        return code.strip()

    def _apply_style(self, code: str) -> str:
        if self.config.style == "compact":
            lines = [l for l in code.split("\n") if l.strip()]
            return "\n".join(lines)
        if self.config.style == "verbose":
            lines = code.split("\n")
            result: list[str] = []
            for line in lines:
                result.append(line)
                stripped = line.strip()
                if stripped.endswith("{"):
                    result.append("")
            return "\n".join(result)
        return code

    def _default_generate_response(self) -> str:
        return 'fn generated() {\n    print("Generated function")\n}'

    def _default_function_response(self) -> str:
        return "fn generated(params) {\n    return null\n}"

    def _default_class_response(self) -> str:
        return "class GeneratedClass {\n    fn init() {\n    }\n}"

    def _default_test_response(self) -> str:
        return (
            "fn test_feature() {\n"
            "    let result = true\n"
            "    if (result == false) {\n"
            '        print("FAIL")\n'
            "    } else {\n"
            '        print("PASS")\n'
            "    }\n"
            "}"
        )

    def _default_explain_response(self) -> str:
        return "This Zoya code defines functions and executes them."

    def _default_translate_response(self) -> str:
        return "def generated():\n    pass"

    def _default_complete_response(self) -> str:
        return ""

    def _mock_code(self, fallback: str) -> str:
        return fallback

    def _mock_explain(self, lines: list[str]) -> str:
        functions = []
        for line in lines:
            fn_match = re.match(r"\s*fn\s+(\w+)", line)
            if fn_match:
                functions.append(fn_match.group(1))
        if functions:
            return f"This code defines the following functions: {', '.join(functions)}."
        return "This is a Zoya program."

    def _mock_translate(self, code: str, target: str) -> str:
        result = code
        replacements: list[tuple[str, str]] = [
            (r"fn\s+(\w+)\s*\(", r"def \1("),
            (r"\blet\b", ""),
            (r"\bconst\b", ""),
            (r"\bprint\(", "print("),
            (r"\binput\(", "input("),
            (r"\band\b", "and"),
            (r"\bor\b", "or"),
            (r"\bnot\b", "not"),
            (r"\bnull\b", "None"),
            (r"\btrue\b", "True"),
            (r"\bfalse\b", "False"),
            (r"\bthis\b", "self"),
            (r"\bsuper\b", "super()"),
            (
                r"\bclass\s+(\w+)(?:\s*:\s*(\w+))?",
                r"class \1(\2):" if target == "python" else r"class \1",
            ),
            (r"\binterface\b", "# interface"),
            (r"\benum\b", "class"),
            (r"\bswitch\s*\(", "match "),
            (r"\bcase\b", "case"),
            (r"\bdefault\b", "case _"),
            (r"\bmatch\b", "match"),
            (r"\bloop\b", "for _ in range"),
            (r"//", "#"),
        ]
        for pattern, repl in replacements:
            result = re.sub(pattern, repl, result)
        return result


class CodeTemplate:
    @staticmethod
    def function_template(name: str, params: list[str], body: str) -> str:
        param_str = ", ".join(params)
        return f"fn {name}({param_str}) {{\n    {body}\n}}"

    @staticmethod
    def class_template(name: str, methods: list[dict[str, Any]]) -> str:
        lines: list[str] = [f"class {name} {{"]
        for method in methods:
            method_name = method.get("name", "method")
            method_params = method.get("params", [])
            method_body = method.get("body", "return null")
            param_str = ", ".join(method_params)
            lines.append(f"    fn {method_name}({param_str}) {{")
            for body_line in method_body.split("\n"):
                lines.append(f"        {body_line}")
            lines.append("    }")
            lines.append("")
        if lines[-1] == "":
            lines.pop()
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def loop_template(iterable: str, var: str = "item") -> str:
        return f"for {var} in {iterable} {{\n    // process {var}\n}}"

    @staticmethod
    def conditional_template(condition: str, body: str, else_body: str = "") -> str:
        result = f"if ({condition}) {{\n    {body}\n}}"
        if else_body:
            result += f" else {{\n    {else_body}\n}}"
        return result
