#!/usr/bin/env python3
"""Check a PDF page count using pypdf or pdfinfo."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_pdfinfo() -> str | None:
    if found := shutil.which("pdfinfo"):
        return found

    codex_cache = Path.home() / ".cache" / "codex-runtimes"
    for candidate in codex_cache.glob("*/dependencies/bin/pdfinfo"):
        if candidate.is_file():
            return str(candidate)
    return None


def count_with_pypdf(path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None
    return len(PdfReader(str(path)).pages)


def count_with_pdfinfo(path: Path) -> int | None:
    pdfinfo = find_pdfinfo()
    if not pdfinfo:
        return None
    result = subprocess.run([pdfinfo, str(path)], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError("pdfinfo did not report a page count")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PDF page count")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--expect", type=int, required=True)
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"Missing PDF: {args.pdf}", file=sys.stderr)
        return 1

    pages = count_with_pypdf(args.pdf)
    if pages is None:
        pages = count_with_pdfinfo(args.pdf)
    if pages is None:
        print("Could not count pages. Install pypdf or Poppler pdfinfo.", file=sys.stderr)
        return 1

    if pages != args.expect:
        print(f"Expected {args.expect} page(s), found {pages}: {args.pdf}", file=sys.stderr)
        return 1

    print(f"ok - {args.pdf} has {pages} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
