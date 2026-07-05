#!/usr/bin/env bun

import { BASE_URL, apiFetch, apiPost, stripHtml, writeError } from "./helpers.js"

interface Flags {
  _: string[]
  [key: string]: string | boolean
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg.startsWith("--") || arg.startsWith("-")) {
      const key = arg.replace(/^-+/, "")
      const next = argv[i + 1]
      if (next === undefined || next.startsWith("-")) flags[key] = true
      else {
        flags[key] = next
        i++
      }
    } else flags._.push(arg)
  }
  return flags
}

function val(flags: Flags, key: string): string | undefined {
  const value = flags[key]
  return typeof value === "string" ? value : undefined
}

function fmt(flags: Flags): "json" | "table" | "plain" {
  const value = val(flags, "format")
  return value === "table" || value === "plain" ? value : "json"
}

function applyLimit<T>(items: T[], flags: Flags): T[] {
  const n = Number(val(flags, "limit"))
  return Number.isFinite(n) && n > 0 ? items.slice(0, n) : items
}

function normalizeUrl(url: string | undefined): string | null {
  if (!url) return null
  return url.startsWith("http") ? url : new URL(url, BASE_URL).toString()
}

function flattenSuggestionGroups(groups: any[]): any[] {
  return groups.flatMap((group) => (Array.isArray(group.items) ? group.items.map((item: any) => ({ group: group.title, ...item })) : []))
}

function render(items: any[], format: "json" | "table" | "plain", meta?: any): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify(meta ? { meta, results: items } : items, null, 2) + "\n")
    return
  }
  if (format === "plain") {
    process.stdout.write(
      items
        .map((item) => `${item.title || item.text || "(untitled)"}\n  ${item.companyName || item.company || item.category || "—"}\n  ${item.url || item.value || item.slug || ""}`)
        .join("\n\n") + "\n",
    )
    return
  }
  const header = `${"TITLE".padEnd(42)} ${"COMPANY/GROUP".padEnd(28)} ${"DEADLINE/VALUE".padEnd(20)}`
  const lines = items.map((item) =>
    `${String(item.title || item.text || "").slice(0, 42).padEnd(42)} ${String(item.companyName || item.group || item.category || "—").slice(0, 28).padEnd(28)} ${String(item.applicationDeadline || item.value || item.slug || "—").slice(0, 20).padEnd(20)}`,
  )
  process.stdout.write([header, "-".repeat(header.length), ...lines].join("\n") + "\n")
}

function filter(type: string, value: string | number | undefined, displayText?: string): any | null {
  if (value === undefined || value === "") return null
  return { type, value, displayText: displayText ?? String(value) }
}

async function runSearch(flags: Flags): Promise<number> {
  const filters = [
    filter("freetext", val(flags, "text")),
    filter("category", val(flags, "category") ? Number(val(flags, "category")) : undefined),
    filter("jobtitle", val(flags, "jobtitle-id") ? Number(val(flags, "jobtitle-id")) : undefined),
    filter("municipality", val(flags, "municipality")),
    filter("zip", val(flags, "zip")),
    filter("region", val(flags, "region")),
  ].filter(Boolean)
  const body = {
    jobTypes: val(flags, "job-type")?.split(",").map((s) => s.trim()).filter(Boolean) ?? [],
    filters,
    locationMode: "Text",
    distance: 50,
  }
  const page = Number(val(flags, "page") || "1")
  const data = await apiPost<any>(`/api/jobsearch/search/${page}`, body)
  const rawRows = data.results ?? data.jobs ?? data.items ?? data.jobAds ?? []
  const rows = applyLimit(
    rawRows.map((row: any) => ({
      ...row,
      url: normalizeUrl(row.url),
      slug: row.slug ?? String(row.url || "").split("/job/")[1] ?? null,
      companyLogo: row.companyLogo ? { ...row.companyLogo, url: normalizeUrl(row.companyLogo.url) } : row.companyLogo,
      coverImage: row.coverImage ? { ...row.coverImage, url: normalizeUrl(row.coverImage.url) } : row.coverImage,
    })),
    flags,
  )
  const meta = data.meta ?? {
    currentPage: data.currentPage ?? page,
    totalItems: data.totalItems ?? data.total ?? null,
    itemsPrPage: data.itemsPrPage ?? data.itemsPerPage ?? null,
    totalPages: data.totalPages ?? null,
  }
  render(rows, fmt(flags), meta)
  return 0
}

function parseJsonLd(html: string): any {
  const scripts = html.matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)
  for (const match of scripts) {
    try {
      const parsed = JSON.parse(match[1].trim())
      const list = Array.isArray(parsed) ? parsed : [parsed]
      const job = list.find((item) => item?.["@type"] === "JobPosting")
      if (job) return job
    } catch {
      continue
    }
  }
  throw new Error("Failed to parse JSON-LD from job page")
}

async function runDetail(flags: Flags): Promise<number> {
  const slug = flags._[1]
  if (!slug) {
    writeError("detail requires a <slug>", "NO_SLUG")
    return 1
  }
  const url = `${BASE_URL}/job/${slug}`
  const response = await fetch(url)
  if (response.status === 404) {
    writeError("Job not found", "NOT_FOUND")
    return 1
  }
  if (!response.ok) throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  const job = parseJsonLd(await response.text())
  const result = { slug, url, ...job }
  if (fmt(flags) === "plain") {
    process.stdout.write(`${job.title || "(untitled)"}\n${job.hiringOrganization?.name || "—"}\n\n${stripHtml(job.description || "")}\n\nURL: ${url}\n`)
  } else {
    process.stdout.write(JSON.stringify(result, null, 2) + "\n")
  }
  return 0
}

async function runCategories(flags: Flags): Promise<number> {
  const data = await apiFetch<any[]>("/api/categorycount/getcounts")
  render(applyLimit(data, flags), fmt(flags))
  return 0
}

async function runSuggestions(flags: Flags, path: string): Promise<number> {
  const query = val(flags, "query")
  if (!query) {
    writeError("--query is required", "MISSING_REQUIRED")
    return 1
  }
  const data = await apiFetch<any[]>(path, { q: query })
  const groups = Array.isArray(data) ? data : []
  const format = fmt(flags)
  const items = format === "json" ? groups : applyLimit(flattenSuggestionGroups(groups), flags)
  render(items, format)
  return 0
}

const HELP = `jobdanmark-cli

USAGE
  bun run src/cli.ts search [--text text] [--category id] [--format json|table|plain]
  bun run src/cli.ts detail <slug> [--format json|plain]
  bun run src/cli.ts categories [--format json|table|plain]
  bun run src/cli.ts autocomplete --query <text>
  bun run src/cli.ts locations --query <text>
`

async function main(): Promise<number> {
  const flags = parseFlags(process.argv.slice(2))
  const command = flags._[0]
  try {
    if (!command || flags.help || flags.h) {
      process.stdout.write(HELP)
      return flags.help || flags.h || command ? 0 : 1
    }
    if (command === "search") return runSearch(flags)
    if (command === "detail") return runDetail(flags)
    if (command === "categories") return runCategories(flags)
    if (command === "autocomplete") return runSuggestions(flags, "/api/search/autocomplete")
    if (command === "locations") return runSuggestions(flags, "/api/search/locations")
    writeError(`Unknown command "${command}"`, "BAD_CMD")
    return 1
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }
}

main().then((code) => process.exit(code))
