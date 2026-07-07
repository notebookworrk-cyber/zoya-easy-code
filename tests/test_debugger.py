from __future__ import annotations

from zoya.tools.debugger import DebugInterpreter, debug


class TestDebugInterpreter:
    def test_should_pause_stepping(self) -> None:
        from zoya.ast import Number

        di = DebugInterpreter(["print 1"], breakpoints=set())
        di._stepping = True
        assert di._should_pause(Number(1)) is True

    def test_should_pause_breakpoint(self) -> None:
        from zoya.ast import Number

        n = Number(1)
        n.line = 1
        di = DebugInterpreter(["print 1"], breakpoints={1})
        di._stepping = False
        assert di._should_pause(n) is True

    def test_should_pause_no_breakpoint(self) -> None:
        from zoya.ast import Number

        n = Number(1)
        n.line = 5
        di = DebugInterpreter(["print 1"], breakpoints={1})
        di._stepping = False
        assert di._should_pause(n) is False

    def test_show_context(self) -> None:
        di = DebugInterpreter(["line1", "line2", "line3", "line4"], breakpoints=set())
        di._call_stack = ["main"]
        di._show_context(2)
        # Should not raise

    def test_do_print_defined_var(self) -> None:
        from zoya.environment import Environment

        env = Environment()
        env.define("x", 42)
        di = DebugInterpreter([""])
        di.current_env = env
        di._do_print("x")

    def test_do_print_undefined(self) -> None:
        from zoya.environment import Environment

        env = Environment()
        di = DebugInterpreter([""])
        di.current_env = env
        di._do_print("y")

    def test_do_break_set(self) -> None:
        di = DebugInterpreter([""], breakpoints=set())
        di._do_break("5")
        assert 5 in di.breakpoints

    def test_do_break_remove(self) -> None:
        di = DebugInterpreter([""], breakpoints={5})
        di._do_break("5")
        assert 5 not in di.breakpoints

    def test_do_break_invalid(self) -> None:
        di = DebugInterpreter([""], breakpoints=set())
        di._do_break("abc")

    def test_show_vars(self) -> None:
        from zoya.environment import Environment

        env = Environment()
        env.define("x", 1)
        env.define("_hidden", 2)
        di = DebugInterpreter([""])
        di.current_env = env
        di._show_vars()

    def test_show_stack_empty(self) -> None:
        di = DebugInterpreter([""])
        di._call_stack = []
        di._show_stack()

    def test_show_stack_with_frames(self) -> None:
        di = DebugInterpreter([""])
        di._call_stack = ["a", "b"]
        di._show_stack()

    def test_show_help(self) -> None:
        DebugInterpreter._show_help()

    def test_debug_basic(self) -> None:
        debug('print "hello"\n')

    def test_debug_with_break_comment(self) -> None:
        debug('// break\nprint "hello"\n')
