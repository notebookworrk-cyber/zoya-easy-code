from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from zoya.cli import main, run_file, show_examples


class TestRunFile:
    def test_file_not_found(self) -> None:
        with pytest.raises(SystemExit):
            run_file("nonexistent_file.zoya")

    def test_valid_file(self, tmp_path) -> None:
        f = tmp_path / "test.zoya"
        f.write_text('print "hello"\n')
        run_file(str(f))


class TestShowExamples:
    def test_show_examples(self) -> None:
        show_examples()


class TestMain:
    def test_version(self) -> None:
        test_args = ["zoya", "--version"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

    def test_examples(self) -> None:
        test_args = ["zoya", "--examples"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

    def test_no_args(self) -> None:
        test_args = ["zoya"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    def test_inline_command(self) -> None:
        test_args = ["zoya", "-c", 'print "hello"']
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0

    def test_inline_command_error(self) -> None:
        test_args = ["zoya", "-c", "x = "]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    def test_docs_subcommand(self) -> None:
        test_args = ["zoya", "docs"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code in (0, 1)
