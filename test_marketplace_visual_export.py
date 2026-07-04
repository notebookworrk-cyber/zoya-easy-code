import json
import os
import sys
import unittest

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from zoya.export import (
    ExportConfig,
    Exporter,
    ExportError,
    ExportResult,
    ExportTarget,
    generate_dockerfile,
    generate_html_wrapper,
    generate_requirements,
    generate_setup_py,
)
from zoya.marketplace import (
    DependencyResolver,
    MarketplaceRegistry,
    PackageError,
    PackageInfo,
    PackageVersion,
)
from zoya.visual import (
    ComponentDefinition,
    ComponentLibrary,
    LayoutEngine,
    Theme,
    VisualBuilder,
    VisualBuilderError,
)


class TestMarketplacePackageInfo(unittest.TestCase):
    def test_create_with_all_fields(self):
        info = PackageInfo(
            name="test-pkg",
            version="1.0.0",
            description="A test package",
            author="tester",
            license="MIT",
            dependencies=["dep1", "dep2"],
            tags=["ui", "button"],
            downloads=100,
            rating=4.5,
            homepage="https://example.com",
            repository="https://github.com/test/test-pkg",
            readme="# Test",
        )
        self.assertEqual(info.name, "test-pkg")
        self.assertEqual(info.version, "1.0.0")
        self.assertEqual(info.description, "A test package")
        self.assertEqual(info.author, "tester")
        self.assertEqual(info.license, "MIT")
        self.assertEqual(info.dependencies, ["dep1", "dep2"])
        self.assertEqual(info.tags, ["ui", "button"])
        self.assertEqual(info.downloads, 100)
        self.assertEqual(info.rating, 4.5)
        self.assertEqual(info.homepage, "https://example.com")
        self.assertEqual(info.repository, "https://github.com/test/test-pkg")
        self.assertEqual(info.readme, "# Test")

    def test_create_with_defaults(self):
        info = PackageInfo(
            name="minimal", version="0.0.1", description="desc", author="a"
        )
        self.assertEqual(info.license, "MIT")
        self.assertEqual(info.dependencies, [])
        self.assertEqual(info.tags, [])
        self.assertEqual(info.downloads, 0)
        self.assertEqual(info.rating, 0.0)
        self.assertIsNotNone(info.created_at)
        self.assertIsNotNone(info.updated_at)
        self.assertIsNone(info.homepage)
        self.assertIsNone(info.repository)
        self.assertIsNone(info.readme)

    def test_created_at_preserved(self):
        fixed = 1000000.0
        info = PackageInfo(
            name="p", version="1.0", description="d", author="a", created_at=fixed
        )
        self.assertEqual(info.created_at, fixed)


class TestMarketplacePackageVersion(unittest.TestCase):
    def test_create_with_all_fields(self):
        v = PackageVersion(
            package="test-pkg",
            version="1.0.0",
            files={"main.py": "print('hello')"},
            manifest={"entry": "main.py"},
        )
        self.assertEqual(v.package, "test-pkg")
        self.assertEqual(v.version, "1.0.0")
        self.assertEqual(v.files, {"main.py": "print('hello')"})
        self.assertEqual(v.manifest, {"entry": "main.py"})
        self.assertIsNotNone(v.published_at)

    def test_create_with_defaults(self):
        v = PackageVersion(package="p", version="0.1")
        self.assertEqual(v.files, {})
        self.assertEqual(v.manifest, {})


class TestMarketplaceRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = MarketplaceRegistry()

    def _make_pkg(self, name="pkg", version="1.0.0", tags=None, downloads=0):
        return PackageInfo(
            name=name,
            version=version,
            description=f"desc-{name}",
            author="author",
            tags=tags or [],
            downloads=downloads,
        )

    def test_register_stores_package(self):
        pkg = self._make_pkg("mypkg")
        result = self.reg.register(pkg)
        self.assertEqual(result, "mypkg")
        self.assertEqual(self.reg.count(), 1)

    def test_get_package_returns_package(self):
        pkg = self._make_pkg("findme")
        self.reg.register(pkg)
        retrieved = self.reg.get_package("findme")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "findme")

    def test_get_package_returns_none_for_missing(self):
        self.assertIsNone(self.reg.get_package("nonexistent"))

    def test_publish_version_stores_version(self):
        pkg = self._make_pkg("ver-pkg")
        self.reg.register(pkg)
        ver = PackageVersion(
            package="ver-pkg", version="2.0.0", files={"app.py": "code"}
        )
        self.reg.publish_version("ver-pkg", ver)
        retrieved = self.reg.get_version("ver-pkg", "2.0.0")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.files, {"app.py": "code"})

    def test_publish_version_updates_package_version(self):
        pkg = self._make_pkg("up-pkg", "1.0.0")
        self.reg.register(pkg)
        self.reg.publish_version(
            "up-pkg", PackageVersion(package="up-pkg", version="2.0.0")
        )
        self.assertEqual(self.reg.get_package("up-pkg").version, "2.0.0")

    def test_get_version_returns_none_for_unregistered(self):
        self.assertIsNone(self.reg.get_version("unknown", "1.0.0"))

    def test_search_by_name(self):
        a = self._make_pkg("alpha-ui", tags=["ui"])
        b = self._make_pkg("beta-core", tags=["core"])
        self.reg.register(a)
        self.reg.register(b)
        results = self.reg.search("alpha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "alpha-ui")

    def test_search_by_description(self):
        a = self._make_pkg("tool-a")
        b = self._make_pkg("tool-b")
        self.reg.register(a)
        self.reg.register(b)
        results = self.reg.search("desc-tool")
        self.assertEqual(len(results), 2)

    def test_search_with_tags_filter(self):
        a = self._make_pkg("a", tags=["ui", "grid"])
        b = self._make_pkg("b", tags=["core"])
        self.reg.register(a)
        self.reg.register(b)
        results = self.reg.search("a", tags=["ui"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "a")

    def test_search_with_tags_no_match(self):
        a = self._make_pkg("a", tags=["ui"])
        self.reg.register(a)
        results = self.reg.search("a", tags=["database"])
        self.assertEqual(len(results), 0)

    def test_list_by_tag(self):
        a = self._make_pkg("a", tags=["web"])
        b = self._make_pkg("b", tags=["web"])
        c = self._make_pkg("c", tags=["cli"])
        self.reg.register(a)
        self.reg.register(b)
        self.reg.register(c)
        results = self.reg.list_by_tag("web")
        self.assertEqual(len(results), 2)

    def test_list_popular(self):
        a = self._make_pkg("a", downloads=10)
        b = self._make_pkg("b", downloads=50)
        c = self._make_pkg("c", downloads=30)
        self.reg.register(a)
        self.reg.register(b)
        self.reg.register(c)
        popular = self.reg.list_popular(2)
        self.assertEqual(len(popular), 2)
        self.assertEqual(popular[0].name, "b")
        self.assertEqual(popular[1].name, "c")

    def test_list_popular_default_limit(self):
        for i in range(15):
            self.reg.register(self._make_pkg(f"pkg-{i}", downloads=i * 10))
        self.assertEqual(len(self.reg.list_popular()), 10)

    def test_list_recent(self):
        a = self._make_pkg("old")
        b = self._make_pkg("new")
        self.reg.register(a)
        self.reg.register(b)
        recent = self.reg.list_recent(1)
        self.assertEqual(len(recent), 1)

    def test_install_returns_files(self):
        pkg = self._make_pkg("installable")
        self.reg.register(pkg)
        ver = PackageVersion(
            package="installable", version="1.0.0", files={"main.py": "code"}
        )
        self.reg.publish_version("installable", ver)
        files = self.reg.install("installable")
        self.assertEqual(files, {"main.py": "code"})

    def test_install_increments_downloads(self):
        pkg = self._make_pkg("dl-pkg", downloads=0)
        self.reg.register(pkg)
        self.reg.publish_version(
            "dl-pkg", PackageVersion(package="dl-pkg", version="1.0.0")
        )
        before = self.reg.get_package("dl-pkg").downloads
        self.reg.install("dl-pkg")
        after = self.reg.get_package("dl-pkg").downloads
        self.assertEqual(after, before + 1)

    def test_install_selects_latest(self):
        pkg = self._make_pkg("multi-ver")
        self.reg.register(pkg)
        self.reg.publish_version(
            "multi-ver",
            PackageVersion(package="multi-ver", version="1.0.0", files={"f1": "v1"}),
        )
        self.reg.publish_version(
            "multi-ver",
            PackageVersion(package="multi-ver", version="2.0.0", files={"f2": "v2"}),
        )
        files = self.reg.install("multi-ver")
        self.assertEqual(files, {"f2": "v2"})

    def test_install_specific_version(self):
        pkg = self._make_pkg("specific")
        self.reg.register(pkg)
        self.reg.publish_version(
            "specific",
            PackageVersion(package="specific", version="1.0.0", files={"f": "v1"}),
        )
        self.reg.publish_version(
            "specific",
            PackageVersion(package="specific", version="2.0.0", files={"f": "v2"}),
        )
        files = self.reg.install("specific", version="1.0.0")
        self.assertEqual(files, {"f": "v1"})

    def test_install_missing_package_raises(self):
        with self.assertRaises(PackageError):
            self.reg.install("ghost")

    def test_install_no_versions_raises(self):
        pkg = self._make_pkg("no-ver")
        self.reg.register(pkg)
        with self.assertRaises(PackageError):
            self.reg.install("no-ver")

    def test_install_deprecated_raises(self):
        pkg = self._make_pkg("depr")
        self.reg.register(pkg)
        self.reg.publish_version(
            "depr", PackageVersion(package="depr", version="1.0.0")
        )
        self.reg.deprecate("depr", "use v2 instead")
        with self.assertRaises(PackageError) as ctx:
            self.reg.install("depr")
        self.assertIn("deprecated", str(ctx.exception))

    def test_uninstall_removes(self):
        pkg = self._make_pkg("removable")
        self.reg.register(pkg)
        self.reg.uninstall("removable")
        self.assertIsNone(self.reg.get_package("removable"))
        self.assertEqual(self.reg.count(), 0)

    def test_uninstall_missing_raises(self):
        with self.assertRaises(PackageError):
            self.reg.uninstall("ghost")

    def test_update_returns_none_when_version_already_current(self):
        pkg = self._make_pkg("updatable", "1.0.0")
        self.reg.register(pkg)
        self.reg.publish_version(
            "updatable", PackageVersion(package="updatable", version="2.0.0")
        )
        new_ver = self.reg.update("updatable")
        self.assertIsNone(new_ver)

    def test_update_returns_none_when_up_to_date(self):
        pkg = self._make_pkg("current", "2.0.0")
        self.reg.register(pkg)
        self.reg.publish_version(
            "current", PackageVersion(package="current", version="2.0.0")
        )
        result = self.reg.update("current")
        self.assertIsNone(result)

    def test_update_missing_raises(self):
        with self.assertRaises(PackageError):
            self.reg.update("ghost")

    def test_deprecate_marks(self):
        pkg = self._make_pkg("old")
        self.reg.register(pkg)
        self.reg.deprecate("old", "no longer maintained")
        with self.assertRaises(PackageError) as ctx:
            self.reg.install("old")
        self.assertIn("no longer maintained", str(ctx.exception))

    def test_deprecate_missing_raises(self):
        with self.assertRaises(PackageError):
            self.reg.deprecate("ghost")

    def test_duplicate_registration_raises(self):
        pkg = self._make_pkg("dup")
        self.reg.register(pkg)
        with self.assertRaises(PackageError) as ctx:
            self.reg.register(pkg)
        self.assertIn("already registered", str(ctx.exception))

    def test_get_dependency_tree(self):
        inner = PackageInfo(
            name="inner", version="1.0.0", description="i", author="a", dependencies=[]
        )
        outer = PackageInfo(
            name="outer",
            version="2.0.0",
            description="o",
            author="a",
            dependencies=["inner"],
        )
        self.reg.register(inner)
        self.reg.register(outer)
        tree = self.reg.get_dependency_tree("outer")
        self.assertEqual(tree["name"], "outer")
        self.assertEqual(len(tree["dependencies"]), 1)
        self.assertEqual(tree["dependencies"][0]["name"], "inner")

    def test_get_dependency_tree_missing_returns_empty(self):
        self.assertEqual(self.reg.get_dependency_tree("nope"), {})

    def test_check_updates_returns_empty_when_current(self):
        a = self._make_pkg("a", "1.0.0")
        self.reg.register(a)
        self.reg.publish_version("a", PackageVersion(package="a", version="1.0.0"))
        updates = self.reg.check_updates()
        self.assertEqual(len(updates), 0)

    def test_count(self):
        self.assertEqual(self.reg.count(), 0)
        self.reg.register(self._make_pkg("x"))
        self.assertEqual(self.reg.count(), 1)

    def test_clear(self):
        self.reg.register(self._make_pkg("a"))
        self.reg.register(self._make_pkg("b"))
        self.reg.clear()
        self.assertEqual(self.reg.count(), 0)
        self.assertIsNone(self.reg.get_package("a"))


class TestMarketplaceDependencyResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = DependencyResolver()

    def test_resolve_returns_tuple(self):
        result = self.resolver.resolve("mypkg", "1.0")
        self.assertEqual(result, [("mypkg", "1.0")])

    def test_compare_versions_equal(self):
        self.assertEqual(self.resolver.compare_versions("1.0.0", "1.0.0"), 0)

    def test_compare_versions_less(self):
        self.assertEqual(self.resolver.compare_versions("1.0.0", "2.0.0"), -1)

    def test_compare_versions_greater(self):
        self.assertEqual(self.resolver.compare_versions("2.0.0", "1.0.0"), 1)

    def test_compare_versions_different_lengths(self):
        self.assertEqual(self.resolver.compare_versions("1.0", "1.0.0"), 0)
        self.assertEqual(self.resolver.compare_versions("2.0", "1.9.9"), 1)

    def test_satisfies_wildcard(self):
        self.assertTrue(self.resolver.satisfies("1.0.0", "*"))

    def test_satisfies_caret(self):
        self.assertTrue(self.resolver.satisfies("2.5.0", "^2.0.0"))
        self.assertFalse(self.resolver.satisfies("3.0.0", "^2.0.0"))

    def test_satisfies_gte(self):
        self.assertTrue(self.resolver.satisfies("2.0.0", ">=1.0.0"))
        self.assertFalse(self.resolver.satisfies("1.0.0", ">=2.0.0"))

    def test_satisfies_lte(self):
        self.assertTrue(self.resolver.satisfies("1.0.0", "<=2.0.0"))
        self.assertFalse(self.resolver.satisfies("3.0.0", "<=2.0.0"))

    def test_satisfies_gt(self):
        self.assertTrue(self.resolver.satisfies("2.0.0", ">1.0.0"))
        self.assertFalse(self.resolver.satisfies("1.0.0", ">1.0.0"))

    def test_satisfies_lt(self):
        self.assertTrue(self.resolver.satisfies("1.0.0", "<2.0.0"))
        self.assertFalse(self.resolver.satisfies("2.0.0", "<2.0.0"))

    def test_satisfies_exact_equals(self):
        self.assertTrue(self.resolver.satisfies("1.0.0", "=1.0.0"))
        self.assertFalse(self.resolver.satisfies("1.0.1", "=1.0.0"))

    def test_satisfies_twiddle_wakka_two_parts(self):
        self.assertTrue(self.resolver.satisfies("1.2.3", "~>1.2"))
        self.assertFalse(self.resolver.satisfies("1.3.0", "~>1.2"))

    def test_satisfies_twiddle_wakka_one_part(self):
        self.assertTrue(self.resolver.satisfies("2.5.0", "~>2"))
        self.assertFalse(self.resolver.satisfies("3.0.0", "~>2"))

    def test_satisfies_exact_match_default(self):
        self.assertTrue(self.resolver.satisfies("1.0.0", "1.0.0"))
        self.assertFalse(self.resolver.satisfies("1.0.1", "1.0.0"))

    def test_validate_version_valid(self):
        self.assertTrue(self.resolver.validate_version("1.2.3"))
        self.assertTrue(self.resolver.validate_version("0.0.1"))
        self.assertTrue(self.resolver.validate_version("999.999.999"))

    def test_validate_version_invalid(self):
        self.assertFalse(self.resolver.validate_version("1.2"))
        self.assertFalse(self.resolver.validate_version("1.2.3.4"))
        self.assertFalse(self.resolver.validate_version("abc"))
        self.assertFalse(self.resolver.validate_version(""))

    def test_check_conflicts_no_conflicts(self):
        deps = [("a", "1.0"), ("b", "2.0")]
        self.assertEqual(self.resolver.check_conflicts(deps), [])

    def test_check_conflicts_detects(self):
        deps = [("a", "1.0"), ("a", "2.0")]
        conflicts = self.resolver.check_conflicts(deps)
        self.assertEqual(len(conflicts), 1)


class TestVisualComponentDefinition(unittest.TestCase):
    def test_create_with_all_fields(self):
        child = ComponentDefinition(type="label", props={"text": "hello"})
        comp = ComponentDefinition(
            type="button",
            props={"text": "Click"},
            children=[child],
            events={"on_click": "handle"},
            style={"color": "red"},
            comp_id="btn-1",
        )
        self.assertEqual(comp.type, "button")
        self.assertEqual(comp.props, {"text": "Click"})
        self.assertEqual(len(comp.children), 1)
        self.assertEqual(comp.children[0].type, "label")
        self.assertEqual(comp.events, {"on_click": "handle"})
        self.assertEqual(comp.style, {"color": "red"})
        self.assertEqual(comp.id, "btn-1")

    def test_auto_generates_id(self):
        comp = ComponentDefinition(type="button")
        self.assertTrue(comp.id.startswith("button_"))

    def test_defaults(self):
        comp = ComponentDefinition(type="label")
        self.assertEqual(comp.props, {})
        self.assertEqual(comp.children, [])
        self.assertEqual(comp.events, {})
        self.assertEqual(comp.style, {})


class TestVisualComponentLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = ComponentLibrary()

    def test_list_types_includes_builtins(self):
        types = self.lib.list_types()
        self.assertIn("button", types)
        self.assertIn("label", types)
        self.assertIn("textfield", types)
        self.assertIn("image", types)
        self.assertIn("list", types)
        self.assertIn("card", types)
        self.assertIn("column", types)
        self.assertIn("row", types)
        self.assertIn("switch", types)
        self.assertIn("slider", types)
        self.assertIn("progress", types)
        self.assertIn("spacer", types)
        self.assertIn("divider", types)

    def test_get_schema_returns_schema(self):
        schema = self.lib.get_schema("button")
        self.assertIsNotNone(schema)
        self.assertIn("props", schema)
        self.assertIn("events", schema)
        self.assertIn("text", schema["props"])
        self.assertIn("enabled", schema["props"])

    def test_get_schema_returns_none_for_unknown(self):
        self.assertIsNone(self.lib.get_schema("nonexistent"))

    def test_register_custom_type(self):
        schema = {"props": {"value": {"type": "string"}}, "events": ["on_change"]}
        self.lib.register("custom-slider", schema)
        self.assertIn("custom-slider", self.lib.list_types())
        retrieved = self.lib.get_schema("custom-slider")
        self.assertEqual(retrieved, schema)

    def test_register_overwrites_existing(self):
        schema = {"props": {}, "events": []}
        self.lib.register("button", schema)
        self.assertEqual(self.lib.get_schema("button"), schema)


class TestVisualBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = VisualBuilder()

    def test_build_from_dict_spec(self):
        spec = {"type": "button", "props": {"text": "OK"}}
        components = self.builder.build(spec)
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].type, "button")
        self.assertEqual(components[0].props, {"text": "OK"})

    def test_build_from_list_spec(self):
        spec = [
            {"type": "button", "props": {"text": "A"}},
            {"type": "label", "props": {"text": "B"}},
        ]
        components = self.builder.build(spec)
        self.assertEqual(len(components), 2)

    def test_build_from_spec_with_components_key(self):
        spec = {"components": [{"type": "button"}, {"type": "label"}]}
        components = self.builder.build(spec)
        self.assertEqual(len(components), 2)

    def test_build_from_json_string(self):
        spec = '{"type": "button", "props": {"text": "JSON"}}'
        components = self.builder.build(spec)
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].props["text"], "JSON")

    def test_build_raises_on_invalid_spec(self):
        with self.assertRaises(VisualBuilderError):
            self.builder.build(42)

    def test_build_raises_on_missing_type(self):
        with self.assertRaises(VisualBuilderError):
            self.builder.build({"props": {"text": "oops"}})

    def test_build_with_children(self):
        spec = {
            "type": "column",
            "children": [
                {"type": "button", "props": {"text": "A"}},
                {"type": "button", "props": {"text": "B"}},
            ],
        }
        components = self.builder.build(spec)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(components[0].children), 2)

    def test_to_json_serializes(self):
        comps = [ComponentDefinition(type="button", props={"text": "Hi"})]
        output = self.builder.to_json(comps)
        data = json.loads(output)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["type"], "button")

    def test_to_zoya_code_generates_source(self):
        comps = [ComponentDefinition(type="button", props={"text": "Hi"})]
        code = self.builder.to_zoya_code(comps)
        self.assertIn("button(", code)
        self.assertIn("text='Hi'", code)

    def test_to_zoya_code_with_children(self):
        comps = [
            ComponentDefinition(
                type="column",
                children=[ComponentDefinition(type="button", props={"text": "A"})],
            )
        ]
        code = self.builder.to_zoya_code(comps)
        self.assertIn("column(", code)
        self.assertIn("{", code)
        self.assertIn("button(", code)
        self.assertIn("}", code)

    def test_to_zoya_code_with_style_and_events(self):
        comps = [
            ComponentDefinition(
                type="button",
                props={"text": "Go"},
                style={"color": "blue"},
                events={"on_click": "go()"},
            )
        ]
        code = self.builder.to_zoya_code(comps)
        self.assertIn('"color": "blue"', code)
        self.assertIn('"on_click"', code)

    def test_render_preview(self):
        comps = [
            ComponentDefinition(
                type="button",
                props={"text": "Click"},
                children=[ComponentDefinition(type="label", props={"text": "Nested"})],
            )
        ]
        preview = self.builder.render_preview(comps)
        self.assertIn("[button]", preview)
        self.assertIn("Click", preview)
        self.assertIn("[label]", preview)
        self.assertIn("Nested", preview)

    def test_validate_spec_valid(self):
        spec = {"components": [{"type": "button", "props": {"text": "OK"}}]}
        errors = self.builder.validate_spec(spec)
        self.assertEqual(errors, [])

    def test_validate_spec_unknown_type(self):
        spec = {"components": [{"type": "alien", "props": {}}]}
        errors = self.builder.validate_spec(spec)
        self.assertTrue(any("unknown type" in e for e in errors))

    def test_validate_spec_unknown_prop(self):
        spec = {"components": [{"type": "button", "props": {"nonexistent_prop": "x"}}]}
        errors = self.builder.validate_spec(spec)
        self.assertTrue(any("unknown prop" in e for e in errors))

    def test_validate_spec_unknown_event(self):
        spec = {"components": [{"type": "button", "events": {"on_alien": "fn"}}]}
        errors = self.builder.validate_spec(spec)
        self.assertTrue(any("unknown event" in e for e in errors))

    def test_validate_spec_not_dict(self):
        errors = self.builder.validate_spec("not a dict")
        self.assertEqual(errors, ["Spec must be a dictionary"])

    def test_validate_spec_single_component(self):
        spec = {"type": "label", "props": {"text": "hello"}}
        errors = self.builder.validate_spec(spec)
        self.assertEqual(errors, [])

    def test_validate_spec_missing_type(self):
        spec = {"components": [{"props": {"text": "oops"}}]}
        errors = self.builder.validate_spec(spec)
        self.assertTrue(any("missing 'type'" in e for e in errors))

    def test_merge_styles_shallow(self):
        merged = self.builder.merge_styles({"color": "red"}, {"color": "blue"})
        self.assertEqual(merged, {"color": "blue"})

    def test_merge_styles_nested(self):
        merged = self.builder.merge_styles(
            {"font": {"size": 12, "weight": "normal"}},
            {"font": {"weight": "bold"}},
        )
        self.assertEqual(merged, {"font": {"size": 12, "weight": "bold"}})

    def test_merge_styles_adds_new(self):
        merged = self.builder.merge_styles({"color": "red"}, {"bg": "blue"})
        self.assertEqual(merged, {"color": "red", "bg": "blue"})


class TestVisualLayoutEngine(unittest.TestCase):
    def setUp(self):
        self.engine = LayoutEngine()

    def test_calculate_returns_positions(self):
        comps = [ComponentDefinition(type="button", style={"width": 80, "height": 30})]
        positions = self.engine.calculate(comps, container_width=400)
        self.assertEqual(len(positions), 1)
        self.assertIn("x", positions[0])
        self.assertIn("y", positions[0])
        self.assertIn("width", positions[0])
        self.assertIn("height", positions[0])

    def test_calculate_row_layout(self):
        comps = [
            ComponentDefinition(type="button", style={"width": 50, "height": 30}),
            ComponentDefinition(type="button", style={"width": 50, "height": 30}),
        ]
        positions = self.engine.calculate(comps, container_width=200)
        self.assertEqual(positions[0]["x"], 0)
        self.assertEqual(positions[1]["x"], 50)

    def test_calculate_row_wraps(self):
        comps = [
            ComponentDefinition(type="button", style={"width": 120, "height": 30}),
            ComponentDefinition(type="button", style={"width": 120, "height": 30}),
        ]
        positions = self.engine.calculate(comps, container_width=200)
        self.assertEqual(positions[0]["x"], 0)
        self.assertEqual(positions[0]["y"], 0)
        self.assertEqual(positions[1]["x"], 0)
        self.assertEqual(positions[1]["y"], 30)

    def test_calculate_column_layout(self):
        comps = [
            ComponentDefinition(
                type="label", style={"layout": "flex-column", "width": 50, "height": 20}
            ),
            ComponentDefinition(
                type="label", style={"layout": "flex-column", "width": 50, "height": 30}
            ),
        ]
        positions = self.engine.calculate(comps, container_width=400)
        self.assertEqual(positions[0]["x"], 0)
        self.assertEqual(positions[0]["y"], 0)
        self.assertEqual(positions[1]["x"], 0)
        self.assertEqual(positions[1]["y"], 20)

    def test_calculate_absolute_layout(self):
        comps = [
            ComponentDefinition(
                type="button",
                style={
                    "layout": "absolute",
                    "left": 10,
                    "top": 20,
                    "width": 100,
                    "height": 50,
                },
            )
        ]
        positions = self.engine.calculate(comps, container_width=400)
        self.assertEqual(positions[0]["x"], 10)
        self.assertEqual(positions[0]["y"], 20)

    def test_calculate_absolute_defaults(self):
        comps = [ComponentDefinition(type="button", style={"layout": "absolute"})]
        positions = self.engine.calculate(comps, container_width=400)
        self.assertEqual(positions[0]["x"], 0)
        self.assertEqual(positions[0]["y"], 0)

    def test_calculate_with_margin(self):
        comps = [
            ComponentDefinition(
                type="button", style={"width": 50, "height": 30, "margin": 10}
            ),
            ComponentDefinition(type="button", style={"width": 50, "height": 30}),
        ]
        positions = self.engine.calculate(comps, container_width=400)
        self.assertEqual(positions[0]["x"], 0)
        self.assertEqual(positions[1]["x"], 60)


class TestVisualTheme(unittest.TestCase):
    def test_create_with_defaults(self):
        theme = Theme()
        self.assertIn("primary", theme.colors)
        self.assertIn("md", theme.spacing)
        self.assertEqual(theme.border_radius, 4)

    def test_create_with_custom_values(self):
        theme = Theme(
            colors={"primary": "#ff0000", "background": "#000"},
            spacing={"sm": 2, "lg": 20},
            border_radius=8,
        )
        self.assertEqual(theme.colors["primary"], "#ff0000")
        self.assertEqual(theme.spacing["sm"], 2)
        self.assertEqual(theme.border_radius, 8)

    def test_to_css_includes_color_vars(self):
        theme = Theme(colors={"primary": "#ff6600"})
        css = theme.to_css()
        self.assertIn("--color-primary: #ff6600;", css)

    def test_to_css_includes_spacing_vars(self):
        theme = Theme(spacing={"md": 16})
        css = theme.to_css()
        self.assertIn("--spacing-md: 16px;", css)

    def test_to_css_includes_font_vars(self):
        theme = Theme(fonts={"family": "Helvetica", "size_md": 14})
        css = theme.to_css()
        self.assertIn("--font-family: Helvetica;", css)
        self.assertIn("--font-size-md: 14;", css)

    def test_to_css_includes_border_radius(self):
        theme = Theme(border_radius=12)
        css = theme.to_css()
        self.assertIn("--border-radius: 12px;", css)

    def test_to_css_wraps_in_root(self):
        theme = Theme()
        css = theme.to_css()
        self.assertTrue(css.startswith(":root {"))
        self.assertTrue(css.endswith("}"))

    def test_to_css_converts_underscores_to_hyphens(self):
        theme = Theme(colors={"text_secondary": "#888"})
        css = theme.to_css()
        self.assertIn("--color-text-secondary", css)

    def test_visual_builder_error_is_exception(self):
        self.assertTrue(issubclass(VisualBuilderError, Exception))


class TestExportTarget(unittest.TestCase):
    def test_values(self):
        self.assertEqual(ExportTarget.WEB, "web")
        self.assertEqual(ExportTarget.DESKTOP, "desktop")
        self.assertEqual(ExportTarget.MOBILE, "mobile")
        self.assertEqual(ExportTarget.CLI, "cli")
        self.assertEqual(ExportTarget.LIBRARY, "library")
        self.assertEqual(ExportTarget.DOCKER, "docker")


class TestExportConfig(unittest.TestCase):
    def test_create_with_all_fields(self):
        config = ExportConfig(
            target=ExportTarget.WEB,
            output_dir="/out",
            minify=True,
            include_tests=True,
            include_docs=True,
            entry_point="app.zy",
            format="binary",
        )
        self.assertEqual(config.target, ExportTarget.WEB)
        self.assertEqual(config.output_dir, "/out")
        self.assertTrue(config.minify)
        self.assertTrue(config.include_tests)
        self.assertTrue(config.include_docs)
        self.assertEqual(config.entry_point, "app.zy")
        self.assertEqual(config.format, "binary")

    def test_defaults(self):
        config = ExportConfig(target=ExportTarget.CLI, output_dir=".")
        self.assertFalse(config.minify)
        self.assertFalse(config.include_tests)
        self.assertFalse(config.include_docs)
        self.assertEqual(config.entry_point, "main.zy")
        self.assertEqual(config.format, "source")


class TestExportResult(unittest.TestCase):
    def test_create_with_all_fields(self):
        result = ExportResult(
            success=True,
            files={"a.py": "code"},
            output_dir="/out",
            errors=["err1"],
            warnings=["warn1"],
            target=ExportTarget.WEB,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.files, {"a.py": "code"})
        self.assertEqual(result.output_dir, "/out")
        self.assertEqual(result.errors, ["err1"])
        self.assertEqual(result.warnings, ["warn1"])
        self.assertEqual(result.target, ExportTarget.WEB)

    def test_defaults(self):
        result = ExportResult(success=False)
        self.assertEqual(result.files, {})
        self.assertEqual(result.output_dir, "")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.target, ExportTarget.WEB)


class TestExportHelpers(unittest.TestCase):
    def test_generate_requirements_basic(self):
        reqs = generate_requirements("print('hello')")
        self.assertIn("zoya", reqs)

    def test_generate_requirements_flask(self):
        reqs = generate_requirements("import flask")
        self.assertIn("flask", reqs)

    def test_generate_requirements_django(self):
        reqs = generate_requirements("from django.urls import path")
        self.assertIn("django", reqs)

    def test_generate_requirements_requests(self):
        reqs = generate_requirements("import requests")
        self.assertIn("requests", reqs)

    def test_generate_dockerfile(self):
        df = generate_dockerfile("print('hello')")
        self.assertIn("FROM python:3.12-slim", df)
        self.assertIn("WORKDIR /app", df)
        self.assertIn("requirements.txt", df)
        self.assertIn("EXPOSE 8080", df)
        self.assertIn('CMD ["python", "main.py"]', df)

    def test_generate_html_wrapper(self):
        html = generate_html_wrapper("print('hello')")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("pyodide", html)
        self.assertIn("print('hello')", html)

    def test_generate_html_wrapper_escapes_special_chars(self):
        html = generate_html_wrapper("x < 5 && y > 10")
        self.assertIn("&lt;", html)
        self.assertIn("&gt;", html)

    def test_generate_setup_py(self):
        setup = generate_setup_py("# name: my-app\n# version: 2.0.0\nprint('hi')")
        self.assertIn('name="my-app"', setup)
        self.assertIn('version="2.0.0"', setup)

    def test_generate_setup_py_defaults(self):
        setup = generate_setup_py("print('hi')")
        self.assertIn('name="zoya-app"', setup)
        self.assertIn('version="0.1.0"', setup)


class TestExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = Exporter()
        self.source = "print('hello world')"

    def test_export_web_returns_index_html(self):
        config = ExportConfig(target=ExportTarget.WEB, output_dir="/tmp/web")
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertIn("main.html", result.files)
        self.assertIn("main.zy", result.files)
        self.assertIn("requirements.txt", result.files)

    def test_export_web_html_contains_pyodide(self):
        config = ExportConfig(target=ExportTarget.WEB, output_dir="/tmp/web")
        result = self.exporter.export(self.source, config)
        html = result.files["main.html"]
        self.assertIn("pyodide", html)
        self.assertIn("print('hello world')", html)

    def test_export_web_with_tests(self):
        config = ExportConfig(
            target=ExportTarget.WEB, output_dir="/tmp/web", include_tests=True
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("tests/test_app.py", result.files)

    def test_export_desktop_returns_python_files(self):
        config = ExportConfig(
            target=ExportTarget.DESKTOP, output_dir="/tmp/desk", entry_point="app.zy"
        )
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertIn("app.py", result.files)
        self.assertIn("run.py", result.files)
        self.assertIn("requirements.txt", result.files)

    def test_export_desktop_run_py_has_create_app(self):
        config = ExportConfig(
            target=ExportTarget.DESKTOP, output_dir="/tmp/desk", entry_point="main.zy"
        )
        result = self.exporter.export(self.source, config)
        run_py = result.files["run.py"]
        self.assertIn("def main():", run_py)
        self.assertIn("create_app()", run_py)

    def test_export_desktop_with_tests(self):
        config = ExportConfig(
            target=ExportTarget.DESKTOP, output_dir="/tmp/desk", include_tests=True
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("tests/test_app.py", result.files)

    def test_export_cli_returns_executable(self):
        config = ExportConfig(target=ExportTarget.CLI, output_dir="/tmp/cli")
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertIn("main.py", result.files)
        self.assertIn("main_cli.py", result.files)
        self.assertIn("requirements.txt", result.files)

    def test_export_cli_has_shebang(self):
        config = ExportConfig(target=ExportTarget.CLI, output_dir="/tmp/cli")
        result = self.exporter.export(self.source, config)
        cli_py = result.files["main_cli.py"]
        self.assertIn("#!/usr/bin/env python3", cli_py)
        self.assertIn("cli_main", cli_py)

    def test_export_cli_with_tests(self):
        config = ExportConfig(
            target=ExportTarget.CLI, output_dir="/tmp/cli", include_tests=True
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("tests/test_cli.py", result.files)

    def test_export_docker_returns_dockerfile(self):
        config = ExportConfig(target=ExportTarget.DOCKER, output_dir="/tmp/dkr")
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertIn("Dockerfile", result.files)
        self.assertIn("docker-compose.yml", result.files)
        self.assertIn(".dockerignore", result.files)
        self.assertIn("requirements.txt", result.files)

    def test_export_docker_dockerfile_content(self):
        config = ExportConfig(target=ExportTarget.DOCKER, output_dir="/tmp/dkr")
        result = self.exporter.export(self.source, config)
        df = result.files["Dockerfile"]
        self.assertIn("FROM python:3.12-slim", df)

    def test_export_docker_with_tests(self):
        config = ExportConfig(
            target=ExportTarget.DOCKER, output_dir="/tmp/dkr", include_tests=True
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("tests/test_docker.py", result.files)

    def test_export_mobile_returns_project_structure(self):
        config = ExportConfig(
            target=ExportTarget.MOBILE, output_dir="/tmp/mob", entry_point="main.zy"
        )
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertIn("app/__init__.py", result.files)
        self.assertIn("app/main.py", result.files)
        self.assertIn("app/main_view.py", result.files)
        self.assertIn("requirements.txt", result.files)

    def test_export_mobile_with_tests(self):
        config = ExportConfig(
            target=ExportTarget.MOBILE, output_dir="/tmp/mob", include_tests=True
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("tests/test_mobile.py", result.files)

    def test_export_library_returns_setup_py(self):
        config = ExportConfig(
            target=ExportTarget.LIBRARY, output_dir="/tmp/lib", entry_point="mylib.zy"
        )
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertIn("mylib/__init__.py", result.files)
        self.assertIn("setup.py", result.files)
        self.assertIn("requirements.txt", result.files)

    def test_export_library_with_docs(self):
        config = ExportConfig(
            target=ExportTarget.LIBRARY,
            output_dir="/tmp/lib",
            entry_point="lib.zy",
            include_docs=True,
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("README.md", result.files)

    def test_export_library_with_tests(self):
        config = ExportConfig(
            target=ExportTarget.LIBRARY,
            output_dir="/tmp/lib",
            entry_point="lib.zy",
            include_tests=True,
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("tests/test_library.py", result.files)

    def test_export_invalid_target_raises(self):
        config = ExportConfig(target="nonexistent", output_dir="/tmp")  # type: ignore
        with self.assertRaises(ExportError) as ctx:
            self.exporter.export(self.source, config)
        self.assertIn("Unsupported export target", str(ctx.exception))

    def test_export_result_fields(self):
        config = ExportConfig(target=ExportTarget.WEB, output_dir="/tmp/web")
        result = self.exporter.export(self.source, config)
        self.assertTrue(result.success)
        self.assertEqual(result.target, ExportTarget.WEB)
        self.assertIsInstance(result.files, dict)
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.warnings, list)

    def test_export_result_uses_entry_point_name(self):
        config = ExportConfig(
            target=ExportTarget.WEB, output_dir="/tmp/web", entry_point="custom.zy"
        )
        result = self.exporter.export(self.source, config)
        self.assertIn("custom.html", result.files)
        self.assertIn("custom.zy", result.files)

    def test_export_docker_dockerignore_content(self):
        config = ExportConfig(target=ExportTarget.DOCKER, output_dir="/tmp/dkr")
        result = self.exporter.export(self.source, config)
        ignore = result.files[".dockerignore"]
        self.assertIn("__pycache__", ignore)
        self.assertIn(".env", ignore)
        self.assertIn(".git", ignore)

    def test_export_docker_compose_content(self):
        config = ExportConfig(target=ExportTarget.DOCKER, output_dir="/tmp/dkr")
        result = self.exporter.export(self.source, config)
        compose = result.files["docker-compose.yml"]
        self.assertIn("version:", compose)
        self.assertIn("build: .", compose)
        self.assertIn("8080:8080", compose)


class TestExportError(unittest.TestCase):
    def test_export_error_is_exception(self):
        self.assertTrue(issubclass(ExportError, Exception))
        err = ExportError("something broke")
        self.assertEqual(str(err), "something broke")


if __name__ == "__main__":
    unittest.main()
