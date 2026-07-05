# Setup Guide

Step-by-step instructions for getting the AI Job Search framework running.

## 1. Prerequisites

### Codex

Install Codex from OpenAI. On macOS/Linux, the standalone installer is:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Then authenticate with your OpenAI or ChatGPT account. See the [Codex docs](https://developers.openai.com/codex) for the current setup options across CLI, IDE extension, and the Codex app.

### Python

Python 3.10+ is required for the salary lookup tool. Check with:

```bash
python --version
```

### Bun (for job search tools)

The job portal CLIs (four Danish portals plus the country-agnostic LinkedIn tool) are written in TypeScript and run with Bun:

```bash
curl -fsSL https://bun.sh/install | bash
```

### LaTeX (for compiling CVs and cover letters)

Install a LaTeX distribution to compile the generated `.tex` files to PDF:

- **Windows:** [MiKTeX](https://miktex.org/download)
- **macOS:** [MacTeX](https://tug.org/mactex/)
- **Linux:** `sudo apt install texlive-full` or `sudo dnf install texlive-scheme-full`

The CV compiles with `lualatex` (pdflatex often fails on modern MiKTeX installs with `fontawesome5` font-expansion errors). The cover letter compiles with `xelatex` because `cover.cls` requires `fontspec` for its custom Lato/Raleway fonts.

## 2. Fork and clone

```bash
gh repo fork MadsLorentzen/ai-job-search --clone
cd ai-job-search
```

Or manually: fork on GitHub, then clone your fork.

## 3. Install job search CLI dependencies

```bash
for tool in jobbank-search jobdanmark-search jobindex-search jobnet-search linkedin-search; do
  cd .agents/skills/$tool/cli && bun install && cd ../../../..
done
```

The CLIs have no runtime npm dependencies and run with plain `bun`. `bun install` is still useful if you want local TypeScript dev types or package-lock metadata.

## 4. Run the setup interview

Start Codex in the repository:

```bash
codex
```

Then run the onboarding:

```
$job-setup
```

Codex will offer three paths:

- **Path A:** Read documents from `documents/` if you have populated it.
- **Path B:** Import a single CV that you paste or mention.
- **Path C:** Answer structured interview questions section by section.

Both paths produce the same result: fully populated profile files.

### What gets populated

| File | Content |
|------|---------|
| `01-candidate-profile.md` | Structured education, experience, skills |
| `02-behavioral-profile.md` | Behavioral assessment |
| `04-job-evaluation.md` | Personalized skill match areas and career goals |
| `05-cv-templates.md` | Profile statement templates for your background |
| `07-interview-prep.md` | STAR examples from your experience |
| `cv/main_example.tex` | Your LaTeX CV with actual details |
| `search-queries.md` | Job search queries for `$job-scraper` |

### Re-running setup

You can update specific sections later:

```
$job-setup --section skills
$job-setup --section experience
$job-setup --section search
```

The `--section search` option is especially useful as your priorities evolve. It re-runs the search configuration interview and suggests role types you may not have considered based on your full profile.

## 5. Optional: Set up salary benchmarking

If you have salary data (from a union, salary survey, Glassdoor, or personal research):

1. **Option A:** Create `salary_data.json` manually in the repo root (see `tools/README_SALARY_TOOL.md` for the format)
2. **Option B:** Convert from Excel:
   ```bash
   pip install openpyxl
   python tools/convert_salary_excel.py path/to/salary-data.xlsx --source "My Salary Data 2025"
   ```

This creates `salary_data.json` which the `$job-apply` workflow uses for salary benchmarking. If you skip this step, salary lookup is simply omitted.

## 6. Test the workflow

First run the repository smoke test:

```bash
python3 scripts/smoke_test.py
```

This verifies the Codex skill layout, CLI import wiring, package metadata, and Python helpers. If Bun is not installed, CLI runtime checks are skipped and reported clearly.

Find a job posting you're interested in, then:

```
$job-apply https://jobindex.dk/job/1234567
```

Or paste the job description directly:

```
$job-apply [paste job posting text here]
```

Codex will:
1. Evaluate the fit against your profile
2. Ask if you want to proceed
3. Draft a tailored CV and cover letter
4. Run a reviewer pass that critiques the drafts
5. Revise and present the final output

## 7. Compile your documents

After `$job-apply` creates the LaTeX files:

```bash
# Compile CV
scripts/compile_cv.sh cv/main_<company>.tex

# Compile cover letter
scripts/compile_cover_letter.sh cover_letters/cover_<company>_<role>.tex
```

## Troubleshooting

### "salary_data.json not found"
This is expected if you haven't set up salary benchmarking. The `$job-apply` workflow skips this step automatically.

### Job search CLI tools not working
Make sure Bun is installed and you ran `bun install` in each CLI directory. The tools require network access to fetch job listings.

### LaTeX compilation errors
- CV: uses `lualatex` (pdflatex often fails on modern MiKTeX with `fontawesome5` font-expansion errors; lualatex handles the same sources cleanly)
- Cover letter: uses `xelatex` (for custom fonts in `OpenFonts/fonts/`)
- Make sure your LaTeX distribution includes the `moderncv` package

### Fonts not found in cover letter
The cover letter template expects fonts in `cover_letters/OpenFonts/fonts/`. Make sure this directory exists and contains the Lato and Raleway font files.

### Legacy `.claude/` files

This repo keeps the original `.claude/` tree as migration reference. Codex uses `AGENTS.md` and `.agents/skills/` for the active workflow. Prefer editing the Codex-native files unless you are intentionally comparing against the legacy source.
