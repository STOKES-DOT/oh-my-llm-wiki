#!/usr/bin/env python3
"""Validate structural completeness of an LLM Wiki Evidence Pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
COVERAGE_DIMENSIONS = (
    "research_question",
    "method",
    "data",
    "results",
    "limitations",
    "relations",
)
COVERAGE_STATES = {"covered", "none-found", "not-applicable"}
REVIEW_STATES = {"reviewed", "unresolved"}
VISUAL_STATES = {"not_required", "reviewed", "pending"}
VISUAL_REQUIRED_PAGE_TYPES = {
    "figure",
    "table",
    "equation",
    "key-numerical",
    "identity-ambiguous",
    "extraction-failure",
}
PAGE_TYPES = {
    "title",
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "limitations",
    "conclusion",
    "appendix",
    "references",
    "figure",
    "table",
    "equation",
    "key-numerical",
    "identity-ambiguous",
    "extraction-failure",
    "visual-only",
    "boilerplate",
    "front-or-results",
}


def safe_read_text(path: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing required file {path.name}")
    except UnicodeError:
        errors.append(f"cannot read {path.name} as UTF-8")
    except OSError as exc:
        errors.append(f"cannot read {path.name}: {exc.strerror or exc}")
    return None


def read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    text = safe_read_text(path, errors)
    if text is None:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path.name}: {exc.msg}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name} must contain a JSON object")
        return {}
    return value


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    text = safe_read_text(path, errors)
    if text is None:
        return []
    lines = text.splitlines()

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                f"invalid JSON in {path.name} line {line_number}: {exc.msg}"
            )
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.name} line {line_number} must be a JSON object")
            continue
        records.append(value)
    return records


def validate_evidence_pack(pack: Path) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(pack / "manifest.json", errors)
    ledger = read_jsonl(pack / "page-ledger.jsonl", errors)
    cards = read_jsonl(pack / "evidence-cards.jsonl", errors)
    coverage = read_json(pack / "coverage.json", errors)

    source_sha = manifest.get("source_sha256")
    if not isinstance(source_sha, str) or not SHA256_RE.fullmatch(source_sha):
        errors.append("manifest source_sha256 must be 64 hexadecimal characters")
        normalized_source_sha = ""
    else:
        normalized_source_sha = source_sha.lower()

    page_count = manifest.get("pdf_page_count")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        errors.append("manifest pdf_page_count must be a positive integer")
        page_count = 0

    seen_pages: set[int] = set()
    duplicate_pages: set[int] = set()
    ledger_card_refs: list[tuple[int, str]] = []
    ledger_refs_by_page: dict[int, set[str]] = {}
    for record in ledger:
        page = record.get("pdf_page")
        if not isinstance(page, int) or isinstance(page, bool):
            errors.append("page-ledger record has a non-integer pdf_page")
            continue
        if page in seen_pages:
            duplicate_pages.add(page)
        seen_pages.add(page)

        page_type = record.get("page_type")
        if not isinstance(page_type, str):
            errors.append(f"PDF page {page} has invalid page_type")
            normalized_page_type = ""
        else:
            normalized_page_type = page_type.strip()
            if not normalized_page_type:
                errors.append(f"PDF page {page} has no page_type")
            elif normalized_page_type not in PAGE_TYPES:
                errors.append(
                    f"PDF page {page} has unknown page_type {normalized_page_type}"
                )

        review_status = record.get("review_status")
        if not isinstance(review_status, str) or review_status not in REVIEW_STATES:
            errors.append(f"PDF page {page} has invalid review_status {review_status!r}")
        if review_status == "unresolved":
            open_check = record.get("open_check")
            if not isinstance(open_check, str) or not open_check.strip():
                errors.append(f"unresolved PDF page {page} has no open_check")

        visual_status = record.get("visual_status")
        if not isinstance(visual_status, str) or visual_status not in VISUAL_STATES:
            errors.append(f"PDF page {page} has invalid visual_status {visual_status!r}")
        elif visual_status == "pending":
            errors.append(f"visual review pending on PDF page {page}")

        visual_required = normalized_page_type in VISUAL_REQUIRED_PAGE_TYPES
        if visual_required and visual_status != "reviewed":
            errors.append(f"visual review required on PDF page {page}")
        if visual_status == "reviewed" or visual_required:
            rendered_path = record.get("rendered_path")
            if not isinstance(rendered_path, str) or not rendered_path.strip():
                errors.append(f"missing rendered artifact for PDF page {page}")
            else:
                pack_root = pack.resolve()
                artifact = (pack / rendered_path).resolve()
                if not artifact.is_relative_to(pack_root) or not artifact.is_file():
                    errors.append(f"missing rendered artifact for PDF page {page}")

        references = record.get("evidence_cards", [])
        if not isinstance(references, list):
            errors.append(f"PDF page {page} evidence_cards must be a list")
        else:
            for card_id in references:
                if not isinstance(card_id, str) or not card_id:
                    errors.append(f"PDF page {page} has an invalid Evidence Card ID")
                else:
                    ledger_card_refs.append((page, card_id))
                    ledger_refs_by_page.setdefault(page, set()).add(card_id)

    for page in sorted(duplicate_pages):
        errors.append(f"duplicate PDF page in ledger: {page}")

    if page_count:
        expected_pages = set(range(1, page_count + 1))
        missing_pages = sorted(expected_pages - seen_pages)
        extra_pages = sorted(seen_pages - expected_pages)
        if missing_pages:
            errors.append(
                "missing PDF pages: " + ", ".join(str(page) for page in missing_pages)
            )
        if extra_pages:
            errors.append(
                "out-of-range PDF pages: "
                + ", ".join(str(page) for page in extra_pages)
            )

    card_ids: set[str] = set()
    for card in cards:
        card_id = card.get("card_id")
        if not isinstance(card_id, str) or not card_id:
            errors.append("Evidence Card has no valid card_id")
            continue
        if card_id in card_ids:
            errors.append(f"duplicate Evidence Card ID {card_id}")
        card_ids.add(card_id)

        card_sha = card.get("source_sha256")
        if (
            not isinstance(card_sha, str)
            or not SHA256_RE.fullmatch(card_sha)
            or card_sha.lower() != normalized_source_sha
        ):
            errors.append(f"Evidence Card {card_id} source_sha256 does not match manifest")

        page = card.get("pdf_page")
        if (
            not isinstance(page, int)
            or isinstance(page, bool)
            or page < 1
            or (page_count and page > page_count)
        ):
            errors.append(f"Evidence Card {card_id} has out-of-range pdf_page")

        for field in ("section", "claim_type", "content", "evidence"):
            value = card.get(field)
            if not isinstance(value, str):
                errors.append(f"Evidence Card {card_id} {field} must be a string")
            elif not value.strip():
                errors.append(f"Evidence Card {card_id} has no {field}")

        if isinstance(page, int) and card_id not in ledger_refs_by_page.get(page, set()):
            errors.append(f"Evidence Card {card_id} is not linked from PDF page {page}")

    for page, card_id in ledger_card_refs:
        if card_id not in card_ids:
            errors.append(
                f"PDF page {page} references unknown Evidence Card {card_id}"
            )

    dimensions = coverage.get("dimensions")
    if not isinstance(dimensions, dict):
        errors.append("coverage.json dimensions must be an object")
        dimensions = {}
    coverage_card_refs = coverage.get("evidence_cards")
    if not isinstance(coverage_card_refs, dict):
        errors.append("coverage.json evidence_cards must be an object")
        coverage_card_refs = {}
    unknown_dimensions = (set(dimensions) | set(coverage_card_refs)) - set(
        COVERAGE_DIMENSIONS
    )
    for dimension in sorted(unknown_dimensions):
        errors.append(f"unknown coverage dimension {dimension}")
    for dimension in COVERAGE_DIMENSIONS:
        state = dimensions.get(dimension)
        if not isinstance(state, str):
            errors.append(f"coverage dimension {dimension} has invalid state")
        elif state not in COVERAGE_STATES:
            errors.append(f"coverage dimension {dimension} is {state or 'missing'}")
        references = coverage_card_refs.get(dimension, [])
        if not isinstance(references, list):
            errors.append(
                f"coverage dimension {dimension} evidence_cards must be a list"
            )
            continue
        if state == "covered" and not references:
            errors.append(f"covered dimension {dimension} has no Evidence Cards")
        if isinstance(state, str) and state in {"none-found", "not-applicable"} and references:
            errors.append(
                f"{state} dimension {dimension} must not reference Evidence Cards"
            )
        for card_id in references:
            if not isinstance(card_id, str) or card_id not in card_ids:
                errors.append(
                    f"coverage dimension {dimension} references unknown "
                    f"Evidence Card {card_id}"
                )

    covered_pages = len(
        {
            page
            for page in seen_pages
            if isinstance(page, int) and 1 <= page <= page_count
        }
    )
    return {
        "schema_version": 1,
        "valid": not errors,
        "source_sha256": normalized_source_sha or source_sha,
        "page_coverage": f"{covered_pages}/{page_count}",
        "evidence_card_count": len(card_ids),
        "errors": errors,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate page coverage and provenance in an Evidence Pack."
    )
    parser.add_argument("evidence_pack", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = validate_evidence_pack(args.evidence_pack.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
