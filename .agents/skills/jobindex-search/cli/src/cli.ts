#!/usr/bin/env bun

import { BASE_URL, apiFetch, htmlFetch, parseHitCount, parseJobCards, writeError } from "./helpers.js"

interface Flags {
  _: string[]
  [key: string]: string | boolean
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query" }
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg.startsWith("--") || arg.startsWith("-")) {
      const key = alias[arg.replace(/^-+/, "")] ?? arg.replace(/^-+/, "")
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

function renderRows(rows: any[], format: "json" | "table" | "plain", meta: any): void {
  if (format === "json") {
    process.stdout.write(JSON.stringify({ meta, results: rows }, null, 2) + "\n")
    return
  }
  if (format === "plain") {
    process.stdout.write(rows.map((r) => `${r.title}\n  ${r.company || "—"} · ${r.location || "—"} · ${r.date || "—"}\n  id: ${r.id}\n  ${r.url}`).join("\n\n") + "\n")
    return
  }
  const header = `${"ID".padEnd(10)} ${"TITLE".padEnd(42)} ${"COMPANY".padEnd(24)} ${"LOCATION".padEnd(22)} DATE`
  const lines = rows.map((r) =>
    `${String(r.id || "").padEnd(10)} ${String(r.title || "").slice(0, 42).padEnd(42)} ${String(r.company || "—").slice(0, 24).padEnd(24)} ${String(r.location || "—").slice(0, 22).padEnd(22)} ${r.date || "—"}`,
  )
  process.stdout.write([header, "-".repeat(header.length), ...lines].join("\n") + "\n")
}

async function runSearch(flags: Flags): Promise<number> {
  const params: Record<string, string> = {
    page: val(flags, "page") || "1",
    jobage: val(flags, "jobage") || "9999",
    sort: val(flags, "sort") || "score",
  }
  const query = val(flags, "query")
  if (query) params.q = query

  const data = await apiFetch<any>("/jobsoegning.json", params)
  const html = data.result_list_box_html ?? data.resultListBoxHtml ?? data.html ?? ""
  let rows = parseJobCards(html)
  const limit = Number(val(flags, "limit"))
  if (Number.isFinite(limit) && limit > 0) rows = rows.slice(0, limit)
  const total = parseHitCount(data.hitcount_html ?? data.hitCountHtml ?? "")
  renderRows(rows, fmt(flags), { total, page: Number(params.page), perPage: 20 })
  return 0
}

function firstMatch(html: string, re: RegExp): string | null {
  return stripHtml(html.match(re)?.[1] || "") || null
}

async function runDetail(flags: Flags): Promise<number> {
  const input = flags._[1]
  if (!input) {
    writeError("detail requires an <id|url>", "NO_ID")
    return 1
  }
  const url = input.startsWith("http") ? input : `${BASE_URL}/jobannonce/${input}`
  const html = await htmlFetch(url)
  const canonical = html.match(/<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["']/i)?.[1] ?? url
  const id = canonical.match(/\/jobannonce\/([^/]+)/)?.[1] ?? input
  const title = firstMatch(html, /<h1[^>]*>([\s\S]*?)<\/h1>/i) ?? "(untitled)"
  const company = firstMatch(html, /class=["'][^"']*(?:jix_jobdetails_company|company)[^"']*["'][^>]*>([\s\S]*?)<\/[^>]+>/i)
  const descriptionBlock = html.match(/class=["'][^"']*(?:jobtext|jobad|jix_jobdetails)[^"']*["'][^>]*>([\s\S]*?)(?:<\/main>|<\/article>|<\/body>)/i)?.[1] ?? html
  const applyUrl = html.match(/href=["']([^"']*\/c\?t=[^"']+)["']/i)?.[1] ?? null
  const result = {
    id,
    title,
    company,
    companyUrl: null,
    location: null,
    date: null,
    deadline: null,
    employmentType: null,
    hours: null,
    applyUrl: applyUrl ? new URL(applyUrl, BASE_URL).toString() : null,
    url: canonical,
    description: stripHtml(descriptionBlock),
  }
  if (fmt(flags) === "plain") {
    process.stdout.write(`${result.title}\n${result.company || "—"}\n\n${result.description}\n\nURL: ${result.url}\n${result.applyUrl ? `Apply: ${result.applyUrl}\n` : ""}`)
  } else {
    process.stdout.write(JSON.stringify(result, null, 2) + "\n")
  }
  return 0
}

const HELP = `jobindex-cli

USAGE
  bun run src/cli.ts search --query <text> [--jobage 7] [--format json|table|plain]
  bun run src/cli.ts detail <id|url> [--format json|plain]
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
    writeError(`Unknown command "${command}"`, "BAD_CMD")
    return 1
  } catch (error) {
    writeError(error instanceof Error ? error.message : String(error), "API_ERROR")
    return 1
  }
}

main().then((code) => process.exit(code))
