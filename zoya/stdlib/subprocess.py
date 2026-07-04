from __future__ import annotations

import subprocess as _subprocess
from typing import Any


def load_module(interpreter: Any) -> Any:
    from zoya.interpreter import ZoyaModule

    def run(cmd: str | list[str]) -> dict[str, Any]:
        try:
            result = _subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    def run_output(cmd: str | list[str]) -> dict[str, Any]:
        try:
            result = _subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    def run_background(cmd: str | list[str]) -> dict[str, Any]:
        try:
            process = _subprocess.Popen(
                cmd,
                shell=isinstance(cmd, str),
                stdout=_subprocess.PIPE,
                stderr=_subprocess.PIPE,
                text=True,
            )
            return {
                "pid": process.pid,
                "returncode": None,
                "stdout": "",
                "stderr": "",
            }
        except Exception as e:
            return {"pid": -1, "returncode": -1, "stdout": "", "stderr": str(e)}

    funcs = {
        "run": run,
        "run_output": run_output,
        "run_background": run_background,
    }

    return ZoyaModule("subprocess", funcs)
