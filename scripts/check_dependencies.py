#!/usr/bin/env python3
"""Report whether the PDF reader's external runtime dependencies are ready."""

import json
import platform
import shutil
import sys


DEPENDENCIES = (
    ("pdfinfo", "PDF metadata and page count"),
    ("pdftotext", "layout-preserving page text"),
    ("pdftoppm", "visual PNG page rendering"),
)


def install_hints(system: str):
    if system == "Darwin":
        return ["macOS (Homebrew): brew install poppler"]
    if system == "Windows":
        return [
            "Windows: install a maintained Poppler build and add the directory "
            "containing pdfinfo.exe, pdftotext.exe, and pdftoppm.exe to PATH",
            "Windows (Chocolatey, if available): choco install poppler",
        ]
    return [
        "Debian/Ubuntu: sudo apt-get install poppler-utils",
        "Fedora/RHEL: sudo dnf install poppler-utils",
        "Arch Linux: sudo pacman -S poppler",
    ]


def main() -> int:
    dependencies = []
    missing = []
    for name, purpose in DEPENDENCIES:
        path = shutil.which(name)
        dependencies.append(
            {"name": name, "purpose": purpose, "found": bool(path), "path": path}
        )
        if not path:
            missing.append(name)
    report = {
        "schema_version": 1,
        "platform": platform.system() or "Unknown",
        "ready": not missing,
        "missing": missing,
        "dependencies": dependencies,
        "install_hints": install_hints(platform.system()) if missing else [],
        "note": (
            "Unit tests use isolated fake Poppler commands; run this doctor to "
            "verify the real PDF runtime."
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
