from __future__ import annotations

import pytest

from zoya.environment import Environment


class TestEnvironment:
    def test_define_and_get(self) -> None:
        env = Environment()
        env.define("x", 42)
        assert env.get("x") == 42

    def test_get_undefined_raises(self) -> None:
        env = Environment()
        with pytest.raises(NameError, match="'y' is not defined"):
            env.get("y")

    def test_set_existing_var(self) -> None:
        env = Environment()
        env.define("x", 1)
        env.set("x", 2)
        assert env.get("x") == 2

    def test_set_undefined_creates_var(self) -> None:
        env = Environment()
        env.set("x", 10)
        assert env.get("x") == 10

    def test_has_existing_var(self) -> None:
        env = Environment()
        env.define("x", 1)
        assert env.has("x") is True

    def test_has_missing_var(self) -> None:
        env = Environment()
        assert env.has("x") is False

    def test_parent_chain_get(self) -> None:
        parent = Environment()
        parent.define("x", 42)
        child = Environment(parent)
        assert child.get("x") == 42

    def test_parent_chain_has(self) -> None:
        parent = Environment()
        parent.define("x", 42)
        child = Environment(parent)
        assert child.has("x") is True

    def test_child_override(self) -> None:
        parent = Environment()
        parent.define("x", 1)
        child = Environment(parent)
        child.define("x", 2)
        assert child.get("x") == 2
        assert parent.get("x") == 1

    def test_set_in_parent(self) -> None:
        parent = Environment()
        parent.define("x", 1)
        child = Environment(parent)
        child.set("x", 99)
        assert parent.get("x") == 99

    def test_set_in_child_only(self) -> None:
        parent = Environment()
        child = Environment(parent)
        child.set("x", 42)
        assert child.get("x") == 42
        assert parent.has("x") is False

    def test_repr(self) -> None:
        env = Environment()
        env.define("a", 1)
        r = repr(env)
        assert "a" in r
        assert "1" in r

    def test_no_parent(self) -> None:
        env = Environment()
        assert env.parent is None

    def test_nested_parent_chain(self) -> None:
        grandparent = Environment()
        grandparent.define("a", 1)
        parent = Environment(grandparent)
        parent.define("b", 2)
        child = Environment(parent)
        child.define("c", 3)
        assert child.get("a") == 1
        assert child.get("b") == 2
        assert child.get("c") == 3
