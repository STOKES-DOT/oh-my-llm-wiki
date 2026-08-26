#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fake_poppler import make_python_tool, tool_environment


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "read_pdf.py"


class ReadPdfCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.pdf = self.root / "paper with spaces.pdf"
        self.pdf.write_bytes(b"%PDF-1.4\nfixture\n")

        make_python_tool(
            self.bin,
            "pdfinfo",
            "print('Title:          Fixture Paper')\n"
            "print('Author:         Test Author')\n"
            "print('Pages:          3')\n"
            "print('PDF version:    1.4')\n",
        )
        make_python_tool(
            self.bin,
            "pdftotext",
            "import sys\n"
            "args = sys.argv[1:]\n"
            "page = args[args.index('-f') + 1] if '-f' in args else '1'\n"
            "pages = {\n"
            "  '1': 'Fixture Paper\\nAbstract body\\n',\n"
            "  '2': 'II.   METHODS                              side-column text\\nMethod body\\n',\n"
            "  '3': 'left-column text                           III.   RESULTS AND DISCUSSION\\nResult body\\nIV. CONCLUSION\\n',\n"
            "}\n"
            "sys.stdout.write(pages[page])\n",
        )
        make_python_tool(
            self.bin,
            "pdftoppm",
            "from pathlib import Path\n"
            "import sys\n"
            "Path(sys.argv[-1] + '.png').write_bytes(b'png')\n",
        )
        self.env = tool_environment(self.bin)

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
