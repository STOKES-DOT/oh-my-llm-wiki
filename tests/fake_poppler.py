"""Cross-platform fake command helpers for PDF-reader tests."""

import os
from pathlib import Path
import shlex
import stat
import sys
from typing import Dict


def make_python_tool(bin_dir: Path, name: str, source: str) -> Path:
    implementation = bin_dir / f"_{name}_impl.py"
    implementation.write_text(source)
    if os.name == "nt":
        wrapper = bin_dir / f"{name}.cmd"
        wrapper.write_text(
            f'@echo off\r\n"{sys.executable}" "{implementation}" %*\r\n'
        )
    else:
        wrapper = bin_dir / name
        wrapper.write_text(
            "#!/bin/sh\n"
            f"exec {shlex.quote(sys.executable)} "
            f"{shlex.quote(str(implementation))} \"$@\"\n"
        )
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    return wrapper


def tool_environment(bin_dir: Path) -> Dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(bin_dir)
    if os.name == "nt":
        extensions = env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
        if ".CMD" not in extensions.upper().split(";"):
            extensions += ";.CMD"
        env["PATHEXT"] = extensions
    return env
