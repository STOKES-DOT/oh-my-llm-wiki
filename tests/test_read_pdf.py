#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "read_pdf.py"


def make_executable(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class ReadPdfCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.pdf = self.root / "paper with spaces.pdf"
        self.pdf.write_bytes(b"%PDF-1.4\nfixture\n")

        make_executable(
            self.bin / "pdfinfo",
            "#!/bin/sh\n"
            "cat <<'EOF'\n"
            "Title:          Fixture Paper\n"
            "Author:         Test Author\n"
            "Pages:          3\n"
            "PDF version:    1.4\n"
            "EOF\n",
        )
        make_executable(
            self.bin / "pdftotext",
            "#!/bin/sh\n"
            "page=1\n"
            "while [ $# -gt 0 ]; do\n"
            "  if [ \"$1\" = \"-f\" ]; then page=$2; shift 2; continue; fi\n"
            "  shift\n"
            "done\n"
            "case \"$page\" in\n"
            "  1) printf 'Fixture Paper\\nAbstract body\\n' ;;\n"
            "  2) printf 'II.   METHODS                              side-column text\\nMethod body\\n' ;;\n"
            "  3) printf 'left-column text                           III.   RESULTS AND DISCUSSION\\nResult body\\nIV. CONCLUSION\\n' ;;\n"
            "esac\n",
        )
        make_executable(
            self.bin / "pdftoppm",
            "#!/bin/sh\n"
            "last=''\n"
            "for arg in \"$@\"; do last=$arg; done\n"
            "printf 'png' > \"${last}.png\"\n",
        )
        self.env = os.environ.copy()
        self.env["PATH"] = str(self.bin) + os.pathsep + self.env.get("PATH", "")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.pdf), *args],
            text=True,
            capture_output=True,
            env=self.env,
        )

    def test_extracts_metadata_page_marked_text_and_section_index(self) -> None:
        out = self.root / "out"
        result = self.run_cli("--output-dir", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)

        metadata = json.loads((out / "metadata.json").read_text())
        summary = json.loads(result.stdout)
        self.assertEqual(metadata["schema_version"], 1)
        self.assertEqual(metadata["page_count"], 3)
        self.assertEqual(metadata["pages_selected"], [1, 2, 3])
        self.assertEqual(
            metadata["source_sha256"], hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        )
        self.assertEqual(metadata["pdfinfo"]["Title"], "Fixture Paper")
        self.assertEqual(summary["source_sha256"], metadata["source_sha256"])

        text = (out / "layout_text_page_marked.txt").read_text()
        self.assertEqual(text.count("===== PDF PAGE "), 3)
        self.assertIn("===== PDF PAGE 2 =====\nII.   METHODS", text)

        sections = json.loads((out / "section_index.json").read_text())
        self.assertIn(
            {"page": 2, "heading": "II. METHODS", "kind": "methods"}, sections
        )
        self.assertIn(
            {
                "page": 3,
                "heading": "III. RESULTS AND DISCUSSION",
                "kind": "results",
            },
            sections,
        )
        self.assertTrue((out / "section_index.md").exists())

    def test_renders_selected_pages_without_rendering_every_page(self) -> None:
        out = self.root / "rendered-out"
        result = self.run_cli(
            "--output-dir", str(out), "--pages", "1-3", "--render", "2", "--dpi", "180"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((out / "rendered" / "page-0002.png").exists())
        self.assertFalse((out / "rendered" / "page-0001.png").exists())

        metadata = json.loads((out / "metadata.json").read_text())
        self.assertEqual(metadata["rendered_pages"], [2])
        self.assertEqual(metadata["render_dpi"], 180)

    def test_rejects_pages_outside_the_pdf(self) -> None:
        out = self.root / "bad-out"
        result = self.run_cli("--output-dir", str(out), "--pages", "4")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside PDF page range 1-3", result.stderr)


if __name__ == "__main__":
    unittest.main()
