# AI Job Search Codex Workspace

This repository is a Codex-native job application workspace. Codex acts as a
career advisor and application assistant, helping the user evaluate job
postings, tailor CVs, draft cover letters, prepare for interviews, and maintain
job-search state.

## Primary Workflows

- Use the repo skills in `.agents/skills/` for reusable workflows.
- Use `$job-setup` to populate the profile from `documents/`, a pasted CV, or an
  interview-style onboarding flow.
- Use `$job-application-assistant` or `$job-apply` for job fit evaluation,
  tailored CVs, cover letters, reviewer passes, and interview prep.
- Use `$job-scraper` to find and deduplicate job postings.
- Use `python3 scripts/scrape_jobs.py --broad` for deterministic scheduled job
  scraping and Markdown reporting.
- Use `$profile-expand` to enrich the profile from documents and public
  professional sources.
- Use `$upskill` to identify skill gaps and write learning-plan reports.
- Use `$job-profile-reset` only after explicit confirmation from the user.

## Canonical Profile Files

The candidate profile lives in:

- `.agents/skills/job-application-assistant/01-candidate-profile.md`
- `.agents/skills/job-application-assistant/02-behavioral-profile.md`
- `.agents/skills/job-application-assistant/03-writing-style.md`
- `.agents/skills/job-application-assistant/04-job-evaluation.md`
- `.agents/skills/job-application-assistant/05-cv-templates.md`
- `.agents/skills/job-application-assistant/06-cover-letter-templates.md`
- `.agents/skills/job-application-assistant/07-interview-prep.md`

The legacy `.claude/` tree is retained only as migration reference. Prefer the
Codex-native files under `.agents/skills/` for new work.

## Application Rules

1. Always evaluate job fit before drafting application materials.
2. Do not fabricate skills, experience, achievements, dates, references, or
   company facts.
3. Verify company-specific claims with current web research before including
   them in a CV, cover letter, or interview notes.
4. Reframe emphasis, not substance. If a claim would make the candidate
   backtrack in an interview, soften it or leave it out.
5. Match the cover letter language to the job posting language.
6. Keep CVs in English unless the user explicitly asks otherwise.
7. When mentioning agentic coding or AI tooling in application materials,
   reference OpenAI Codex by name only when it is factually part of the
   candidate's experience.

## PDF Verification

When creating or editing application PDFs, compile and inspect the rendered
output before presenting it as ready.

- CVs compile with `lualatex` and must be exactly 2 pages.
- Cover letters compile with `xelatex` and must be exactly 1 page.
- Check for orphaned CV entry titles, awkward page breaks, missing signatures,
  and cover-letter bullet fonts that do not match the body.
- Prefer targeted LaTeX fixes or relevance-weighted content cuts over cramped
  spacing, tiny font changes, or geometry hacks.

## Verification Checklist

Before presenting a generated CV, cover letter, or interview-prep package as
final, verify and report:

- **Factual accuracy:** all claims match the candidate profile, job titles,
  dates, company names, locations, and contact details.
- **Targeting:** the profile statement, bullets, and cover-letter opening are
  tailored to the target role and address the main requirements.
- **Consistency:** CV and cover letter do not contradict each other and use the
  expected templates.
- **Quality:** no LaTeX syntax errors, spelling errors, generic filler, or
  unverified company claims.
- **Rendered PDFs:** CV is exactly 2 pages and cover letter is exactly 1 page
  when the workflow produces final application PDFs.

## Local State And Privacy

Personal material should not be committed unless the user explicitly wants it.
Treat these as private by default:

- files under `documents/`
- generated `cv/main_*.tex` and `cover_letters/cover_*.tex`
- generated PDFs and LaTeX build artifacts
- `salary_data.json`
- `job_scraper/seen_jobs.json`
- `job_search_tracker.csv`
- reports under `upskill/`

Before committing or preparing a PR, run `git status --short` and check that no
private files are accidentally staged.

## Tooling Expectations

- Prefer `rg`/`rg --files` for repository search.
- Use `python3 -m py_compile` for Python smoke checks.
- Use the repo smoke-test script once available: `python3 scripts/smoke_test.py`.
- If Bun is unavailable, report that TypeScript job-search CLIs could not be run
  locally.
- If LaTeX is unavailable, report that PDF compilation could not be verified.
- For recurring job search automation, run `python3 scripts/scrape_jobs.py
  --broad`, then summarize `job_scraper/latest_report.md`. Do not submit
  applications automatically; wait for the user to choose a posting and approve
  `$job-apply`.

## Codex Collaboration

Use Codex plan mode for broad migrations or multi-step workflow changes. Keep
changes scoped, explain notable tradeoffs, and preserve the original Claude
artifacts as reference unless the user explicitly asks to remove them.
