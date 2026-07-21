#!/usr/bin/env python3
"""Compile a CV and cover letter through the real application PDF workflow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COVER_TEX = ROOT / "cover_letters" / "cover_smoke_test.tex"

COVER_TEMPLATE = r"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Smoke test cover letter
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\documentclass[]{cover}
\usepackage{fancyhdr}
\usepackage{setspace}

\setstretch{1.0}
\pagestyle{fancy}
\fancyhf{}
\rfoot{Page \thepage \hspace{0pt}}
\thispagestyle{empty}
\renewcommand{\headrulewidth}{0pt}

\begin{document}

\namesection{}{\Huge{Your Name}}{  \href{mailto:you@example.com}{you@example.com} |  \urlstyle{same}\href{https://github.com/your-handle}{GitHub}
}

\currentdate{\today}
\lettercontent{Dear hiring team,}

\lettercontent{I am writing to test the application pipeline for a sample machine learning engineer role. My background combines full-stack development, research work, and applied AI projects, and this generated letter is intentionally concise so the one-page layout can be verified.}

\lettercontent{This smoke document exercises the same cover-letter class, local fonts, page-count check, and compiler path used for real applications. It is not intended for submission.}

\lettercontent{In a real workflow, Codex will replace this placeholder text with claims grounded in the configured candidate profile and the selected job posting. The smoke test keeps that generation step separate while proving that the final PDF machinery is ready.}

\lettercontent{I look forward to hearing from you.}

\begin{flushright}
\closing{Kind regards,}
\signature{Your Name}
\end{flushright}

\end{document}
"""


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def tail(text: str, line_count: int = 120) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-line_count:])


def run_step(label: str, command: list[str]) -> int:
    print(f"== {label}")
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    combined = "\n".join(part for part in [result.stdout, result.stderr] if part)

    if result.returncode != 0:
        print(tail(combined).strip())
        return result.returncode

    ok_lines = [
        line
        for line in combined.splitlines()
        if line.startswith("ok - ") or line.startswith("Output written on ")
    ]
    for line in ok_lines[-4:]:
        print(line)
    print(f"ok - {label}")
    return 0


def cleanup_cover_artifacts() -> None:
    stem = COVER_TEX.with_suffix("")
    for suffix in [".tex", ".pdf", ".aux", ".log", ".out"]:
        path = stem.with_suffix(suffix)
        path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile the example CV and a generated cover letter smoke document."
    )
    parser.add_argument("--cv", default="cv/main_example.tex", help="CV .tex file to compile")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep generated smoke-test cover letter files for visual inspection",
    )
    args = parser.parse_args()

    cv_tex = ROOT / args.cv
    if not cv_tex.exists():
        print(f"Missing CV file: {relative(cv_tex)}", file=sys.stderr)
        return 1

    COVER_TEX.write_text(COVER_TEMPLATE, encoding="utf-8")

    steps = [
        ("CV PDF compile", ["bash", "scripts/compile_cv.sh", relative(cv_tex)]),
        ("cover letter PDF compile", ["bash", "scripts/compile_cover_letter.sh", relative(COVER_TEX)]),
    ]

    try:
        for label, command in steps:
            result = run_step(label, command)
            if result != 0:
                return result
    finally:
        if not args.keep:
            cleanup_cover_artifacts()

    print("ok - application PDF smoke test passed")
    if args.keep:
        print(f"kept - {relative(COVER_TEX)}")
        print(f"kept - {relative(COVER_TEX.with_suffix('.pdf'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
