#!/usr/bin/env python3
"""Extract page-bounded PDF evidence with optional visual renders.

The script uses Poppler command-line tools and writes derived artifacts only to
an explicit output directory. It never modifies the source PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Dict, Iterable, List, Optional


SCHEMA_VERSION = 1


def fail(message: str) -> "None":
    raise SystemExit(message)


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        fail(
            f"required tool '{name}' was not found in PATH; run "
            "scripts/check_dependencies.py for platform-specific Poppler setup "
            "guidance, then retry"
        )
    return path


def run_text(command: List[str]) -> str:
    try:
        completed = subprocess.run(
            command, check=True, text=True, capture_output=True
        )
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip() or "no diagnostic output"
        fail(f"command failed ({' '.join(command)}): {details}")
    return completed.stdout


def parse_pdfinfo(output: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def parse_page_spec(spec: Optional[str], page_count: int) -> List[int]:
    if spec is None:
        return list(range(1, page_count + 1))
    pages = set()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            fail(f"invalid empty page component in '{spec}'")
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            if not start_text.isdigit() or not end_text.isdigit():
                fail(f"invalid page range '{part}'")
            start, end = int(start_text), int(end_text)
            if start > end:
                fail(f"invalid descending page range '{part}'")
            pages.update(range(start, end + 1))
        else:
            if not part.isdigit():
                fail(f"invalid page number '{part}'")
            pages.add(int(part))
    ordered = sorted(pages)
    invalid = [page for page in ordered if page < 1 or page > page_count]
    if invalid:
        fail(
            f"page selection {invalid} is outside PDF page range 1-{page_count}"
        )
    return ordered


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


HEADING_KINDS = {
        "METHOD": "methods",
        "METHODS": "methods",
        "METHODOLOGY": "methods",
        "COMPUTATIONAL METHOD": "methods",
        "COMPUTATIONAL METHODS": "methods",
        "COMPUTATIONAL DETAILS": "methods",
        "THEORY AND METHODS": "methods",
        "EXPERIMENTS": "results",
        "RESULTS": "results",
        "RESULTS AND DISCUSSION": "results",
        "EXPERIMENTAL RESULTS": "results",
        "DISCUSSION": "discussion",
        "SUMMARY": "conclusion",
        "SUMMARY AND DISCUSSION": "conclusion",
        "CONCLUSION": "conclusion",
        "CONCLUSIONS": "conclusion",
        "LIMITATION": "limitations",
        "LIMITATIONS": "limitations",
        "LIMITATIONS AND FUTURE WORK": "limitations",
        "FUTURE WORK": "limitations",
        "FUTURE DIRECTIONS": "limitations",
        "OUTLOOK": "limitations",
}


NUMBERED_HEADING = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?P<number>[IVXLCDM]+|\d+(?:\.\d+)*)[.)]?\s+"
    r"(?P<title>"
    r"RESULTS\s+AND\s+DISCUSSION|SUMMARY\s+AND\s+DISCUSSION|"
    r"LIMITATIONS\s+AND\s+FUTURE\s+WORK|COMPUTATIONAL\s+METHODS?|"
    r"COMPUTATIONAL\s+DETAILS|THEORY\s+AND\s+METHODS|"
    r"EXPERIMENTAL\s+RESULTS|FUTURE\s+DIRECTIONS|FUTURE\s+WORK|"
    r"METHODS?|METHODOLOGY|EXPERIMENTS|RESULTS|DISCUSSION|"
    r"SUMMARY|CONCLUSIONS?|LIMITATIONS?|OUTLOOK"
    r")(?=\s{2,}|$)",
    flags=re.IGNORECASE,
)


def detect_heading(line: str) -> Optional[tuple[str, str]]:
    if not line.strip():
        return None
    numbered = NUMBERED_HEADING.search(line)
    if numbered:
        title = " ".join(numbered.group("title").upper().split())
        kind = HEADING_KINDS.get(title)
        if kind:
            return kind, f"{numbered.group('number').upper()}. {title}"

    stripped = " ".join(line.strip().split())
    if len(stripped) > 120:
        return None
    normalized = stripped.upper().strip(" .:-")
    if normalized in HEADING_KINDS:
        return HEADING_KINDS[normalized], normalized
    if normalized.startswith("APPENDIX"):
        return "appendix", normalized
    return None


def find_sections(page_text: Dict[int, str]) -> List[Dict[str, object]]:
    sections: List[Dict[str, object]] = []
    seen = set()
    for page, text in page_text.items():
        for line in text.splitlines():
            detected = detect_heading(line)
            if not detected:
                continue
            kind, heading = detected
            key = (page, heading, kind)
            if key not in seen:
                sections.append({"page": page, "heading": heading, "kind": kind})
                seen.add(key)
    return sections


def write_section_markdown(path: Path, sections: Iterable[Dict[str, object]]) -> None:
    lines = [
        "# PDF section index\n\n",
        "Detected conservatively from heading-like lines; verify against the rendered page before citing layout-sensitive content.\n\n",
        "| PDF page | Kind | Heading |\n",
        "|---:|---|---|\n",
    ]
    for item in sections:
        heading = str(item["heading"]).replace("|", "\\|")
        lines.append(f"| {item['page']} | {item['kind']} | {heading} |\n")
    path.write_text("".join(lines), encoding="utf-8")


def reject_raw_output(output_dir: Path) -> None:
    parts = output_dir.resolve().parts
    for index in range(len(parts) - 1):
        if parts[index] == ".wiki" and parts[index + 1] == "raw":
            fail("derived PDF artifacts must not be written under .wiki/raw")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract page-bounded PDF evidence using Poppler."
    )
    parser.add_argument("pdf", type=Path, help="source PDF (read-only)")
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="directory for derived artifacts"
    )
    parser.add_argument(
        "--pages", help="pages to extract, e.g. '1-3,7'; default: every page"
    )
    parser.add_argument(
        "--render", help="pages to render as PNG, e.g. '2,4-5'; default: none"
    )
    parser.add_argument("--dpi", type=int, default=160, help="PNG render DPI")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    pdf = args.pdf.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not pdf.is_file():
        fail(f"PDF does not exist: {pdf}")
    if pdf.suffix.lower() != ".pdf":
        fail(f"source does not have a .pdf extension: {pdf}")
    if args.dpi < 72 or args.dpi > 600:
        fail("--dpi must be between 72 and 600")
    reject_raw_output(output_dir)

    pdfinfo_tool = require_tool("pdfinfo")
    pdftotext_tool = require_tool("pdftotext")
    pdfinfo = parse_pdfinfo(run_text([pdfinfo_tool, str(pdf)]))
    try:
        page_count = int(pdfinfo["Pages"])
    except (KeyError, ValueError):
        fail("pdfinfo did not report a valid Pages value")
    pages = parse_page_spec(args.pages, page_count)
    render_pages = parse_page_spec(args.render, page_count) if args.render else []

    output_dir.mkdir(parents=True, exist_ok=True)
    page_text: Dict[int, str] = {}
    marked_parts = []
    for page in pages:
        text = run_text(
            [
                pdftotext_tool,
                "-f",
                str(page),
                "-l",
                str(page),
                "-layout",
                str(pdf),
                "-",
            ]
        ).replace("\f", "")
        page_text[page] = text.rstrip() + "\n"
        marked_parts.append(f"===== PDF PAGE {page} =====\n{text.rstrip()}\n\n")

    text_path = output_dir / "layout_text_page_marked.txt"
    text_path.write_text("".join(marked_parts), encoding="utf-8")
    sections = find_sections(page_text)
    section_json_path = output_dir / "section_index.json"
    section_json_path.write_text(
        json.dumps(sections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    section_md_path = output_dir / "section_index.md"
    write_section_markdown(section_md_path, sections)

    if render_pages:
        pdftoppm_tool = require_tool("pdftoppm")
        rendered_dir = output_dir / "rendered"
        rendered_dir.mkdir(parents=True, exist_ok=True)
        for page in render_pages:
            prefix = rendered_dir / f"page-{page:04d}"
            run_text(
                [
                    pdftoppm_tool,
                    "-singlefile",
                    "-png",
                    "-r",
                    str(args.dpi),
                    "-f",
                    str(page),
                    "-l",
                    str(page),
                    str(pdf),
                    str(prefix),
                ]
            )

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "source_path": str(pdf),
        "source_name": pdf.name,
        "source_size_bytes": pdf.stat().st_size,
        "source_sha256": sha256_file(pdf),
        "page_count": page_count,
        "pages_selected": pages,
        "rendered_pages": render_pages,
        "render_dpi": args.dpi if render_pages else None,
        "pdfinfo": pdfinfo,
        "artifacts": {
            "page_marked_text": text_path.name,
            "section_index_json": section_json_path.name,
            "section_index_markdown": section_md_path.name,
            "rendered_directory": "rendered" if render_pages else None,
        },
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "source_sha256": metadata["source_sha256"],
                "page_count": page_count,
                "pages_selected": pages,
                "rendered_pages": render_pages,
                "section_hits": len(sections),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
