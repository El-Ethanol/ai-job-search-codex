#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

if [[ $# -ne 1 ]]; then
  echo "Usage: scripts/compile_cv.sh cv/main_company.tex" >&2
  exit 2
fi

tex_file="$1"
if [[ ! -f "$tex_file" ]]; then
  echo "Missing file: $tex_file" >&2
  exit 1
fi

if ! command -v lualatex >/dev/null 2>&1; then
  echo "lualatex is not installed" >&2
  exit 1
fi

dir="$(dirname "$tex_file")"
base="$(basename "$tex_file")"
pdf_file="${tex_file%.tex}.pdf"

(cd "$dir" && lualatex -interaction=nonstopmode "$base")
python3 scripts/check_pdf_pages.py "$pdf_file" --expect 2
rm -f "${tex_file%.tex}.aux" "${tex_file%.tex}.log" "${tex_file%.tex}.out"
