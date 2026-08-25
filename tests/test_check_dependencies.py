#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fake_poppler import make_python_tool, tool_environment


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "check_dependencies.py"


class DependencyDoctorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        self.env = tool_environment(self.bin)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_doctor(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            text=True,
            capture_output=True,
            env=self.env,
        )

    def test_reports_ready_when_all_poppler_commands_exist(self) -> None:
        for name in ("pdfinfo", "pdftotext", "pdftoppm"):
            make_python_tool(self.bin, name, "raise SystemExit(0)\n")

        result = self.run_doctor()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ready"])
        self.assertEqual(report["missing"], [])
        self.assertEqual(
            {item["name"] for item in report["dependencies"]},
            {"pdfinfo", "pdftotext", "pdftoppm"},
        )

    def test_reports_missing_poppler_and_actionable_install_hint(self) -> None:
        make_python_tool(self.bin, "pdftotext", "raise SystemExit(0)\n")
        make_python_tool(self.bin, "pdftoppm", "raise SystemExit(0)\n")

        result = self.run_doctor()
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["ready"])
        self.assertEqual(report["missing"], ["pdfinfo"])
        self.assertTrue(report["install_hints"])
        self.assertIn("poppler", " ".join(report["install_hints"]).lower())


if __name__ == "__main__":
    unittest.main()
