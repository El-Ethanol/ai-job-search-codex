#!/usr/bin/env bun

import {
  BASE_URL,
  extractJobIdFromUrl,
  fetchWithUA,
  parseRssDescription,
  rssFetch,
  writeError,
} from "./helpers.js"

interface Flags {
  _: string[]
  [key: string]: string | string[] | boolean
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = {}
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg.startsWith("--") || arg.startsWith("-")) {
      const key = alias[arg.replace(/^-+/, "")] ?? arg.replace(/^-+/, "")
      const next = argv[i + 1]
      if (next === undefined || next.startsWith("-")) {
        flags[key] = true
      } else {
        const existing = flags[key]
        if (Array.isArray(existing)) existing.push(next)
        else if (typeof existing === "string") flags[key] = [existing, next]
        else flags[key] = next
        i++
      }
    } else {
      flags._.push(arg)
    }
  }
  return flags
}

function one(flags: Flags, key: string): string | undefined {
  const value = flags[key]
  return Array.isArray(value) ? value[value.length - 1] : typeof value === "string" ? value : undefined
}

function many(flags: Flags, key: string): string[] {
  const value = flags[key]
  if (Array.isArray(value)) return value
  if (typeof value === "string") return [value]
  return []
}

function fmt(flags: Flags): "json" | "table" | "plain" {
  const value = one(flags, "format")
  return value === "table" || value === "plain" ? value : "json"
}

function limit<T>(items: T[], flags: Flags): T[] {
  const n = Number(one(flags, "limit"))
  return Number.isFinite(n) && n > 0 ? items.slice(0, n) : items
}

function stripHtml(html: string): string {
  return html
    .replace(/<\s*br\s*\/?>/gi, "\n")
    .replace(/<\/(p|li|div|h\d)>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim()
}

function renderRows(rows: any[], format: "json" | "table" | "plain", meta?: any): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify(meta ? { meta, results: rows } : rows, null, 2) + "\n")
    return
  }
  if (format === "plain") {
    process.stdout.write(
      rows
        .map((r) => `${r.title || "(untitled)"}\n  ${r.company || "—"} · ${r.location || "—"}\n  id: ${r.id || "—"}\n  ${r.url || ""}`)
        .join("\n\n") + "\n",
    )
    return
  }
  const header = `${"ID".padEnd(10)} ${"TITLE".padEnd(42)} ${"COMPANY".padEnd(24)} ${"LOCATION".padEnd(22)} DEADLINE`
  const lines = rows.map((r) =>
    `${String(r.id || "").padEnd(10)} ${String(r.title || "").slice(0, 42).padEnd(42)} ${String(r.company || "—").slice(0, 24).padEnd(24)} ${String(r.location || "—").slice(0, 22).padEnd(22)} ${r.deadline || "—"}`,
  )
  process.stdout.write([header, "-".repeat(header.length), ...lines].join("\n") + "\n")
}

async function runSearch(flags: Flags): Promise<number> {
  const params: Record<string, string | string[]> = {}
  const map: Record<string, string> = {
    key: "key",
    exclude: "antikey",
    type: "cvtype",
    education: "udd",
    location: "amt",
    "work-area": "erf",
    industry: "branche",
    "suitable-for": "andet",
    company: "virk",
    remote: "fjernarbejde",
    since: "oprettet",
  }
  for (const [flag, param] of Object.entries(map)) {
    const values = many(flags, flag)
    if (values.length === 1) params[param] = values[0]
    else if (values.length > 1) params[param] = values
  }
  if (Object.keys(params).length === 0) {
    writeError("--key or at least one filter is required", "MISSING_REQUIRED")
    return 1
  }

  const items = await rssFetch(params)
  const rows = limit(
    items.map((item) => {
      const parsed = parseRssDescription(item.description)
      const id = extractJobIdFromUrl(item.link)
      return {
        id,
        title: item.title,
        company: parsed.company,
        location: parsed.location,
        jobType: parsed.jobType,
        description: item.description,
        url: item.link,
        posted: item.pubDate ? new Date(item.pubDate).toISOString() : null,
        deadline: parsed.deadline,
      }
    }),
    flags,
  )
  renderRows(rows, fmt(flags), { total: null, count: rows.length })
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
  throw new Error("No JSON-LD JobPosting found on job page")
}

async function runDetail(flags: Flags): Promise<number> {
  const id = flags._[1]
  if (!id) {
    writeError("detail requires an <id>", "NO_ID")
    return 1
  }
  const response = await fetchWithUA(`${BASE_URL}/job/${id}/`)
  if (response.status === 404) {
    writeError("Job not found", "NOT_FOUND")
    return 1
  }
  if (!response.ok) throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  const job = parseJsonLd(await response.text())
  const address = Array.isArray(job.jobLocation) ? job.jobLocation[0]?.address : job.jobLocation?.address
  const result = {
    id: job.identifier?.value ?? id,
    url: job.url ?? `${BASE_URL}/job/${id}/`,
    title: job.title ?? "(untitled)",
    description: job.description ?? null,
    datePosted: job.datePosted ?? null,
    deadline: job.validThrough ?? null,
    employmentType: Array.isArray(job.employmentType) ? job.employmentType : job.employmentType ? [job.employmentType] : [],
    company: {
      name: job.hiringOrganization?.name ?? null,
      logo: job.hiringOrganization?.logo ?? null,
    },
    location: {
      streetAddress: address?.streetAddress ?? "",
      city: address?.addressLocality ?? "",
      postalCode: address?.postalCode ?? "",
      country: address?.addressCountry ?? "",
    },
  }
  if (fmt(flags) === "plain") {
    process.stdout.write(`${result.title}\n${result.company.name || "—"} · ${result.location.city || "—"}\n\n${stripHtml(result.description || "")}\n\nURL: ${result.url}\n`)
  } else {
    process.stdout.write(JSON.stringify(result, null, 2) + "\n")
  }
  return 0
}

const HELP = `jobbank-cli

USAGE
  bun run src/cli.ts search [--key text] [filters] [--format json|table|plain]
  bun run src/cli.ts detail <id> [--format json|plain]
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
    writeError(`Unknown command "${command}"`, "BAD_CMD")
    return 1
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }
}

main().then((code) => process.exit(code))
