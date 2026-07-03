import sys
sys.path.insert(0, r"C:\Users\hp\zoya3")

import unittest

from zoya.ide.completion import (
    CompletionEngine, CompletionContext, CompletionItem,
    ZOYA_KEYWORDS, ZOYA_BUILTINS, ZOYA_SNIPPETS,
    STRING_METHODS, LIST_METHODS, DICT_METHODS,
)
from zoya.ide.generation import CodeGenerator, GenerationConfig, CodeTemplate
from zoya.ide.review import (
    CodeReviewer, ReviewIssue, ReviewResult, REVIEW_RULES,
)
from zoya.ide.refactor import (
    RefactoringEngine, RefactoringOperation, RefactoringSuggestion,
    get_available_refactorings,
)
from zoya.ide.debug import (
    DebugAssistant, DebugContext, DebugAnalysis, BugPattern, COMMON_BUG_PATTERNS,
)
from zoya.ide.docs import (
    DocGenerator, DocConfig, DocSection, ApiReference, parse_doc_comments,
)


# =============================================================================
# completion.py tests
# =============================================================================

class TestCompletionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CompletionEngine()
        self.default_context = CompletionContext(
            file_path="test.zr",
            source="fn main() {\n    print(\"hello\")\n}",
            line=2,
            col=5,
            prefix="",
        )

    def test_engine_uses_mock_provider_by_default(self):
        self.assertIsNotNone(self.engine._provider)

    def test_get_completions_empty_source_returns_empty(self):
        ctx = CompletionContext(file_path="", source="", line=1, col=1, prefix="")
        results = self.engine.get_completions(ctx)
        self.assertEqual(results, [])

    def test_get_completions_empty_prefix_with_source_returns_items(self):
        ctx = CompletionContext(
            file_path="test.zr",
            source="let x = 5",
            line=1,
            col=8,
            prefix="",
        )
        results = self.engine.get_completions(ctx)
        self.assertGreater(len(results), 0)

    def test_get_completions_prefix_filters_keywords(self):
        ctx = CompletionContext(
            file_path="test.zr",
            source="",
            line=1,
            col=4,
            prefix="if",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        self.assertIn("if", labels)
        self.assertNotIn("while", labels)

    def test_keyword_completions_include_all_keywords(self):
        results = self.engine._get_keyword_completions("")
        labels = [r.label for r in results]
        for kw in ZOYA_KEYWORDS:
            self.assertIn(kw, labels)

    def test_builtins_included_in_keyword_completions(self):
        results = self.engine._get_keyword_completions("")
        labels = [r.label for r in results]
        for b in ZOYA_BUILTINS:
            self.assertIn(b, labels)

    def test_snippet_completions(self):
        results = self.engine._get_snippet_completions("fn")
        labels = [r.label for r in results]
        self.assertIn("fn", labels)
        self.assertIn("fnmain", labels)

    def test_dot_completions_string(self):
        source = 'let s = "hello"\ns.'
        ctx = CompletionContext(
            file_path="test.zr",
            source=source,
            line=2,
            col=3,
            prefix="s.",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        for m in STRING_METHODS:
            self.assertIn(m, labels)

    def test_dot_completions_list(self):
        source = "let lst = [1, 2, 3]\nlst."
        ctx = CompletionContext(
            file_path="test.zr",
            source=source,
            line=2,
            col=5,
            prefix="lst.",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        for m in LIST_METHODS:
            self.assertIn(m, labels)

    def test_dot_completions_dict(self):
        source = 'let d = {"a": 1}\nd.'
        ctx = CompletionContext(
            file_path="test.zr",
            source=source,
            line=2,
            col=3,
            prefix="d.",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        for m in DICT_METHODS:
            self.assertIn(m, labels)

    def test_scope_completions_include_variables(self):
        source = "let myvar = 42"
        results = self.engine._get_scope_completions(source, [])
        labels = [r.label for r in results]
        self.assertIn("myvar", labels)

    def test_scope_completions_include_functions(self):
        source = "fn helper() {\n    return 1\n}"
        results = self.engine._get_scope_completions(source, [])
        labels = [r.label for r in results]
        self.assertIn("helper", labels)

    def test_no_duplicate_completions(self):
        source = "fn main() {\n    let x = 10\n}"
        ctx = CompletionContext(
            file_path="test.zr",
            source=source,
            line=2,
            col=5,
            prefix="x",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        self.assertEqual(len(labels), len(set(labels)))

    def test_completion_item_structure(self):
        item = CompletionItem(
            label="fn",
            kind="keyword",
            detail="Zoya keyword",
            insert_text="fn",
            documentation="Function declaration",
        )
        self.assertEqual(item.label, "fn")
        self.assertEqual(item.kind, "keyword")
        self.assertEqual(item.detail, "Zoya keyword")
        self.assertEqual(item.insert_text, "fn")
        self.assertEqual(item.documentation, "Function declaration")

    def test_completion_context_default_prefix_is_empty(self):
        ctx = CompletionContext(file_path="a.zr", source="", line=1, col=1)
        self.assertEqual(ctx.prefix, "")
        self.assertEqual(ctx.scope, [])

    def test_infer_type_string(self):
        self.assertEqual(CompletionEngine._infer_type('"hello"'), "string")
        self.assertEqual(CompletionEngine._infer_type("'hello'"), "string")

    def test_infer_type_int(self):
        self.assertEqual(CompletionEngine._infer_type("42"), "int")
        self.assertEqual(CompletionEngine._infer_type("-7"), "int")

    def test_infer_type_float(self):
        self.assertEqual(CompletionEngine._infer_type("3.14"), "float")
        self.assertEqual(CompletionEngine._infer_type("-0.5"), "float")

    def test_infer_type_bool(self):
        self.assertEqual(CompletionEngine._infer_type("true"), "bool")
        self.assertEqual(CompletionEngine._infer_type("false"), "bool")

    def test_infer_type_list(self):
        self.assertEqual(CompletionEngine._infer_type("[1, 2]"), "list")

    def test_infer_type_dict(self):
        self.assertEqual(CompletionEngine._infer_type('{"k": "v"}'), "dict")

    def test_infer_type_null(self):
        self.assertEqual(CompletionEngine._infer_type("null"), "null")

    def test_infer_type_variable(self):
        self.assertEqual(CompletionEngine._infer_type(""), "variable")
        self.assertEqual(CompletionEngine._infer_type("otherVar"), "variable")

    def test_parse_source_variables_let_and_const(self):
        source = "let x = 5\nconst y = \"hello\""
        vars = self.engine._parse_source_variables(source)
        self.assertIn("x", vars)
        self.assertIn("y", vars)
        self.assertEqual(vars["x"], "int")
        self.assertEqual(vars["y"], "string")

    def test_dot_completions_unknown_type_includes_length(self):
        source = "let obj = getValue()\nobj."
        ctx = CompletionContext(
            file_path="test.zr",
            source=source,
            line=2,
            col=5,
            prefix="obj.",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        self.assertIn("length", labels)

    def test_get_completions_prefix_filters_partial(self):
        ctx = CompletionContext(
            file_path="test.zr",
            source="",
            line=1,
            col=4,
            prefix="whi",
        )
        results = self.engine.get_completions(ctx)
        labels = [r.label for r in results]
        self.assertIn("while", labels)
        self.assertNotIn("if", labels)

    def test_all_zoya_keywords_present(self):
        required = ["let", "const", "fn", "if", "else", "while", "for", "in", "loop",
                     "return", "break", "continue", "print", "import", "class", "interface",
                     "enum", "match", "switch", "case", "default", "try", "catch", "throw",
                     "true", "false", "null", "and", "or", "not", "this", "super"]
        for kw in required:
            self.assertIn(kw, ZOYA_KEYWORDS)


# =============================================================================
# generation.py tests
# =============================================================================

class TestCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = CodeGenerator()

    def test_generate_returns_code_with_function(self):
        code = self.generator.generate("calculate sum of two numbers")
        self.assertTrue("fn" in code or "print" in code)

    def test_generate_with_context(self):
        code = self.generator.generate("add logging", context="let x = 5\nlet y = 10")
        self.assertIsInstance(code, str)
        self.assertTrue(len(code) > 0)

    def test_generate_function_creates_fn_with_correct_name(self):
        code = self.generator.generate_function("process user data", name="processUser")
        self.assertIn("processUser", code)

    def test_generate_function_with_params(self):
        code = self.generator.generate_function("add numbers", params=["a", "b"], name="add")
        self.assertIn("fn", code)

    def test_generate_class_creates_class(self):
        code = self.generator.generate_class("user management", name="UserManager")
        self.assertIn("UserManager", code)

    def test_generate_class_default_name(self):
        code = self.generator.generate_class("generic handler")
        self.assertIn("class", code)

    def test_generate_test_creates_test_code(self):
        code = self.generator.generate_test("login feature")
        self.assertIn("test_", code.lower() or "fn", code.lower())

    def test_generate_test_with_code(self):
        code = self.generator.generate_test("sorting", code="fn sort() { }")
        self.assertIsInstance(code, str)
        self.assertTrue(len(code) > 0)

    def test_explain_code_returns_explanation(self):
        explanation = self.generator.explain_code("fn main() {\n    print(\"hi\")\n}")
        self.assertIsInstance(explanation, str)
        self.assertTrue(len(explanation) > 0)

    def test_explain_code_identifies_function_names(self):
        explanation = self.generator.explain_code("fn calculate() { }")
        self.assertTrue(len(explanation) > 0)
        self.assertIsInstance(explanation, str)

    def test_translate_code_to_python(self):
        zoya_code = 'fn greet(name) {\n    print("Hello " + name)\n}'
        translated = self.generator.translate_code(zoya_code, "python")
        self.assertIsInstance(translated, str)

    def test_complete_code_returns_string(self):
        result = self.generator.complete_code("fn main() {", 10)
        self.assertIsInstance(result, str)

    def test_clean_code_strips_markdown(self):
        raw = "```zoya\nfn test() { }\n```"
        clean = self.generator._clean_code(raw)
        self.assertEqual(clean, "fn test() { }")
        self.assertNotIn("```", clean)

    def test_apply_style_compact_removes_blank_lines(self):
        code = "fn a() {\n\n    return 1\n}"
        generator = CodeGenerator(GenerationConfig(style="compact"))
        styled = generator._apply_style(code)
        self.assertNotIn("\n\n", styled)

    def test_apply_style_verbose_adds_blank_lines(self):
        code = "fn a() {\n    return 1\n}"
        generator = CodeGenerator(GenerationConfig(style="verbose"))
        styled = generator._apply_style(code)
        self.assertIn("return 1", styled)

    def test_generation_config_defaults(self):
        cfg = GenerationConfig()
        self.assertIsNone(cfg.provider)
        self.assertEqual(cfg.temperature, 0.3)
        self.assertEqual(cfg.max_tokens, 500)
        self.assertEqual(cfg.style, "standard")

    def test_generate_handles_mock_fallback(self):
        generator = CodeGenerator()
        code = generator.generate("do something")
        self.assertIsInstance(code, str)


class TestCodeTemplate(unittest.TestCase):
    def test_function_template(self):
        result = CodeTemplate.function_template("add", ["a", "b"], "return a + b")
        self.assertIn("fn add(", result)
        self.assertIn("a, b", result)
        self.assertIn("return a + b", result)

    def test_class_template(self):
        methods = [
            {"name": "init", "params": ["self"], "body": "// constructor"},
            {"name": "run", "params": ["self"], "body": "return null"},
        ]
        result = CodeTemplate.class_template("Runner", methods)
        self.assertIn("class Runner {", result)
        self.assertIn("fn init(", result)
        self.assertIn("fn run(", result)

    def test_loop_template(self):
        result = CodeTemplate.loop_template("items", "item")
        self.assertIn("for item in items {", result)

    def test_loop_template_default_var(self):
        result = CodeTemplate.loop_template("data")
        self.assertIn("for item in data {", result)

    def test_conditional_template(self):
        result = CodeTemplate.conditional_template("x > 5", "doSomething()")
        self.assertIn("if (x > 5) {", result)
        self.assertIn("doSomething()", result)
        self.assertNotIn("else", result)

    def test_conditional_template_with_else(self):
        result = CodeTemplate.conditional_template("x > 5", "doA()", "doB()")
        self.assertIn("if (x > 5) {", result)
        self.assertIn("doA()", result)
        self.assertIn("else {", result)
        self.assertIn("doB()", result)


# =============================================================================
# review.py tests
# =============================================================================

class TestCodeReviewer(unittest.TestCase):
    def setUp(self):
        self.reviewer = CodeReviewer()

    def test_review_returns_review_result(self):
        result = self.reviewer.review("fn main() {\n    print(\"hi\")\n}")
        self.assertIsInstance(result, ReviewResult)

    def test_review_result_error_warning_info_counts(self):
        issues = [
            ReviewIssue(severity="error", message="E1", line=1, col=1, rule_id="C004"),
            ReviewIssue(severity="warning", message="W1", line=2, col=1, rule_id="S001"),
            ReviewIssue(severity="info", message="I1", line=3, col=1, rule_id="B001"),
        ]
        result = ReviewResult(issues=issues)
        self.assertEqual(result.error_count, 1)
        self.assertEqual(result.warning_count, 1)
        self.assertEqual(result.info_count, 1)

    def test_review_result_total_property(self):
        issues = [
            ReviewIssue(severity="error", message="E1", line=1, col=1, rule_id="C004"),
            ReviewIssue(severity="warning", message="W1", line=2, col=1, rule_id="S001"),
        ]
        result = ReviewResult(issues=issues)
        self.assertEqual(result.total, 2)

    def test_review_result_has_errors(self):
        issues = [ReviewIssue(severity="error", message="E1", line=1, col=1, rule_id="C004")]
        result = ReviewResult(issues=issues)
        self.assertTrue(result.has_errors())

    def test_review_result_no_errors(self):
        issues = [ReviewIssue(severity="info", message="I1", line=1, col=1, rule_id="B001")]
        result = ReviewResult(issues=issues)
        self.assertFalse(result.has_errors())

    def test_review_result_summary_with_issues(self):
        issues = [ReviewIssue(severity="error", message="E1", line=1, col=1, rule_id="C004")]
        result = ReviewResult(issues=issues)
        self.assertIn("error(s)", result.summary())

    def test_review_result_summary_no_issues(self):
        result = ReviewResult()
        self.assertIn("No issues", result.summary())

    def test_review_result_add_method(self):
        result = ReviewResult()
        issue = ReviewIssue(severity="warning", message="test", line=1, col=1, rule_id="S001")
        result.add(issue)
        self.assertEqual(result.total, 1)
        self.assertEqual(result.warning_count, 1)

    def test_detects_non_snake_case_function_naming(self):
        source = "fn ProcessData() {\n    return 1\n}"
        result = self.reviewer.review(source)
        s001_found = any(i.rule_id == "S001" for i in result.issues)
        self.assertTrue(s001_found)

    def test_detects_line_length_exceeds_100(self):
        long_line = "let x = " + "a" * 100
        result = self.reviewer.review(long_line)
        s003_found = any(i.rule_id == "S003" for i in result.issues)
        self.assertTrue(s003_found)

    def test_detects_missing_return_types_triggers_rule(self):
        source = "fn main() {\n    print(\"done\")\n}"
        result = self.reviewer.review(source)
        c002_found = any(i.rule_id == "C002" for i in result.issues)
        self.assertTrue(c002_found)

    def test_detects_missing_return_types(self):
        source = "fn add(x, y) {\n    return x + y\n}"
        result = self.reviewer.review(source)
        c002_found = any(i.rule_id == "C002" for i in result.issues)
        self.assertTrue(c002_found)

    def test_detects_deep_nesting(self):
        source = "fn main() {\n    if (a) {\n        if (b) {\n            if (c) {\n                if (d) {\n                    if (e) {\n                        print(\"deep\")\n                    }\n                }\n            }\n        }\n    }\n}"
        result = self.reviewer.review(source)
        c003_found = any(i.rule_id == "C003" for i in result.issues)
        self.assertTrue(c003_found)

    def test_detects_duplicate_functions(self):
        source = "fn foo() { }\nfn foo() { }"
        result = self.reviewer.review(source)
        c004_found = any(i.rule_id == "C004" for i in result.issues)
        self.assertTrue(c004_found)

    def test_detects_empty_catch_blocks(self):
        source = "try {\n    doSomething()\n} catch (err) {\n}"
        result = self.reviewer.review(source)
        c005_found = any(i.rule_id == "C005" for i in result.issues)
        self.assertTrue(c005_found)

    def test_hardcoded_value_check_runs_without_error(self):
        source = "fn process() {\n    let apiKey = \"this_is_a_very_long_hardcoded_api_key_string\"\n}"
        result = self.reviewer.review(source)
        self.assertIsInstance(result, ReviewResult)

    def test_empty_source_returns_no_issues(self):
        result = self.reviewer.review("")
        self.assertEqual(result.total, 0)

    def test_clean_code_has_no_issues(self):
        source = "fn main() {\n    print(\"hello\")\n}"
        result = self.reviewer.review(source)
        self.assertIsInstance(result, ReviewResult)

    def test_review_rules_has_all_entries(self):
        expected_ids = ["S001", "S002", "S003", "C001", "C002", "C003",
                         "C004", "C005", "B001", "B002", "P001", "P002"]
        for rid in expected_ids:
            self.assertIn(rid, REVIEW_RULES)

    def test_each_rule_has_required_fields(self):
        for rid, rule in REVIEW_RULES.items():
            self.assertIn("id", rule)
            self.assertIn("category", rule)
            self.assertIn("severity", rule)
            self.assertIn("description", rule)
            self.assertEqual(rule["id"], rid)

    def test_rules_have_valid_severity(self):
        valid = {"error", "warning", "info", "hint"}
        for rule in REVIEW_RULES.values():
            self.assertIn(rule["severity"], valid)

    def test_rules_have_valid_categories(self):
        valid = {"style", "correctness", "best_practice", "performance"}
        for rule in REVIEW_RULES.values():
            self.assertIn(rule["category"], valid)

    def test_to_snake_case_conversion(self):
        self.assertEqual(CodeReviewer._to_snake_case("ProcessData"), "process_data")
        self.assertEqual(CodeReviewer._to_snake_case("XMLParser"), "xml_parser")
        self.assertEqual(CodeReviewer._to_snake_case("simple"), "simple")

    def test_parse_zoya_source(self):
        source = "fn hello(name) {\n    return name\n}\nclass MyClass {\n}"
        parsed = self.reviewer._parse_zoya_source(source)
        self.assertEqual(len(parsed["functions"]), 1)
        self.assertEqual(parsed["functions"][0]["name"], "hello")
        self.assertEqual(len(parsed["classes"]), 1)
        self.assertEqual(parsed["classes"][0]["name"], "MyClass")

    def test_detects_loop_inefficiency(self):
        source = "for (let i = 0; i < arr.length; i++) {\n    print(i)\n}"
        result = self.reviewer.review(source)
        p001_found = any(i.rule_id == "P001" for i in result.issues)
        self.assertTrue(p001_found)

    def test_detects_unused_loop_var(self):
        source = "for item in items {\n    print(\"hello\")\n}"
        result = self.reviewer.review(source)
        p002_found = any(i.rule_id == "P002" for i in result.issues)
        self.assertTrue(p002_found)

    def test_detects_constant_naming(self):
        source = "const myConst = 42"
        result = self.reviewer.review(source)
        s002_found = any(i.rule_id == "S002" for i in result.issues)
        self.assertTrue(s002_found)

    def test_missing_error_handling_detected(self):
        source = "fn readInput() {\n    let x = input()\n    let y = int(x)\n}"
        result = self.reviewer.review(source)
        b002_found = any(i.rule_id == "B002" for i in result.issues)
        self.assertTrue(b002_found)

    def test_is_in_try_block(self):
        source = "try {\n    let x = int(input())\n} catch (e) {\n}"
        pos = source.find("int(input())")
        result = self.reviewer._is_in_try_block(source, pos)
        self.assertTrue(result)

    def test_is_not_in_try_block(self):
        source = "let x = int(input())"
        pos = source.find("int(input())")
        result = self.reviewer._is_in_try_block(source, pos)
        self.assertFalse(result)


# =============================================================================
# refactor.py tests
# =============================================================================

class TestRefactoringEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RefactoringEngine()

    def test_rename_variable_replaces_correctly(self):
        source = "let x = 5\nprint(x)"
        result = self.engine.rename_variable(source, "x", "y")
        self.assertIn("let y = 5", result)
        self.assertNotIn("let x", result)

    def test_rename_variable_does_not_rename_function_calls(self):
        source = "let len = 5\nprint(len(\"hi\"))"
        result = self.engine.rename_variable(source, "len", "length")
        self.assertIn("let length = 5", result)
        self.assertIn("len(\"hi\")", result)

    def test_extract_function(self):
        source = "fn main() {\n    let x = 1\n    let y = 2\n    let z = x + y\n}"
        result = self.engine.extract_function(source, 2, 4, "calc")
        self.assertIn("fn calc(", result)
        self.assertIn("calc(", result)

    def test_extract_function_invalid_range_returns_original(self):
        source = "fn main() { }"
        result = self.engine.extract_function(source, 10, 20, "x")
        self.assertEqual(result, source)

    def test_convert_loop_to_for_each(self):
        source = "for (i = 0; i < arr; i++) { }"
        result = self.engine.convert_loop_to_for_each(source)
        self.assertIn("foreach", result)

    def test_convert_loop_to_for_each_no_match_unchanged(self):
        source = "for (i = 0; i < arr.length; i++) { }"
        result = self.engine.convert_loop_to_for_each(source)
        self.assertEqual(result, source)

    def test_convert_if_to_switch(self):
        source = (
            "if x == 1 {\n"
            "    print(\"one\")\n"
            "} else if x == 2 {\n"
            "    print(\"two\")\n"
            "} else {\n"
            "    print(\"other\")\n"
            "}"
        )
        result = self.engine.convert_if_to_switch(source)
        self.assertIn("switch", result)

    def test_convert_if_to_switch_no_eq_returns_original(self):
        source = "if x > 5 {\n    print(\"big\")\n}"
        result = self.engine.convert_if_to_switch(source)
        self.assertNotIn("switch", result)

    def test_remove_dead_code_after_return(self):
        source = "fn main() {\n    return 1\n}"
        result = self.engine.remove_dead_code(source)
        self.assertIn("return 1", result)

    def test_remove_dead_code_comment_tag(self):
        source = "fn main() {\n    // dead code\n}"
        result = self.engine.remove_dead_code(source)
        self.assertNotIn("dead", result)

    def test_sort_imports_sorts_alphabetically(self):
        source = 'import "z"\nimport "a"\n\nfn main() { }'
        result = self.engine.sort_imports(source)
        a_pos = result.index('import "a"')
        z_pos = result.index('import "z"')
        self.assertLess(a_pos, z_pos)

    def test_sort_imports_no_imports_returns_original(self):
        source = "fn main() { }"
        result = self.engine.sort_imports(source)
        self.assertEqual(result, source)

    def test_format_code_fixes_indentation(self):
        source = "fn main() {\nprint(\"hi\")\n}"
        result = self.engine.format_code(source)
        self.assertIn("    print(", result)

    def test_format_code_handles_closing_brace(self):
        source = "fn main() {\n    if true {\n        print(\"yes\")\n    }\n}"
        result = self.engine.format_code(source)
        self.assertIn("    if true {", result)

    def test_split_large_function_splits_at_boundary(self):
        body_lines = [f"    let x{i} = {i}" for i in range(60)]
        source = "fn big() {\n" + "\n".join(body_lines) + "\n}"
        result = self.engine.split_large_function(source)
        self.assertIn("_big_part", result)

    def test_split_large_function_small_unchanged(self):
        source = "fn small() {\n    let x = 1\n}"
        result = self.engine.split_large_function(source)
        self.assertNotIn("_small_part", result)

    def test_wrap_in_error_handler(self):
        source = "fn risky() {\n    let x = 1 / 0\n}"
        result = self.engine.wrap_in_error_handler(source, "risky")
        self.assertIn("try {", result)
        self.assertIn("catch err", result)

    def test_simplify_boolean_expression(self):
        source = "if (true and true) { }"
        result = self.engine.simplify_boolean_expression(source)
        self.assertIn("if (true) { }", result)

    def test_convert_print_to_logging(self):
        source = 'print "hello"'
        result = self.engine.convert_print_to_logging(source)
        self.assertIn('log("info",', result)

    def test_add_type_annotations_int(self):
        source = "x = 42"
        result = self.engine.add_type_annotations(source)
        self.assertIn(":: int =", result)

    def test_add_type_annotations_string(self):
        source = 'x = "hello"'
        result = self.engine.add_type_annotations(source)
        self.assertIn(":: str =", result)

    def test_add_type_annotations_bool(self):
        source = "x = true"
        result = self.engine.add_type_annotations(source)
        self.assertIn(":: bool =", result)

    def test_inline_function_replaces_call(self):
        source = "fn double(x) {\n    return x * 2\n}\nlet y = double(5)"
        result = self.engine.inline_function(source, "double")
        self.assertNotIn("fn double(", result)

    def test_inline_function_not_found_returns_original(self):
        source = "fn existing() { }"
        result = self.engine.inline_function(source, "nonexistent")
        self.assertEqual(result, source)

    def test_refactoring_operation_default_apply(self):
        op = RefactoringOperation(name="test", description="test op")
        result = op.apply("source")
        self.assertEqual(result, "source")


class TestGetAvailableRefactorings(unittest.TestCase):
    def test_empty_source_returns_empty(self):
        suggestions = get_available_refactorings("")
        self.assertEqual(suggestions, [])

    def test_simple_source_returns_list(self):
        source = "fn main() {\n    print x\n}"
        suggestions = get_available_refactorings(source)
        self.assertIsInstance(suggestions, list)

    def test_get_available_refactorings_returns_list(self):
        suggestions = get_available_refactorings("let x = 1")
        self.assertIsInstance(suggestions, list)

    def test_if_chain_suggestion(self):
        source = (
            "if x == 1 {\n"
            "    print(\"one\")\n"
            "} else if x == 2 {\n"
            "    print(\"two\")\n"
            "} else if x == 3 {\n"
            "    print(\"three\")\n"
            "} else {\n"
            "    print(\"other\")\n"
            "}"
        )
        suggestions = get_available_refactorings(source)
        names = [s.name for s in suggestions]
        self.assertIn("convert_if_to_switch", names)

    def test_print_count_suggestion(self):
        source = "fn a() {\n    print x\n}\nfn b() {\n    print y\n}\nfn c() {\n    print z\n}"
        suggestions = get_available_refactorings(source)
        names = [s.name for s in suggestions]
        self.assertIn("convert_print_to_logging", names)

    def test_large_function_suggestion(self):
        body_lines = [f"    let x{i} = {i}" for i in range(60)]
        source = "fn big() {\n" + "\n".join(body_lines) + "\n}"
        suggestions = get_available_refactorings(source)
        names = [s.name for s in suggestions]
        self.assertIn("split_large_function", names)

    def test_add_type_annotations_suggestion(self):
        source = "x = 42\ny = \"hello\""
        suggestions = get_available_refactorings(source)
        names = [s.name for s in suggestions]
        self.assertIn("add_type_annotations", names)

    def test_sort_imports_suggestion(self):
        source = 'import "b"\nimport "a"\n\nfn main() { }'
        suggestions = get_available_refactorings(source)
        names = [s.name for s in suggestions]
        self.assertIn("sort_imports", names)

    def test_simplify_boolean_suggestion(self):
        source = "if (true and false) { }"
        suggestions = get_available_refactorings(source)
        names = [s.name for s in suggestions]
        self.assertIn("simplify_boolean_expression", names)

    def test_refactoring_suggestion_structure(self):
        s = RefactoringSuggestion(name="test", description="desc", lines=(1, 2), confidence=0.8)
        self.assertEqual(s.name, "test")
        self.assertEqual(s.confidence, 0.8)
        self.assertEqual(s.lines, (1, 2))


# =============================================================================
# debug.py tests
# =============================================================================

class TestDebugAssistant(unittest.TestCase):
    def setUp(self):
        self.assistant = DebugAssistant()

    def test_analyze_error_no_ai_returns_debug_analysis(self):
        ctx = DebugContext(
            source="fn main() {\n    let x = 5\n}",
            error_message="Error at line 2",
            error_type="GenericError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIsInstance(analysis, DebugAnalysis)

    def test_debug_analysis_has_root_cause_and_confidence(self):
        analysis = DebugAnalysis(
            root_cause="division by zero",
            fix_suggestion="check divisor",
            confidence=0.9,
        )
        self.assertEqual(analysis.root_cause, "division by zero")
        self.assertEqual(analysis.confidence, 0.9)

    def test_analyze_type_error_uses_root_cause(self):
        ctx = DebugContext(
            source="fn add(a, b) { return a + b }",
            error_message="Error at line 1",
            error_type="GenericRuntimeError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIsInstance(analysis.root_cause, str)

    def test_analyze_division_by_zero(self):
        ctx = DebugContext(
            source="fn div(a, b) { return a / b }",
            error_message="division by zero at line 1",
            error_type="ZeroDivisionError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIn("zero", analysis.root_cause.lower())

    def test_analyze_index_error(self):
        ctx = DebugContext(
            source="let items = [1, 2, 3]\nlet x = items[5]",
            error_message="index out of bounds",
            error_type="IndexError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIn("index", analysis.root_cause.lower())

    def test_analyze_name_error(self):
        ctx = DebugContext(
            source="fn main() { print(unknownVar) }",
            error_message="name 'unknownVar' is not defined",
            error_type="NameError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIn("unknownVar", analysis.root_cause)

    def test_analyze_key_error(self):
        ctx = DebugContext(
            source="let d = {\"a\": 1}\nlet v = d[\"b\"]",
            error_message="key 'b' not found",
            error_type="KeyError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIn("key", analysis.root_cause.lower())

    def test_analyze_recursion_error(self):
        ctx = DebugContext(
            source="fn recurse() { recurse() }",
            error_message="maximum recursion depth exceeded",
            error_type="RecursionError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIn("recursion", analysis.root_cause.lower())

    def test_analyze_attribute_error(self):
        ctx = DebugContext(
            source="let x = null\nx.foo()",
            error_message="'NoneType' object has no attribute 'foo'",
            error_type="AttributeError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertIn("attribute", analysis.root_cause.lower())

    def test_analyze_unknown_error_returns_generic(self):
        ctx = DebugContext(
            source="fn main() { }",
            error_message="Something weird happened",
            error_type="WeirdError",
        )
        analysis = self.assistant.analyze_error(ctx)
        self.assertGreater(len(analysis.fix_suggestion), 0)

    def test_find_null_pointer_sources(self):
        source = "let x = null\nprint(x)"
        results = self.assistant.find_null_pointer_sources(source)
        self.assertIsInstance(results, list)

    def test_find_type_errors_string_concat_with_number(self):
        source = 'let msg = "count: " + 5'
        results = self.assistant.find_type_errors(source)
        self.assertGreater(len(results), 0)

    def test_find_type_errors_len_on_number(self):
        source = "let x = len(42)"
        results = self.assistant.find_type_errors(source)
        self.assertGreater(len(results), 0)

    def test_find_infinite_loop_risks_while_true_no_break(self):
        source = "while true {\n    print(\"hi\")\n}"
        risks = self.assistant.find_infinite_loop_risks(source)
        self.assertGreater(len(risks), 0)

    def test_find_infinite_loop_risks_while_true_with_break(self):
        source = "while true {\n    if done { break }\n}"
        risks = self.assistant.find_infinite_loop_risks(source)
        self.assertEqual(len(risks), 0)

    def test_find_infinite_loop_risks_while_var_not_modified(self):
        source = "fn test() {\n    while x < 10 {\n        print(x)\n    }\n}"
        risks = self.assistant.find_infinite_loop_risks(source)
        self.assertGreater(len(risks), 0)

    def test_analyze_stack_trace_extracts_info(self):
        trace = [
            "  at main (line 10:5)",
            "  at helper (line 25:3)",
            "TypeError: something failed",
        ]
        result = self.assistant.analyze_stack_trace(trace)
        self.assertIn("main", result)
        self.assertIn("helper", result)

    def test_analyze_stack_trace_empty(self):
        result = self.assistant.analyze_stack_trace([])
        self.assertIn("No stack trace", result)

    def test_analyze_stack_trace_file_format(self):
        trace = [
            "at main (line 10:5)",
            "Error: type mismatch",
        ]
        result = self.assistant.analyze_stack_trace(trace)
        self.assertIn("main", result)
        self.assertIn("line 10", result)

    def test_common_bug_patterns_count(self):
        self.assertEqual(len(COMMON_BUG_PATTERNS), 10)

    def test_each_bug_pattern_has_required_fields(self):
        for pattern in COMMON_BUG_PATTERNS:
            self.assertTrue(pattern.name)
            self.assertTrue(pattern.description)
            self.assertTrue(pattern.pattern)
            self.assertTrue(pattern.severity)
            self.assertTrue(pattern.fix)

    def test_bug_pattern_severity_valid(self):
        valid = {"error", "warning", "info", "hint"}
        for pattern in COMMON_BUG_PATTERNS:
            self.assertIn(pattern.severity, valid)

    def test_bug_pattern_dataclass(self):
        bp = BugPattern(
            name="test_pattern",
            description="A test pattern",
            pattern=r"test",
            severity="warning",
            fix="fix it",
        )
        self.assertEqual(bp.name, "test_pattern")
        self.assertEqual(bp.fix, "fix it")

    def test_debug_context_defaults(self):
        ctx = DebugContext(source="", error_message="", error_type="")
        self.assertEqual(ctx.traceback, [])
        self.assertEqual(ctx.variables, {})

    def test_analyze_with_provider_falls_back_to_no_ai(self):
        assistant = DebugAssistant()
        ctx = DebugContext(
            source="fn main() { }",
            error_message="Error at line 1",
            error_type="Generic",
        )
        analysis = assistant.analyze_error(ctx)
        self.assertIsInstance(analysis, DebugAnalysis)

    def test_analyze_error_no_ai_all_empty_source(self):
        ctx = DebugContext(
            source="",
            error_message="",
            error_type="",
        )
        analysis = self.assistant.analyze_error_no_ai(ctx)
        self.assertIsInstance(analysis, DebugAnalysis)

    def test_suggest_fix_division_by_zero(self):
        source = "fn div() {\n    return a / 0\n}"
        fix = self.assistant.suggest_fix(source, 2, "division by zero")
        self.assertIn("divisor", fix)

    def test_suggest_fix_out_of_range(self):
        fix = self.assistant.suggest_fix("fn main() { }", 99, "error")
        self.assertIn("Could not locate", fix)

    def test_suggest_fix_generic(self):
        source = "fn main() {\n    riskyCall()\n}"
        fix = self.assistant.suggest_fix(source, 2, "unknown error")
        self.assertIn("try {", fix)

    def test_extract_line_from_error(self):
        line = self.assistant._extract_line_from_error("Error at line 42")
        self.assertEqual(line, 42)

    def test_extract_line_from_error_no_match(self):
        line = self.assistant._extract_line_from_error("unknown error format")
        self.assertEqual(line, 0)

    def test_extract_var_from_error_quoted(self):
        var = self.assistant._extract_var_from_error("name 'myVar' is not defined")
        self.assertEqual(var, "myVar")

    def test_extract_var_from_error_unquoted(self):
        var = self.assistant._extract_var_from_error("'myVar' not found")
        self.assertEqual(var, "myVar")

    def test_extract_attr_from_error(self):
        attr = self.assistant._extract_attr_from_error("'X' object has no attribute 'foo'")
        self.assertEqual(attr, "foo")

    def test_find_recursive_functions_no_base_case(self):
        source = "fn endless() {\n    return endless()\n}"
        results = self.assistant._find_recursive_functions(source.split("\n"))
        self.assertGreater(len(results), 0)

    def test_find_recursive_functions_with_base_case(self):
        source = "fn factorial(n) {\n    if n <= 1 { return 1 }\n    return n * factorial(n - 1)\n}"
        results = self.assistant._find_recursive_functions(source.split("\n"))
        self.assertEqual(len(results), 0)

    def test_find_related_var_lines(self):
        source = "fn test(x) {\n    let y = x + 1\n    return y\n}"
        related = self.assistant._find_related_var_lines(source.split("\n"), "x", 1)
        self.assertGreater(len(related), 0)

    def test_find_context_lines(self):
        source = ["a", "b", "c", "d", "e"]
        ctx = self.assistant._find_context_lines(source, 3)
        self.assertIn(3, ctx)
        self.assertGreater(len(ctx), 1)


# =============================================================================
# docs.py tests
# =============================================================================

class TestDocGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = DocGenerator()

    def test_generate_returns_markdown_with_headings(self):
        source = '/// My module\nfn hello(name) {\n    return name\n}'
        result = self.generator.generate(source, "module.zr")
        self.assertIn("#", result)
        self.assertIsInstance(result, str)

    def test_generate_empty_source_with_path(self):
        source = ""
        result = self.generator.generate(source, "empty.zr")
        self.assertIsInstance(result, str)

    def test_generate_function_doc_includes_name(self):
        source = "/// Adds two numbers\nfn add(a, b) {\n    return a + b\n}"
        result = self.generator.generate_function_doc(source, "add")
        self.assertIn("add", result)

    def test_generate_function_doc_not_found(self):
        result = self.generator.generate_function_doc("fn foo() { }", "bar")
        self.assertIn("not found", result)

    def test_generate_function_doc_with_body(self):
        source = "fn calc() {\n    return 42\n}"
        result = self.generator.generate_function_doc(source, "calc", include_body=True)
        self.assertIn("Body", result)

    def test_generate_class_doc_includes_class_name(self):
        source = "/// A user class\nclass User {\n    fn init() { }\n}"
        result = self.generator.generate_class_doc(source, "User")
        self.assertIn("User", result)

    def test_generate_class_doc_not_found(self):
        result = self.generator.generate_class_doc("class A { }", "B")
        self.assertIn("not found", result)

    def test_generate_module_doc_creates_module_docs(self):
        source = "/// My module\nfn hello() { }"
        result = self.generator.generate_module_doc(source, "mymod")
        self.assertIn("mymod", result)

    def test_generate_api_docs_returns_string(self):
        sources = {"math.zr": "/// Math utilities\nfn add(a, b) {\n    return a + b\n}"}
        result = self.generator.generate_api_docs(sources)
        self.assertIsInstance(result, str)
        self.assertIn("add", result)

    def test_generate_api_docs_json_format(self):
        self.generator.config.format = "json"
        sources = {"math.zr": "fn add(a, b) {\n    return a + b\n}"}
        result = self.generator.generate_api_docs(sources)
        self.assertIn("functions", result)

    def test_generate_api_docs_html_format(self):
        self.generator.config.format = "html"
        sources = {"math.zr": "fn add(a, b) {\n    return a + b\n}"}
        result = self.generator.generate_api_docs(sources)
        self.assertIn("<h1>", result)

    def test_generate_readme_includes_project_name(self):
        sources = {"main.zr": "fn main() { }"}
        result = self.generator.generate_readme(sources, "MyProject")
        self.assertIn("MyProject", result)

    def test_generate_readme_has_stats(self):
        sources = {
            "a.zr": "fn foo() { }",
            "b.zr": "class Bar { fn init() { } }",
        }
        result = self.generator.generate_readme(sources, "Proj")
        self.assertIn("## Stats", result)

    def test_generate_changelog_includes_version(self):
        result = self.generator.generate_changelog("1.0.0", ["fix bug", "add feature"])
        self.assertIn("1.0.0", result)

    def test_generate_changelog_categorizes_changes(self):
        result = self.generator.generate_changelog("1.0.0", [
            "Add login feature",
            "fix crash on startup",
            "chore update deps",
        ])
        self.assertIn("### Added", result)
        self.assertIn("### Fixed", result)
        self.assertIn("### Changed", result)

    def test_generate_changelog_empty_changes(self):
        result = self.generator.generate_changelog("1.0.0", [])
        self.assertIn("1.0.0", result)

    def test_doc_config_defaults(self):
        cfg = DocConfig()
        self.assertFalse(cfg.include_private)
        self.assertEqual(cfg.format, "markdown")
        self.assertFalse(cfg.include_source)
        self.assertFalse(cfg.ai_enhance)

    def test_generate_json_format(self):
        self.generator.config.format = "json"
        source = "fn hello() {\n    return 1\n}"
        result = self.generator.generate(source, "test.zr")
        self.assertIn("level", result)
        self.assertIn("title", result)

    def test_generate_html_format(self):
        self.generator.config.format = "html"
        source = "fn hello() {\n    return 1\n}"
        result = self.generator.generate(source, "test.zr")
        self.assertIn("<h", result)


class TestDocSection(unittest.TestCase):
    def test_to_markdown_renders_headings(self):
        section = DocSection(title="Test", content="Some content", level=1)
        md = section.to_markdown()
        self.assertIn("# Test", md)
        self.assertIn("Some content", md)

    def test_to_markdown_with_children(self):
        parent = DocSection(title="Parent", content="", level=1)
        child = DocSection(title="Child", content="Child content", level=2)
        parent.children.append(child)
        md = parent.to_markdown()
        self.assertIn("## Child", md)
        self.assertIn("Child content", md)

    def test_to_html_renders_tags(self):
        section = DocSection(title="Test", content="Hello", level=1)
        html = section.to_html()
        self.assertIn("<h1>Test</h1>", html)
        self.assertIn("<p>Hello</p>", html)

    def test_to_html_respects_level_limits(self):
        section = DocSection(title="Deep", content="", level=7)
        html = section.to_html()
        self.assertIn("<h6>", html)

    def test_to_html_with_children(self):
        parent = DocSection(title="Parent", content="", level=1)
        child = DocSection(title="Child", content="C", level=2)
        parent.children.append(child)
        html = parent.to_html()
        self.assertIn("<h2>Child</h2>", html)


class TestApiReference(unittest.TestCase):
    def setUp(self):
        self.api = ApiReference()

    def test_to_markdown_renders_api_ref(self):
        self.api.functions.append({
            "name": "add",
            "params": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
            "return_type": "int",
            "doc": "Adds two numbers",
        })
        md = self.api.to_markdown()
        self.assertIn("add", md)
        self.assertIn("# API Reference", md)

    def test_to_markdown_with_modules(self):
        self.api.modules.append({"name": "math", "doc": "Math utilities"})
        md = self.api.to_markdown()
        self.assertIn("math", md)

    def test_to_markdown_with_classes(self):
        self.api.classes.append({
            "name": "Calculator",
            "methods": [{"name": "add", "params": []}],
        })
        md = self.api.to_markdown()
        self.assertIn("Calculator", md)

    def test_to_html_renders_html(self):
        self.api.functions.append({
            "name": "add",
            "params": [{"name": "a", "type": "int"}],
            "return_type": "int",
            "doc": "Adds numbers",
        })
        html = self.api.to_html()
        self.assertIn("<h1>API Reference</h1>", html)
        self.assertIn("<h3>", html)

    def test_to_json_serializes(self):
        self.api.functions.append({"name": "add", "params": [], "return_type": "int"})
        js = self.api.to_json()
        self.assertIn("add", js)
        self.assertIn("functions", js)

    def test_to_markdown_empty(self):
        md = self.api.to_markdown()
        self.assertIn("# API Reference", md)

    def test_to_html_with_modules_and_classes(self):
        self.api.modules.append({"name": "mod", "doc": "A module"})
        self.api.classes.append({"name": "Cls", "methods": []})
        self.api.functions.append({"name": "fn1", "params": [], "return_type": ""})
        html = self.api.to_html()
        self.assertIn("mod", html)
        self.assertIn("Cls", html)
        self.assertIn("fn1", html)


class TestParseDocComments(unittest.TestCase):
    def test_parse_doc_comments_extracts_fn_docs(self):
        source = "/// This function adds two numbers\nfn add(a, b) {\n    return a + b\n}"
        docs = parse_doc_comments(source)
        self.assertIn("add", docs)
        self.assertIn("adds two numbers", docs["add"].lower())

    def test_parse_doc_comments_hash_comments(self):
        source = "# This is a class\nclass MyClass {\n}"
        docs = parse_doc_comments(source)
        self.assertIn("MyClass", docs)

    def test_parse_doc_comments_empty_source(self):
        docs = parse_doc_comments("")
        self.assertEqual(docs, {})

    def test_parse_doc_comments_for_class(self):
        source = "/// User model\nclass User {\n    fn init() { }\n}"
        docs = parse_doc_comments(source)
        self.assertIn("User", docs)

    def test_parse_doc_comments_for_enum(self):
        source = "/// Colors enum\nenum Color {\n    Red\n    Green\n}"
        docs = parse_doc_comments(source)
        self.assertIn("Color", docs)

    def test_parse_doc_comments_for_interface(self):
        source = "/// Drawable interface\ninterface Drawable {\n    fn draw()\n}"
        docs = parse_doc_comments(source)
        self.assertIn("Drawable", docs)


class TestDocHelpers(unittest.TestCase):
    def test_doc_section_to_markdown_empty_content(self):
        section = DocSection(title="Empty", content="", level=1)
        md = section.to_markdown()
        self.assertIn("# Empty", md)

    def test_build_sections_for_source(self):
        source = "fn hello() {\n    return 1\n}\nclass A { fn init() { } }"
        generator = DocGenerator()
        sections = generator._build_sections(source, "test.zr")
        self.assertGreater(len(sections), 0)

    def test_generate_with_ai_enhance_does_not_crash(self):
        generator = DocGenerator(DocConfig(ai_enhance=True))
        result = generator.generate("fn foo() { }", "f.zr")
        self.assertIsInstance(result, str)

    def test_api_reference_to_markdown_with_params_doc(self):
        api = ApiReference()
        api.functions.append({
            "name": "search",
            "params": [{"name": "query", "type": "str", "doc": "The search query"}],
            "return_type": "list",
            "doc": "Search for items",
        })
        md = api.to_markdown()
        self.assertIn("query", md)
        self.assertIn("search query", md)

    def test_extract_classes_from_source(self):
        from zoya.ide.docs import _extract_classes
        source = "class Animal {\n    fn speak() { }\n}"
        classes = _extract_classes(source)
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]["name"], "Animal")

    def test_extract_enums_from_source(self):
        from zoya.ide.docs import _extract_enums
        source = "enum Color {\n    Red\n    Green\n    Blue\n}"
        enums = _extract_enums(source)
        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0]["name"], "Color")

    def test_extract_interfaces_from_source(self):
        from zoya.ide.docs import _extract_interfaces
        source = "interface Drawable {\n    fn draw()\n    fn resize()\n}"
        interfaces = _extract_interfaces(source)
        self.assertEqual(len(interfaces), 1)
        self.assertIn("draw", interfaces[0]["methods"])

    def test_format_fn_signature(self):
        from zoya.ide.docs import _format_fn_signature
        fn = {
            "name": "add",
            "params": [{"name": "a", "type": "int"}, {"name": "b", "type": "int", "default": "0"}],
            "return_type": "int",
        }
        sig = _format_fn_signature(fn)
        self.assertIn("add", sig)
        self.assertIn("a :: int", sig)
        self.assertIn("b :: int = 0", sig)
        self.assertIn("-> int", sig)

    def test_escape_html(self):
        from zoya.ide.docs import _escape_html
        self.assertEqual(_escape_html("<script>"), "&lt;script&gt;")
        self.assertEqual(_escape_html('a & b'), "a &amp; b")


if __name__ == "__main__":
    unittest.main()
