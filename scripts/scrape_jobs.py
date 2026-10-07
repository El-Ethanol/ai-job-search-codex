#!/usr/bin/env python3
"""Deterministic job scraper for the Codex job-search workspace.

The script reads `.agents/skills/job-scraper/search-queries.md`, queries
supported public job sources, deduplicates against `job_scraper/seen_jobs.json`
and `job_search_tracker.csv`, then writes a Markdown report of new matches.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH_QUERIES = ROOT / ".agents" / "skills" / "job-scraper" / "search-queries.md"
# Personal queries live in a gitignored file so the tracked template stays generic.
LOCAL_SEARCH_QUERIES = ROOT / "job_scraper" / "search-queries.local.md"
SEEN_JOBS = ROOT / "job_scraper" / "seen_jobs.json"
TRACKER = ROOT / "job_search_tracker.csv"
DEFAULT_REPORT = ROOT / "job_scraper" / "latest_report.md"

TODAY = dt.date.today().isoformat()
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)


@dataclass(frozen=True)
class Query:
    source: str
    priority: int
    text: str
    location: str | None = None


@dataclass
class Job:
    key: str
    source: str
    query: str
    title: str
    company: str
    location: str | None
    posting_date: str | None
    deadline: str | None
    url: str
    description: str
    fit: str
    fit_reason: str
    seniority_risk: str
    visa_risk: str
    danish_risk: str
    status: str = "new"

    def to_seen_record(self, first_seen: str | None = None) -> dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "source": self.source,
            "location": self.location,
            "posting_date": self.posting_date,
            "deadline": self.deadline,
            "first_seen": first_seen or TODAY,
            "fit": self.fit,
            "seniority_risk": self.seniority_risk,
            "status": self.status,
        }


def fetch_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def strip_tags(text: str) -> str:
    text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|li|ul|ol|div|h\d)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(html.unescape(text))
    return re.sub(r"\s+", " ", text).strip()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_queries(path: Path, *, broad: bool) -> list[Query]:
    text = path.read_text(encoding="utf-8")
    queries: list[Query] = []
    priority = 99
    in_code = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading = re.match(r"^###\s+Priority\s+(\d+):", line)
        if heading:
            priority = int(heading.group(1))
            continue
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code or not line or line.startswith("#"):
            continue
        if not broad and priority > 3:
            continue
        if line.startswith("site:jobindex.dk"):
            query = normalize_space(line.replace("site:jobindex.dk", "", 1))
            queries.append(Query(source="jobindex", priority=priority, text=query))
        elif line.startswith("site:linkedin.com/jobs"):
            query = normalize_space(line.replace("site:linkedin.com/jobs", "", 1))
            location = "Denmark"
            if "Aalborg" in query:
                location = "Aalborg, Denmark"
                query = normalize_space(query.replace("Aalborg", ""))
            query = normalize_space(re.sub(r"\bDenmark\b", "", query, flags=re.IGNORECASE))
            queries.append(Query(source="linkedin", priority=priority, text=query, location=location))

    # Preserve order while removing exact duplicates.
    deduped: list[Query] = []
    seen: set[tuple[str, str, str | None]] = set()
    for query in queries:
        key = (query.source, query.text.lower(), query.location)
        if key not in seen:
            seen.add(key)
            deduped.append(query)
    return deduped


def load_seen(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"seen": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"seen": {}}
    if not isinstance(data, dict):
        return {"seen": {}}
    seen = data.setdefault("seen", {})
    if not isinstance(seen, dict):
        data["seen"] = {}
    return data


def load_tracker_keys(path: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    if not path.exists():
        return keys
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            company = (row.get("company") or "").strip().lower()
            role = (row.get("role") or "").strip().lower()
            if company or role:
                keys.add((company, role))
    return keys


def visa_risk(text: str) -> str:
    lower = text.lower()
    positive = [
        "visa sponsorship",
        "sponsor visa",
        "work permit support",
        "relocation package",
        "relocation support",
    ]
    negative = [
        "must be eligible to work",
        "valid work permit",
        "already authorized",
        "right to work",
    ]
    if any(term in lower for term in positive):
        return "Positive signal: mentions visa/work-permit or relocation support."
    if any(term in lower for term in negative):
        return "Visa risk: may require existing work authorization."
    return "Visa risk unknown: sponsorship/work authorization not stated."


def danish_risk(title: str, text: str) -> str:
    lower = f"{title} {text}".lower()
    high_patterns = [
        "fluent danish",
        "native danish",
        "professional danish",
        "speak and write danish",
        "danish language",
        "flydende dansk",
        "dansk i skrift og tale",
        "taler og skriver dansk",
        "kommunikerer p\u00e5 dansk",
    ]
    danish_posting_markers = [
        "ansogn",
        "ansogning",
        "arbejdsopgaver",
        "kvalifikationer",
        "vi soger",
        "du bliver",
        "du skal",
        "du har",
    ]
    english_markers = [
        "we are looking",
        "responsibilities",
        "requirements",
        "you will",
        "about the role",
        "english",
    ]
    if any(term in lower for term in high_patterns):
        return "High Danish risk: likely requires stronger Danish than intermediate."
    if sum(term in lower for term in danish_posting_markers) >= 3 and not any(
        term in lower for term in english_markers
    ):
        return "Danish risk: posting appears Danish-first; confirm language expectations."
    return "Low/unknown Danish risk."


def seniority_risk(title: str, text: str) -> str:
    title_lower = title.lower()
    lower = f"{title} {text}".lower()

    junior_terms = [
        "junior",
        "graduate",
        "entry level",
        "entry-level",
        "associate",
        "early career",
        "newly graduated",
        "nyuddannet",
    ]
    if any(term in title_lower for term in junior_terms):
        return "Low/unknown seniority risk."

    title_patterns = [
        r"\bsr\.?\b",
        r"\bsenior\b",
        r"\bstaff\b",
        r"\bprincipal\b",
        r"\blead\b",
        r"\bhead\b",
        r"\bdirector\b",
        r"\bmanager\b",
        r"\barchitect\b",
        r"\berfaren\b",
        r"\bchef\b",
        r"\barkitekt\b",
    ]
    title_hits = [pattern for pattern in title_patterns if re.search(pattern, title_lower)]
    if title_hits:
        return "High seniority risk: title indicates senior/lead/manager-level scope."

    year_patterns = [
        r"\b(?:at least|minimum|min\.?|over|more than)\s+([6-9]|1[0-9])\+?\s*(?:years|yrs)\b",
        r"\b([6-9]|1[0-9])\+?\s*(?:years|yrs)\s+(?:of\s+)?(?:relevant\s+|professional\s+|industry\s+)?experience\b",
        r"\b([6-9]|1[0-9])\+?\s*(?:years|yrs)\s+of(?:\s+[a-z0-9+#./-]+){0,8}\s+experience\b",
        r"\b([6-9]|1[0-9])\+?\s*(?:års|år)\s+(?:relevant\s+|professionel\s+)?(?:erfaring|erhvervserfaring)\b",
        r"\bmany years of (?:relevant\s+|professional\s+|industry\s+)?experience\b",
    ]
    if any(re.search(pattern, lower) for pattern in year_patterns):
        return "High seniority risk: posting appears to require 6+ years or equivalent senior experience."

    return "Low/unknown seniority risk."


def classify_fit(title: str, description: str, company: str, location: str | None) -> tuple[str, str]:
    lower = f"{title} {description} {company} {location or ''}".lower()
    title_lower = title.lower()

    if any(term in lower for term in ["student", "student assistant", "internship", "praktik"]):
        return "low", "Low: student/internship signal."

    senior = seniority_risk(title, description).startswith("High seniority risk")
    if senior:
        return "low", "Low: likely senior/stretch role; hidden by default unless stretch roles are explicitly requested."

    direct_ml_title = any(
        term in title_lower
        for term in ["machine learning", "ai engineer", "ai developer", "data scientist", "applied ai"]
    )
    direct_structural_title = any(
        term in title_lower
        for term in ["structural engineer", "civil structures", "materials & structural"]
    )
    direct_software_title = any(
        term in title_lower
        for term in ["software engineer", "software developer", "full stack", "full-stack"]
    )

    strong_body_terms = [
        "machine learning",
        "applied ai",
        "computer vision",
        "pytorch",
        "scikit",
        "python",
        "data science",
        "scientific computing",
        "finite element",
        "timber",
        "structural engineering",
    ]
    adjacent_terms = [
        "automation engineer",
        "technical consultant",
        "solutions engineer",
        "backend",
        "typescript",
        "django",
        "node.js",
        "nodejs",
        "developer",
    ]

    if direct_ml_title:
        return "high", "High: direct AI/ML target match."
    if direct_structural_title:
        return "high", "High: direct structural engineering target match."
    if direct_software_title and any(term in lower for term in strong_body_terms):
        return "high", "High: software role with strong engineering/data overlap."
    if any(term in lower for term in strong_body_terms):
        return "high", "High: directly overlaps configured technical strengths."
    if direct_software_title or any(term in lower for term in adjacent_terms):
        return "medium", "Medium: adjacent software/consulting fit; check domain depth."
    return "low", "Low: weak overlap with configured targets."


def parse_jobindex(query: Query, *, max_rows: int) -> tuple[list[Job], str | None]:
    url = "https://www.jobindex.dk/jobsoegning?" + urllib.parse.urlencode(
        {"q": query.text, "jobage": "14", "sort": "date"}
    )
    try:
        page = fetch_text(url)
    except (urllib.error.URLError, TimeoutError) as exc:
        return [], f"Jobindex {query.text}: {exc}"

    match = re.search(r"var Stash = (\{.*?\});\s*//\]\]>", page, re.DOTALL)
    if not match:
        return [], f"Jobindex {query.text}: no embedded search data"

    try:
        data = json.loads(match.group(1))
        # Jobindex renamed "jobsearch/result_app" to "jobsearch/result_app/list" (seen 2026-10); accept both.
        app_key = next((key for key in data if key.startswith("jobsearch/result_app")), None)
        if app_key is None:
            return [], f"Jobindex {query.text}: parse failed: no jobsearch/result_app* key"
        rows = data[app_key]["storeData"]["searchResponse"].get("results", [])[:max_rows]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        return [], f"Jobindex {query.text}: parse failed: {exc}"

    jobs: list[Job] = []
    for row in rows:
        title = str(row.get("headline") or "").strip()
        company = str(
            row.get("companytext")
            or (row.get("company") or {}).get("name")
            or (row.get("workplace_company") or {}).get("name")
            or ""
        ).strip()
        location = str(row.get("area") or "").strip() or None
        description = strip_tags(str(row.get("html") or ""))
        job_url = str(row.get("share_url") or row.get("apply_url") or row.get("url") or "")
        fit, fit_reason = classify_fit(title, description, company, location)
        role_seniority_risk = seniority_risk(title, description)
        key = f"jobindex:{row.get('tid') or job_url}"
        jobs.append(
            Job(
                key=key,
                source="Jobindex",
                query=query.text,
                title=title,
                company=company,
                location=location,
                posting_date=row.get("firstdate"),
                deadline=row.get("lastdate") or row.get("apply_deadline"),
                url=job_url,
                description=description,
                fit=fit,
                fit_reason=fit_reason,
                seniority_risk=role_seniority_risk,
                visa_risk=visa_risk(description),
                danish_risk=danish_risk(title, description),
            )
        )
    return jobs, None


def parse_linkedin(query: Query, *, max_rows: int, detail_delay: float) -> tuple[list[Job], str | None]:
    location = query.location or "Denmark"
    params = {
        "keywords": query.text,
        "location": location,
        "f_TPR": "r1209600",
        "start": "0",
    }
    url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
        + urllib.parse.urlencode(params)
    )
    try:
        page = fetch_text(
            url,
            headers={"Accept-Language": "en-US,en;q=0.9", "X-Requested-With": "XMLHttpRequest"},
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        return [], f"LinkedIn {query.text}: {exc}"

    chunks = re.split(r'data-entity-urn="urn:li:jobPosting:', page)[1:]
    jobs: list[Job] = []
    for chunk in chunks[:max_rows]:
        id_match = re.match(r"(\d+)", chunk)
        if not id_match:
            continue
        job_id = id_match.group(1)
        title_match = re.search(
            r'class="base-search-card__title"[^>]*>(.*?)</h3>', chunk, re.DOTALL
        )
        company_match = re.search(
            r'class="base-search-card__subtitle"[^>]*>(.*?)</h4>', chunk, re.DOTALL
        )
        location_match = re.search(
            r'class="job-search-card__location"[^>]*>(.*?)</span>', chunk, re.DOTALL
        )
        date_match = re.search(
            r'class="job-search-card__listdate[^"]*"[^>]*datetime="([^"]+)"',
            chunk,
            re.DOTALL,
        )
        link_match = re.search(
            r'class="base-card__full-link[^"]*"[^>]*href="([^"]+)"', chunk, re.DOTALL
        )
        title = strip_tags(title_match.group(1)) if title_match else ""
        company = strip_tags(company_match.group(1)) if company_match else ""
        job_location = strip_tags(location_match.group(1)) if location_match else None
        job_url = (
            html.unescape(link_match.group(1)).split("?")[0]
            if link_match
            else f"https://www.linkedin.com/jobs/view/{job_id}"
        )

        description = ""
        try:
            detail = fetch_text(
                f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}",
                headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=20,
            )
            desc_match = re.search(
                r'class="(?:show-more-less-html__markup|description__text[^"]*)"[^>]*>(.*?)</div>',
                detail,
                re.DOTALL,
            )
            description = strip_tags(desc_match.group(1)) if desc_match else ""
            time.sleep(detail_delay)
        except (urllib.error.URLError, TimeoutError):
            description = ""

        fit, fit_reason = classify_fit(title, description, company, job_location)
        role_seniority_risk = seniority_risk(title, description)
        jobs.append(
            Job(
                key=f"linkedin:{job_id}",
                source="LinkedIn",
                query=query.text,
                title=title,
                company=company,
                location=job_location,
                posting_date=date_match.group(1) if date_match else None,
                deadline=None,
                url=job_url,
                description=description,
                fit=fit,
                fit_reason=fit_reason,
                seniority_risk=role_seniority_risk,
                visa_risk=visa_risk(description),
                danish_risk=danish_risk(title, description),
            )
        )
    return jobs, None


def dedupe_jobs(jobs: list[Job]) -> list[Job]:
    unique: list[Job] = []
    keys: set[str] = set()
    company_titles: set[tuple[str, str]] = set()
    normalized_titles: set[tuple[str, str]] = set()
    for job in jobs:
        key = job.key or job.url
        company_title = (job.company.strip().lower(), job.title.strip().lower())
        normalized_company = re.sub(r"\b(a/s|aps|gmbh|group|cloud platforms & security)\b", "", job.company.lower())
        normalized_company = re.sub(r"[^a-z0-9]+", " ", normalized_company).strip()
        normalized_title = re.sub(r"&amp;", "&", job.title.lower())
        normalized_title = re.sub(r"[^a-z0-9]+", " ", normalized_title).strip()
        title_key = (normalized_company, normalized_title)
        if key in keys:
            continue
        if company_title[0] and company_title[1] and company_title in company_titles:
            continue
        if title_key[0] and title_key[1] and title_key in normalized_titles:
            continue
        keys.add(key)
        company_titles.add(company_title)
        normalized_titles.add(title_key)
        unique.append(job)
    return unique


def loc_score(job: Job) -> int:
    location = (job.location or "").lower()
    if "aalborg" in location:
        return 0
    north = ["north jutland", "nordjylland", "bronderslev", "hjorring", "frederikshavn", "hobro"]
    if any(term in location for term in north):
        return 1
    if "aarhus" in location or "arhus" in location:
        return 2
    if "denmark" in location or "danmark" in location:
        return 3
    return 4


def sort_jobs(jobs: list[Job]) -> list[Job]:
    return sorted(
        jobs,
        key=lambda job: (
            0 if job.fit == "high" else 1 if job.fit == "medium" else 2,
            loc_score(job),
            job.posting_date or "9999-99-99",
            job.company.lower(),
            job.title.lower(),
        ),
    )


def markdown_escape(text: str | None) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def render_report(
    *,
    jobs: list[Job],
    fetched_count: int,
    new_count: int,
    low_count: int,
    errors: list[str],
    include_low: bool,
) -> str:
    presented = [job for job in sort_jobs(jobs) if include_low or job.fit in {"high", "medium"}]
    high = sum(1 for job in presented if job.fit == "high")
    medium = sum(1 for job in presented if job.fit == "medium")
    low = sum(1 for job in presented if job.fit == "low")

    lines = [
        f"# New Job Matches - {TODAY}",
        "",
        f"Fetched {fetched_count} unique postings. Found {new_count} new postings.",
        f"Showing {len(presented)} matches ({high} high, {medium} medium, {low} low).",
        f"Hidden low/stretch matches: {low_count if not include_low else 0}.",
        "",
        "Visa note: unless a row says otherwise, sponsorship/work authorization was not stated.",
        "",
    ]
    if errors:
        lines.extend(["## Source Warnings", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")

    if not presented:
        lines.append("No new high/medium matches found.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "| # | Fit | Title | Company | Location | Date | Deadline | Risks |",
            "|---|-----|-------|---------|----------|------|----------|-------|",
        ]
    )
    for idx, job in enumerate(presented, 1):
        risks = "; ".join(
            part
            for part in [job.seniority_risk, job.visa_risk, job.danish_risk]
            if part
            and "Low/unknown seniority risk" not in part
            and "Low/unknown Danish risk" not in part
        )
        if not risks:
            risks = "visa unknown"
        title = f"[{markdown_escape(job.title)}]({job.url})"
        lines.append(
            "| {idx} | {fit} | {title} | {company} | {location} | {date} | {deadline} | {risks} |".format(
                idx=idx,
                fit=job.fit.title(),
                title=title,
                company=markdown_escape(job.company),
                location=markdown_escape(job.location or "unknown"),
                date=markdown_escape(job.posting_date or "unknown"),
                deadline=markdown_escape(job.deadline or "-"),
                risks=markdown_escape(risks),
            )
        )

    highlights = [job for job in presented if job.fit == "high"][:5]
    if highlights:
        lines.extend(["", "## High-Match Highlights", ""])
        for job in highlights:
            lines.extend(
                [
                    f"### {job.title} - {job.company}",
                    f"- {job.fit_reason}",
                    f"- Query/source: {job.query} via {job.source}.",
                    f"- Risk check: {job.seniority_risk} {job.visa_risk} {job.danish_risk}",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def write_seen(
    seen_data: dict[str, Any],
    seen_before: set[str],
    tracker_keys: set[tuple[str, str]],
    jobs: list[Job],
) -> list[Job]:
    seen = seen_data.setdefault("seen", {})
    new_jobs: list[Job] = []
    for job in jobs:
        tracker_key = (job.company.strip().lower(), job.title.strip().lower())
        previous = seen.get(job.key)
        if job.key in seen_before or tracker_key in tracker_keys:
            job.status = previous.get("status", "seen") if isinstance(previous, dict) else "seen"
        else:
            job.status = "new"
            new_jobs.append(job)
        first_seen = previous.get("first_seen") if isinstance(previous, dict) else None
        seen[job.key] = job.to_seen_record(first_seen=first_seen)
    return new_jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape configured job sources and report new matches.")
    parser.add_argument("--broad", action="store_true", help="Run all configured priority categories.")
    parser.add_argument("--include-low", action="store_true", help="Include low-fit matches in report.")
    parser.add_argument("--no-write", action="store_true", help="Do not update seen_jobs.json or report file.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Markdown report output path.")
    parser.add_argument("--json-output", type=Path, help="Optional JSON output of presented matches.")
    parser.add_argument("--max-per-query", type=int, default=12, help="Max Jobindex rows per query.")
    parser.add_argument("--max-linkedin-per-query", type=int, default=5, help="Max LinkedIn rows per query.")
    parser.add_argument("--source", choices=["all", "jobindex", "linkedin"], default="all")
    parser.add_argument("--detail-delay", type=float, default=0.2, help="Delay between LinkedIn detail fetches.")
    parser.add_argument(
        "--queries",
        type=Path,
        help="Search-queries file. Default: job_scraper/search-queries.local.md if present, else the template.",
    )
    args = parser.parse_args(argv)

    seen_data = load_seen(SEEN_JOBS)
    seen_before = set(seen_data.get("seen", {}).keys())
    tracker_keys = load_tracker_keys(TRACKER)
    queries_path = args.queries or (LOCAL_SEARCH_QUERIES if LOCAL_SEARCH_QUERIES.exists() else SEARCH_QUERIES)
    queries = parse_queries(queries_path, broad=args.broad)
    placeholder_queries = [query.text for query in queries if "[" in query.text]
    if placeholder_queries:
        print(
            f"Warning: {len(placeholder_queries)} queries in {queries_path} still contain template placeholders. "
            "Copy the template to job_scraper/search-queries.local.md and fill it in.",
            file=sys.stderr,
        )
    if args.source != "all":
        queries = [query for query in queries if query.source == args.source]

    all_jobs: list[Job] = []
    errors: list[str] = []
    for query in queries:
        if query.source == "jobindex":
            jobs, error = parse_jobindex(query, max_rows=args.max_per_query)
        elif query.source == "linkedin":
            jobs, error = parse_linkedin(
                query, max_rows=args.max_linkedin_per_query, detail_delay=args.detail_delay
            )
        else:
            jobs, error = [], f"Unsupported source: {query.source}"
        all_jobs.extend(jobs)
        if error:
            errors.append(error)
        time.sleep(0.25)

    unique_jobs = dedupe_jobs(all_jobs)
    new_jobs = write_seen(seen_data, seen_before, tracker_keys, unique_jobs)
    low_count = sum(1 for job in new_jobs if job.fit == "low")
    report = render_report(
        jobs=new_jobs,
        fetched_count=len(unique_jobs),
        new_count=len(new_jobs),
        low_count=low_count,
        errors=errors,
        include_low=args.include_low,
    )

    if not args.no_write:
        SEEN_JOBS.parent.mkdir(parents=True, exist_ok=True)
        SEEN_JOBS.write_text(json.dumps(seen_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
        if args.json_output:
            presented = [
                job.__dict__
                for job in sort_jobs(new_jobs)
                if args.include_low or job.fit in {"high", "medium"}
            ]
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(presented, indent=2, ensure_ascii=False) + "\n")

    print(report)
    if errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
