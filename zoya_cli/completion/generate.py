"""Shell completion script generation for bash, zsh, fish, and PowerShell."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import List

from zoya_cli.core.registry import registry


def generate_bash() -> str:
    commands = [c.name for c in registry.all_leaf_commands()]
    return textwrap.dedent(f"""\
        # Zoya CLI shell completion for bash
        _zoya_completions() {{
            local cur="${{COMP_WORDS[COMP_CWORD]}}"
            local prev="${{COMP_WORDS[COMP_CWORD-1]}}"
            COMPREPLY=( $(compgen -W "{" ".join(commands)}" -- "$cur") )
            return 0
        }}
        complete -F _zoya_completions zoya
    """)


def generate_zsh() -> str:
    commands = [c.name for c in registry.all_leaf_commands()]
    return textwrap.dedent(f"""\
        # Zoya CLI shell completion for zsh
        #compdef zoya
        _zoya() {{
            local curcontext="$curcontext" state line
            typeset -A opt_args
            _arguments \\
                '1: :->command' \\
                '*: :->args'
            case $state in
                command)
                    compadd {" ".join(commands)}
                    ;;
            esac
        }}
        _zoya "$@"
    """)


def generate_fish() -> str:
    commands = [c.name for c in registry.all_leaf_commands()]
    cmds_str = "\n".join(f"    complete -c zoya -a '{c}' -d ''" for c in commands)
    return textwrap.dedent(f"""\
        # Zoya CLI shell completion for fish
        {cmds_str}
    """)


def generate_powershell() -> str:
    commands = [c.name for c in registry.all_leaf_commands()]
    cmd_strings = "; ".join(f"'zoya {c}'" for c in commands)
    return textwrap.dedent(f"""\
        # Zoya CLI shell completion for PowerShell
        Register-ArgumentCompleter -Native -CommandName zoya -ScriptBlock {{
            param($wordToComplete, $commandAst, $cursorPosition)
            $commands = @({cmd_strings})
            $commands | Where-Object {{ $_ -like "*$wordToComplete*" }}
        }}
    """)


def write_completion_scripts(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = {
        "zoya.bash": generate_bash(),
        "zoya.zsh": generate_zsh(),
        "zoya.fish": generate_fish(),
        "zoya.ps1": generate_powershell(),
    }
    for name, content in scripts.items():
        (output_dir / name).write_text(content, encoding="utf-8")
