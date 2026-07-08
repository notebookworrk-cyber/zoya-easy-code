"""Tests for the Zoya CLI command dispatch engine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from zoya_cli.cli import main, _parse_options, _walk_tree
from zoya_cli.commands.base import Command, Option, OptionAction, Argument
from zoya_cli.core.errors import UsageError, CommandNotFoundError
from zoya_cli.core.registry import register, registry
from zoya_cli.commands import register_all


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _setup_registry():
    """Re-register all commands before each test."""
    registry.root.subcommands.clear()
    register_all()
    yield


# ---------------------------------------------------------------------------
# Test _walk_tree
# ---------------------------------------------------------------------------


class TestWalkTree:
    def test_top_level_command(self):
        cmd, remainder = _walk_tree(["version"])
        assert cmd.name == "version"
        assert remainder == []

    def test_nested_command(self):
        cmd, remainder = _walk_tree(["ai", "chat"])
        assert cmd.name == "chat"
        assert remainder == []

    def test_unknown_command(self):
        with pytest.raises(CommandNotFoundError):
            _walk_tree(["nonexistent"])

    def test_unknown_subcommand(self):
        with pytest.raises(CommandNotFoundError):
            _walk_tree(["ai", "nonexistent"])

    def test_remainder_passthrough(self):
        cmd, remainder = _walk_tree(["new", "my-project"])
        assert cmd.name == "new"
        assert remainder == ["my-project"]


# ---------------------------------------------------------------------------
# Test _parse_options
# ---------------------------------------------------------------------------


class TestParseOptions:
    def test_simple_flag(self):
        cmd = Command("test", options=[Option("--verbose", action=OptionAction.STORE_TRUE)])
        opts, args, rem = _parse_options(cmd, ["--verbose"])
        assert opts["--verbose"] is True

    def test_store_false(self):
        cmd = Command("test", options=[Option("--quiet", action=OptionAction.STORE_FALSE)])
        opts, args, rem = _parse_options(cmd, ["--quiet"])
        assert opts["--quiet"] is False

    def test_value_option(self):
        cmd = Command("test", options=[Option("--name", help="Name")])
        opts, args, rem = _parse_options(cmd, ["--name", "foo"])
        assert opts["--name"] == "foo"

    def test_value_option_with_equals(self):
        cmd = Command("test", options=[Option("--name", help="Name")])
        opts, args, rem = _parse_options(cmd, ["--name=foo"])
        assert opts["--name"] == "foo"

    def test_short_option(self):
        cmd = Command("test", options=[Option("--verbose", "-v", action=OptionAction.STORE_TRUE)])
        opts, args, rem = _parse_options(cmd, ["-v"])
        assert opts["--verbose"] is True

    def test_count_option(self):
        cmd = Command("test", options=[Option("--verbose", "-v", action=OptionAction.COUNT)])
        opts, args, rem = _parse_options(cmd, ["-v", "-v", "-v"])
        assert opts["--verbose"] == 3

    def test_append_option(self):
        cmd = Command("test", options=[Option("--file", action=OptionAction.APPEND)])
        opts, args, rem = _parse_options(cmd, ["--file", "a.txt", "--file", "b.txt"])
        assert opts["--file"] == ["a.txt", "b.txt"]

    def test_positional_args(self):
        cmd = Command("test", arguments=[Argument("files", "Files")])
        opts, args, rem = _parse_options(cmd, ["a.py", "b.py"])
        assert args == ["a.py", "b.py"]

    def test_double_dash_remainder(self):
        cmd = Command("test")
        opts, args, rem = _parse_options(cmd, ["--", "--extra", "foo"])
        assert rem == ["--extra", "foo"]

    def test_unknown_option_error(self):
        cmd = Command("test")
        with pytest.raises(UsageError):
            _parse_options(cmd, ["--bogus"])

    def test_option_with_choices(self):
        cmd = Command("test", options=[Option("--level", choices=["low", "high"])])
        opts, args, rem = _parse_options(cmd, ["--level", "high"])
        assert opts["--level"] == "high"

    def test_option_with_invalid_choice(self):
        cmd = Command("test", options=[Option("--level", choices=["low", "high"])])
        with pytest.raises(UsageError):
            _parse_options(cmd, ["--level", "medium"])

    def test_integer_option(self):
        cmd = Command("test", options=[Option("--count", value_type=int)])
        opts, args, rem = _parse_options(cmd, ["--count", "42"])
        assert opts["--count"] == 42

    def test_integer_option_error(self):
        cmd = Command("test", options=[Option("--count", value_type=int)])
        with pytest.raises(UsageError):
            _parse_options(cmd, ["--count", "not-a-number"])


# ---------------------------------------------------------------------------
# Test main dispatch
# ---------------------------------------------------------------------------


class TestMain:
    def test_no_args_shows_help(self):
        code = main([])
        assert code == 0

    def test_version_flag(self):
        code = main(["--version"])
        assert code == 0

    def test_unknown_command(self):
        code = main(["nonexistent"])
        assert code != 0

    def test_debug_flag(self):
        code = main(["--debug", "version"])
        assert code == 0

    def test_help_flag(self):
        code = main(["--help"])
        assert code == 0

    def test_subcommand_help(self):
        code = main(["ai", "--help"])
        assert code == 0

    def test_deep_help(self):
        code = main(["ai", "chat", "--help"])
        assert code == 0

    def test_game_help(self):
        code = main(["game", "--help"])
        assert code == 0


# ---------------------------------------------------------------------------
# Test Command model
# ---------------------------------------------------------------------------


class TestCommand:
    def test_is_leaf(self):
        leaf = Command("leaf", run=lambda ctx: 0)
        assert leaf.is_leaf() is True

    def test_is_not_leaf(self):
        group = Command("group")
        group.add_command(Command("sub"))
        assert group.is_leaf() is False

    def test_get_subcommand(self):
        group = Command("group")
        sub = Command("sub")
        group.add_command(sub)
        assert group.get_subcommand("sub") is sub

    def test_get_subcommand_missing(self):
        group = Command("group")
        assert group.get_subcommand("missing") is None

    def test_add_command_with_parent_ref(self):
        group = Command("group")
        sub = Command("sub")
        group.add_command(sub)
        assert len(group.subcommands) == 1

    def test_option_defaults(self):
        cmd = Command("test", options=[Option("--opt", default="val")])
        assert cmd.options[0].default == "val"

    def test_argument_metavar(self):
        arg = Argument("name", "Your name", metavar="NAME")
        assert arg.metavar == "NAME"


# ---------------------------------------------------------------------------
# Test Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_register_lookup(self):
        register(Command("test-cmd", run=lambda ctx: 0))
        found = registry.get(["test-cmd"])
        assert found is not None
        assert found.name == "test-cmd"

    def test_top_level(self):
        initial = len(registry.top_level())
        register(Command("test-top", run=lambda ctx: 0))
        assert len(registry.top_level()) == initial + 1

    def test_register_under_parent(self):
        parent = Command("parent-group")
        register(parent)
        register(Command("child-cmd", run=lambda ctx: 0), parent="parent-group")
        found = registry.get(["parent-group", "child-cmd"])
        assert found is not None

    def test_unknown_parent(self):
        with pytest.raises(KeyError):
            register(Command("orphan"), parent="nonexistent")

    def test_get_missing_path(self):
        assert registry.get(["nope"]) is None

    def test_all_leaf_commands(self):
        leaves = registry.all_leaf_commands()
        assert all(c.is_leaf() for c in leaves)
        assert len(leaves) > 10  # should have many leaves


# ---------------------------------------------------------------------------
# Test CliError hierarchy
# ---------------------------------------------------------------------------


class TestErrors:
    def test_usage_error_exit_code(self):
        err = UsageError("msg")
        assert err.exit_code == 2

    def test_command_not_found_error(self):
        err = CommandNotFoundError(command="bogus", suggestions=["build"])
        assert "bogus" in err.message
        assert err.exit_code != 0

    def test_error_hints(self):
        err = UsageError("msg", hints=["Try --help"])
        assert len(err.hints) > 0

    def test_error_add_hint(self):
        err = UsageError("msg")
        err.add_hint("Run with --debug")
        assert "Run with --debug" in err.hints
