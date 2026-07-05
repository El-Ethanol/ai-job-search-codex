#!/usr/bin/env python3
"""Smoke tests for the Codex-native AI job-search workspace."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CODEX_SKILLS = [
    "job-application-assistant",
    "job-apply",
    "job-profile-reset",
    "job-scraper",
    "job-setup",
    "profile-expand",
    "upskill",
]

CLI_SKILLS = [
    "jobbank-search",
    "jobdanmark-search",
    "jobindex-search",
    "jobnet-search",
    "linkedin-search",
]


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.skips: list[str] = []

    def ok(self, message: str) -> None:
        print(f"ok - {message}")

    def fail(self, message: str) -> None:
        self.failures.append(message)
        print(f"FAIL - {message}")

    def skip(self, message: str) -> None:
        self.skips.append(message)
        print(f"skip - {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def has_frontmatter(text: str) -> bool:
    return bool(re.match(r"^---\n[\s\S]*?\n---\n", text))


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def check_codex_guidance(report: Report) -> None:
    agents = ROOT / "AGENTS.md"
    if not agents.exists():
        report.fail("AGENTS.md is missing")
        return
    text = read(agents)
    for expected in ["Codex", ".agents/skills", "PDF Verification", "Local State And Privacy"]:
        if expected not in text:
            report.fail(f"AGENTS.md missing expected section or phrase: {expected}")
            return
    report.ok("AGENTS.md has Codex workspace guidance")


def check_skills(report: Report) -> None:
    for name in CODEX_SKILLS:
        path = ROOT / ".agents" / "skills" / name / "SKILL.md"
        if not path.exists():
            report.fail(f"missing skill: {path.relative_to(ROOT)}")
            continue
        text = read(path)
        if not has_frontmatter(text):
            report.fail(f"skill has no YAML frontmatter: {path.relative_to(ROOT)}")
            continue
        if not frontmatter_value(text, "name"):
            report.fail(f"skill frontmatter missing name: {path.relative_to(ROOT)}")
            continue
        if "description:" not in text.split("---", 2)[1]:
            report.fail(f"skill frontmatter missing description: {path.relative_to(ROOT)}")
            continue
        report.ok(f"skill metadata present: {name}")


def check_no_claude_leftovers(report: Report) -> None:
    scan_roots = [ROOT / ".agents" / "skills" / name for name in CODEX_SKILLS]
    bad_patterns = [
        "allowed-tools:",
        "WebFetch",
        "WebSearch",
        "AskUserQuestion",
        "Agent tool",
        ".claude/skills",
    ]
    failures: list[str] = []
    for base in scan_roots:
        for path in base.rglob("*.md"):
            text = read(path)
            for pattern in bad_patterns:
                if pattern in text:
                    failures.append(f"{path.relative_to(ROOT)} contains {pattern}")
    if failures:
        for failure in failures:
            report.fail(failure)
    else:
        report.ok("Codex skills have no Claude-only metadata or paths")


def check_cli_imports(report: Report) -> None:
    missing: list[str] = []
    for skill in CLI_SKILLS:
        cli = ROOT / ".agents" / "skills" / skill / "cli" / "src" / "cli.ts"
        if not cli.exists():
            report.fail(f"missing CLI entrypoint: {cli.relative_to(ROOT)}")
            continue
        text = read(cli)
        for match in re.finditer(r'from\s+["\']\./commands/([^"\']+)["\']', text):
            imported = match.group(1)
            target = cli.parent / "commands" / imported
            ts_target = target.with_suffix(".ts") if target.suffix == ".js" else target
            if not target.exists() and not ts_target.exists():
                missing.append(f"{cli.relative_to(ROOT)} imports missing {target.relative_to(ROOT)}")
    if missing:
        for item in missing:
            report.fail(item)
    else:
        report.ok("CLI command imports resolve")


def check_package_json(report: Report) -> None:
    for skill in CLI_SKILLS:
        package_path = ROOT / ".agents" / "skills" / skill / "cli" / "package.json"
        if not package_path.exists():
            report.fail(f"missing package.json: {package_path.relative_to(ROOT)}")
            continue
        try:
            package = json.loads(read(package_path))
        except json.JSONDecodeError as exc:
            report.fail(f"invalid package.json {package_path.relative_to(ROOT)}: {exc}")
            continue
        if package.get("type") != "module":
            report.fail(f"package.json should set type=module: {package_path.relative_to(ROOT)}")
            continue
        if skill != "linkedin-search":
            deps = package.get("dependencies", {})
            stale = sorted(k for k in deps if k.startswith("@bunli"))
            if stale:
                report.fail(f"stale Bunli dependency in {package_path.relative_to(ROOT)}: {', '.join(stale)}")
                continue
        report.ok(f"package metadata ok: {skill}")


def check_python(report: Report) -> None:
    files = [
        ROOT / "salary_lookup.py",
        ROOT / "tools" / "convert_salary_excel.py",
        ROOT / "scripts" / "scrape_jobs.py",
        Path(__file__).resolve(),
    ]
    cmd = [sys.executable, "-m", "py_compile", *map(str, files)]
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if result.returncode == 0:
        report.ok("Python files compile")
    else:
        report.fail("Python compile failed: " + (result.stderr or result.stdout).strip())


def check_scraper_config(report: Report) -> None:
    path = ROOT / ".agents" / "skills" / "job-scraper" / "search-queries.md"
    if not path.exists():
        report.fail("job scraper search-queries.md is missing")
        return
    text = read(path)
    placeholders = ["[YOUR_", "YOUR_PRIMARY", "YOUR_KEY", "YOUR_CITY", "YOUR_COUNTRY"]
    stale = [placeholder for placeholder in placeholders if placeholder in text]
    if stale:
        report.fail("job scraper search queries still contain placeholders: " + ", ".join(stale))
        return
    if "visa sponsorship" not in text.lower() or "machine learning engineer" not in text.lower():
        report.fail("job scraper search queries are missing configured role/visa filters")
        return
    report.ok("job scraper search queries are configured")


def check_bun_help(report: Report) -> None:
    bun = shutil.which("bun")
    if not bun:
        report.skip("bun not installed, skipped CLI runtime help checks")
        return
    for skill in CLI_SKILLS:
        cli_dir = ROOT / ".agents" / "skills" / skill / "cli"
        result = subprocess.run(
            [bun, "run", "src/cli.ts", "--help"],
            cwd=cli_dir,
            text=True,
            capture_output=True,
            timeout=20,
        )
        if result.returncode == 0:
            report.ok(f"Bun CLI help runs: {skill}")
        else:
            report.fail(f"Bun CLI help failed for {skill}: {(result.stderr or result.stdout).strip()}")


def check_latex_tools(report: Report) -> None:
    missing = [tool for tool in ["lualatex", "xelatex"] if not shutil.which(tool)]
    if missing:
        report.skip("LaTeX not installed, skipped PDF compile smoke checks: " + ", ".join(missing))
    elif shutil.which("kpsewhich"):
        result = subprocess.run(["kpsewhich", "moderncv.cls"], text=True, capture_output=True)
        if result.returncode != 0:
            report.skip("LaTeX is installed, but moderncv.cls is missing. Install moderncv before compiling CVs.")
        else:
            report.ok("LaTeX tools and moderncv class available")
    else:
        report.skip("LaTeX tools available, but kpsewhich is missing so moderncv availability was not checked")


def main() -> int:
    report = Report()
    check_codex_guidance(report)
    check_skills(report)
    check_no_claude_leftovers(report)
    check_cli_imports(report)
    check_package_json(report)
    check_python(report)
    check_scraper_config(report)
    check_bun_help(report)
    check_latex_tools(report)

    print()
    if report.failures:
        print(f"Smoke test failed with {len(report.failures)} failure(s).")
        return 1
    print(f"Smoke test passed with {len(report.skips)} skip(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
