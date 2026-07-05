#!/usr/bin/env bun

import { apiFetch, stripHtml, writeError } from "./helpers.js"

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

function render(items: any[], format: "json" | "table" | "plain", meta?: any, facets?: any): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify(meta ? { meta, facets, results: items } : items, null, 2) + "\n")
    return
  }
  if (format === "plain") {
    process.stdout.write(
      items
        .map((item) => `${item.title || item.preferredLabelDa || item}\n  ${item.hiringOrgName || item.occupation || item.conceptUriDa || ""}\n  ${item.jobAdId || item.conceptUriDa || ""}`)
        .join("\n\n") + "\n",
    )
    return
  }
  const header = `${"TITLE".padEnd(44)} ${"EMPLOYER/OCCUPATION".padEnd(30)} ${"DEADLINE/ID".padEnd(24)}`
  const lines = items.map((item) =>
    `${String(item.title || item.preferredLabelDa || item).slice(0, 44).padEnd(44)} ${String(item.hiringOrgName || item.occupation || "—").slice(0, 30).padEnd(30)} ${String(item.applicationDeadline || item.jobAdId || item.conceptUriDa || "—").slice(0, 24).padEnd(24)}`,
  )
  process.stdout.write([header, "-".repeat(header.length), ...lines].join("\n") + "\n")
}

async function runSearch(flags: Flags): Promise<number> {
  const params: Record<string, string> = {
    pageNumber: val(flags, "page") || "1",
    resultsPerPage: val(flags, "per-page") || "10",
    sortValue: val(flags, "order") || "PublicationDate",
  }
  const mapping: Record<string, string> = {
    "search-string": "searchString",
    region: "region",
    "postal-code": "postalCode",
    radius: "radius",
    "work-hours": "workHours",
    duration: "employmentDuration",
    "job-type": "jobType",
    "occupation-area": "occupationArea",
    "occupation-group": "occupationGroup",
  }
  for (const [flag, param] of Object.entries(mapping)) {
    const value = val(flags, flag)
    if (value) params[param] = value
  }
  const data = await apiFetch<any>("/FindJob/Search", params)
  const rows = applyLimit(data.results ?? data.jobAds ?? [], flags)
  const meta = data.meta ?? {
    totalJobAdCount: data.totalJobAdCount ?? data.total ?? null,
    pageNumber: Number(params.pageNumber),
    resultsPerPage: Number(params.resultsPerPage),
    searchString: params.searchString ?? "",
  }
  render(rows, fmt(flags), meta, data.facets)
  return 0
}

async function runDetail(flags: Flags): Promise<number> {
  const id = flags._[1]
  if (!id) {
    writeError("detail requires an <id>", "NO_ID")
    return 1
  }
  const data = await apiFetch<any>(`/FindJob/JobAdDetails/${id}`, { incrementViews: "false" })
  if (fmt(flags) === "plain") {
    process.stdout.write(`${data.title || "(untitled)"}\n${data.employer?.name || "—"}\n\n${stripHtml(data.body || "")}\n\nURL: ${data.application?.url || `https://jobnet.dk/job/${id}`}\n`)
  } else {
    process.stdout.write(JSON.stringify(data, null, 2) + "\n")
  }
  return 0
}

async function runOccupations(flags: Flags): Promise<number> {
  const searchString = val(flags, "search-string")
  if (!searchString) {
    writeError("--search-string is required", "MISSING_REQUIRED")
    return 1
  }
  const data = await apiFetch<any[]>("/OccupationSearch", {
    searchString,
    resultsPerPage: val(flags, "per-page") || "10",
  })
  render(Array.isArray(data) ? data : [], fmt(flags))
  return 0
}

async function runSuggestions(flags: Flags): Promise<number> {
  const query = val(flags, "query")
  if (!query) {
    writeError("--query is required", "MISSING_REQUIRED")
    return 1
  }
  const data = await apiFetch<any[]>("/FindJob/GetTypeaheadSuggestions", { query })
  render(applyLimit(Array.isArray(data) ? data : [], flags), fmt(flags))
  return 0
}

const HELP = `jobnet-cli

USAGE
  bun run src/cli.ts search [--search-string text] [--format json|table|plain]
  bun run src/cli.ts detail <jobAdId> [--format json|plain]
  bun run src/cli.ts occupations --search-string <text>
  bun run src/cli.ts suggestions --query <text>
`

async function main(): Promise<number> {
  const flags = parseFlags(process.argv.slice(2))
  const command = flags._[0]
  try {
    if (!command || flags.help || flags.h) {
      process.stdout.write(HELP)
      return command ? 0 : 1
    }
    if (command === "search") return runSearch(flags)
    if (command === "detail") return runDetail(flags)
    if (command === "occupations") return runOccupations(flags)
    if (command === "suggestions") return runSuggestions(flags)
    writeError(`Unknown command "${command}"`, "BAD_CMD")
    return 1
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }
}

main().then((code) => process.exit(code))
