#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_evidence_pack.py"
SHA = "a" * 64


class ValidateEvidencePackTest(unittest.TestCase):
    def write_pack(
        self,
        root: Path,
        *,
        pages: tuple[int, ...] = (1, 2, 3),
        visual_status: str = "not_required",
        referenced_card: str = "EC-001",
        limitation_status: str = "covered",
        method_coverage_cards: tuple[str, ...] = ("EC-001",),
    ) -> Path:
        pack = root / "evidence-pack"
        pack.mkdir()
        (pack / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source_sha256": SHA,
                    "pdf_page_count": 3,
                }
            ),
            encoding="utf-8",
        )

        ledger = []
        for page in pages:
            ledger.append(
                {
                    "pdf_page": page,
                    "page_type": "methods" if page == 2 else "front-or-results",
                    "review_status": "reviewed",
                    "visual_status": visual_status if page == 2 else "not_required",
                    "evidence_cards": [referenced_card] if page == 2 else [],
                    "open_check": "",
                }
            )
        (pack / "page-ledger.jsonl").write_text(
            "\n".join(json.dumps(row) for row in ledger) + "\n",
            encoding="utf-8",
        )

        (pack / "evidence-cards.jsonl").write_text(
            json.dumps(
                {
                    "card_id": "EC-001",
                    "source_sha256": SHA,
                    "pdf_page": 2,
                    "section": "Methods",
                    "claim_type": "method",
                    "content": "The paper defines the computational method.",
                    "evidence": "PDF p. 2, Methods",
                    "uncertainty": "none",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        dimensions = {
            "research_question": "covered",
            "method": "covered",
            "data": "covered",
            "results": "covered",
            "limitations": limitation_status,
            "relations": "none-found",
        }
        coverage_cards = {
            dimension: (["EC-001"] if status == "covered" else [])
            for dimension, status in dimensions.items()
        }
        coverage_cards["method"] = list(method_coverage_cards)
        (pack / "coverage.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "dimensions": dimensions,
                    "evidence_cards": coverage_cards,
                }
            ),
            encoding="utf-8",
        )
        return pack

    def run_validator(self, pack: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(pack)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_complete_pack_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            result = self.run_validator(pack)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["page_coverage"], "3/3")

    def test_missing_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp), pages=(1, 3))
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing PDF pages: 2", result.stdout)

    def test_pending_visual_review_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp), visual_status="pending")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("visual review pending on PDF page 2", result.stdout)

    def test_unknown_card_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp), referenced_card="EC-404")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown Evidence Card EC-404", result.stdout)

    def test_unresolved_coverage_dimension_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp), limitation_status="pending")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("coverage dimension limitations is pending", result.stdout)

    def test_covered_dimension_without_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp), method_coverage_cards=())
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "covered dimension method has no Evidence Cards", result.stdout
        )

    def test_non_string_states_report_errors_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            ledger_path = pack / "page-ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            rows[0]["review_status"] = []
            ledger_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            coverage_path = pack / "coverage.json"
            coverage = json.loads(coverage_path.read_text())
            coverage["dimensions"]["method"] = {}
            coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertIn("invalid review_status", result.stdout)
        self.assertIn("coverage dimension method has invalid state", result.stdout)

    def test_non_utf8_required_file_reports_error_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            (pack / "manifest.json").write_bytes(b"\xff\xfe")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertIn("cannot read manifest.json as UTF-8", result.stdout)

    def test_coverage_card_must_be_linked_from_its_pdf_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            ledger_path = pack / "page-ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            rows[1]["evidence_cards"] = []
            ledger_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Evidence Card EC-001 is not linked from PDF page 2", result.stdout
        )

    def test_non_string_card_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            card_path = pack / "evidence-cards.jsonl"
            card = json.loads(card_path.read_text())
            card["content"] = {"text": "claim"}
            card_path.write_text(json.dumps(card) + "\n", encoding="utf-8")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Evidence Card EC-001 content must be a string", result.stdout)

    def test_unknown_coverage_dimension_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            coverage_path = pack / "coverage.json"
            coverage = json.loads(coverage_path.read_text())
            coverage["dimensions"]["reslts"] = "covered"
            coverage["evidence_cards"]["reslts"] = ["EC-001"]
            coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown coverage dimension reslts", result.stdout)

    def test_none_found_dimension_cannot_reference_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            coverage_path = pack / "coverage.json"
            coverage = json.loads(coverage_path.read_text())
            coverage["evidence_cards"]["relations"] = ["EC-001"]
            coverage_path.write_text(json.dumps(coverage), encoding="utf-8")
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "none-found dimension relations must not reference Evidence Cards",
            result.stdout,
        )

    def test_sha_comparison_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            manifest_path = pack / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["source_sha256"] = SHA.upper()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = self.run_validator(pack)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_required_visual_page_needs_existing_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            ledger_path = pack / "page-ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            rows[1]["page_type"] = "table"
            rows[1]["visual_status"] = "reviewed"
            rows[1]["rendered_path"] = "rendered/page-0002.png"
            ledger_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing rendered artifact for PDF page 2", result.stdout)

    def test_required_visual_page_with_render_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            rendered = pack / "rendered" / "page-0002.png"
            rendered.parent.mkdir()
            rendered.write_bytes(b"PNG fixture")
            ledger_path = pack / "page-ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            rows[1]["page_type"] = "table"
            rows[1]["visual_status"] = "reviewed"
            rows[1]["rendered_path"] = "rendered/page-0002.png"
            ledger_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(pack)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_non_string_page_type_reports_error_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            ledger_path = pack / "page-ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            rows[0]["page_type"] = []
            ledger_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertIn("PDF page 1 has invalid page_type", result.stdout)

    def test_unknown_page_type_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self.write_pack(Path(tmp))
            ledger_path = pack / "page-ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            rows[1]["page_type"] = "tabl"
            ledger_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(pack)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PDF page 2 has unknown page_type tabl", result.stdout)


if __name__ == "__main__":
    unittest.main()
