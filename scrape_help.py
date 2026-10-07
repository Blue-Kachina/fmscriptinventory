#!/usr/bin/env python3
"""
Scrape the FileMaker Pro script-step help pages into catalogue.sqlite.

Two stages, so parsing can be re-run without re-fetching:

    python3 scrape_help.py fetch  [--locale en] [--delay 1.0] [--refresh] [--limit N]
    python3 scrape_help.py parse  [--locale en]
    python3 scrape_help.py status

fetch  crawls the "Script steps reference" page, each category page it links to, and every
       step page those list, storing the raw HTML in help_pages (history is kept).
parse  fills script_step_categories, script_steps, localizations, sections, examples and
       compatibility from the newest fetch of each page. Idempotent.

Standard library only. See database_structure_brainstorming.md for the schema plan.
"""

import argparse
import hashlib
import html
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "catalogue.sqlite"
MIGRATIONS_DIR = BASE_DIR / "migrations"

HELP_ROOT = "https://help.claris.com/{locale}/pro-help/content/"
REFERENCE_PAGE = "script-steps-reference.html"
USER_AGENT = "fmscriptinventory-scraper/0.1 (personal research; matthew.leering@directimpactsolutions.com)"

CATEGORY_HREF = re.compile(r'<a href="([a-z0-9-]+)-script-steps\.html"[^>]*>([^<]+)<')
# A category page lists steps as table rows: <td><p><a href="slug.html">Name</a></p></td><td><p>Purpose</p></td>
STEP_ROW = re.compile(r'<td[^>]*>\s*<p><a href="([a-z0-9-]+)\.html">([^<]+)</a></p>')


# ── database ──────────────────────────────────────────────────────────────────

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    apply_migrations(conn)
    return conn


def apply_migrations(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations")}
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        conn.executescript(path.read_text(encoding="utf8"))
        conn.execute("INSERT INTO schema_migrations VALUES (?, ?)", (path.name, now()))
        conn.commit()
        print(f"applied {path.name}")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── fetch stage ───────────────────────────────────────────────────────────────

def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf8", errors="replace")


class Fetcher:
    def __init__(self, conn, locale, delay, refresh):
        self.conn, self.locale, self.delay, self.refresh = conn, locale, delay, refresh
        self.root = HELP_ROOT.format(locale=locale)
        self.fetched = 0

    def get(self, page, kind):
        """Return raw HTML for a page, fetching only when we have no copy (or --refresh)."""
        url = self.root + page
        if not self.refresh:
            row = self.conn.execute(
                "SELECT raw_html FROM help_pages WHERE url = ? AND http_status = 200 ORDER BY fetched_at DESC LIMIT 1",
                (url,)).fetchone()
            if row:
                return row["raw_html"]
        if self.fetched:
            time.sleep(self.delay)
        status, body = http_get(url)
        self.fetched += 1
        modified = re.search(r'<meta property="article:modified_time" content="([^"]+)"', body)
        self.conn.execute(
            "INSERT INTO help_pages (url, locale, kind, fetched_at, http_status, page_modified_at, raw_html, sha256)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (url, self.locale, kind, now(), status, modified.group(1) if modified else None, body,
             hashlib.sha256(body.encode("utf8")).hexdigest()))
        self.conn.commit()
        print(f"  {status} {page}")
        if status != 200:
            raise RuntimeError(f"{url} returned {status}")
        return body


def discover_categories(reference_html):
    seen = {}
    for slug, name in CATEGORY_HREF.findall(reference_html):
        seen.setdefault(slug, name.strip())
    return list(seen.items())


def discover_steps(category_html):
    main = main_content(category_html)
    return [(slug, html.unescape(name).strip()) for slug, name in STEP_ROW.findall(main)]


def cmd_fetch(args):
    conn = connect()
    fetcher = Fetcher(conn, args.locale, args.delay, args.refresh)
    reference = fetcher.get(REFERENCE_PAGE, "reference")
    categories = discover_categories(reference)
    print(f"{len(categories)} categories")
    step_pages = []
    for cat_slug, _ in categories:
        category_html = fetcher.get(f"{cat_slug}-script-steps.html", "category")
        steps = discover_steps(category_html)
        print(f"{cat_slug}: {len(steps)} steps")
        step_pages += [slug for slug, _ in steps]
    if args.limit:
        step_pages = step_pages[:args.limit]
    for slug in dict.fromkeys(step_pages):
        fetcher.get(f"{slug}.html", "step")
    print(f"done; {fetcher.fetched} pages fetched from the network")


# ── HTML helpers ──────────────────────────────────────────────────────────────

def main_content(page_html):
    """The topic body: from <div id="mc-main-content"> up to the feedback line."""
    page_html = re.sub(r"<script.*?</script>", "", page_html, flags=re.S)
    start = page_html.find('id="mc-main-content"')
    end = page_html.find('<p class="feedback">', start)
    return page_html[start:end if end != -1 else None]


BLOCK_TAGS = {"p", "div", "ul", "ol", "tr", "h1", "h2", "h3", "h4", "table", "pre", "li"}


class TextExtractor(HTMLParser):
    """HTML fragment -> plain text. Block tags become line breaks, <li> become '- ' items."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.in_pre = 0

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")
            self.in_pre += tag == "pre"
        elif tag in ("td", "th"):
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
            self.in_pre -= tag == "pre"

    def handle_data(self, data):
        self.parts.append(data if self.in_pre else re.sub(r"\s+", " ", data))

    def text(self):
        text = "".join(self.parts).replace("\xa0", " ")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\n\s*\|\s", "\n", text)  # a leading cell separator on a row is just noise
        return text.strip()


def to_text(fragment):
    parser = TextExtractor()
    parser.feed(fragment)
    return parser.text()


# ── parse stage ───────────────────────────────────────────────────────────────

def latest_page(conn, url):
    return conn.execute(
        "SELECT id, raw_html FROM help_pages WHERE url = ? AND http_status = 200 ORDER BY fetched_at DESC LIMIT 1",
        (url,)).fetchone()


def get_or_create_version(conn, raw):
    """'19.6.1' / '12' -> fm_versions row id. None when the text is not a plain version number."""
    # Trailing words ("6.0 or earlier") are tolerated here; the verbatim text stays in originated_in_raw.
    match = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?\b", raw.strip())
    if not match:
        return None
    major, minor, patch = (int(g or 0) for g in match.groups())
    version = f"{major}.{minor}.{patch}" if match.group(3) else (f"{major}.{minor}" if match.group(2) else str(major))
    conn.execute(
        "INSERT OR IGNORE INTO fm_versions (version, major, minor, patch, sort_key) VALUES (?, ?, ?, ?, ?)",
        (version, major, minor, patch, major * 1_000_000 + minor * 1_000 + patch))
    return conn.execute("SELECT id FROM fm_versions WHERE version = ?", (version,)).fetchone()["id"]


def parse_step_page(page_html):
    main = main_content(page_html)
    name = re.search(r"<h1[^>]*>(.*?)</h1>", main, flags=re.S)
    purpose = re.search(r'<p class="ref-purpose-script">(.*?)</p>', main, flags=re.S)
    result = {
        "name": to_text(name.group(1)) if name else None,
        "purpose": to_text(purpose.group(1)) if purpose else None,
        "sections": [], "examples": [], "compat": [], "originated": None,
    }
    # Split on each <h2 class="..."> heading; everything up to the next heading belongs to it.
    heads = list(re.finditer(r'<h2 class="([^"]+)"[^>]*>(.*?)</h2>', main, flags=re.S))
    for i, head in enumerate(heads):
        key = head.group(1).replace("-head", "")
        title = to_text(head.group(2))
        body_html = main[head.end(): heads[i + 1].start() if i + 1 < len(heads) else None]
        if key == "ref-compat":
            for row in re.finditer(r'<tr class="[^"]*Body[^"]*">(.*?)</tr>', body_html, flags=re.S):
                prod = re.search(r"Prod:(\w+)", row.group(1))
                supported = re.search(r"Supported:(\w+)", row.group(1))
                if prod and supported:
                    result["compat"].append((prod.group(1), supported.group(1)))
        elif key == "ref-orig":
            result["originated"] = to_text(body_html)
        elif re.fullmatch(r"ref-example(?:\d+|n)", key):
            code = "\n".join(to_text(m.group(1)) for m in re.finditer(r"<pre[^>]*>(.*?)</pre>", body_html, flags=re.S))
            before_code = body_html.split('<div class="codeSnippet"')[0]
            result["examples"].append((title, to_text(before_code), code))
        if key not in ("ref-compat",):
            result["sections"].append((key, title, to_text(body_html)))
    return result


def cmd_parse(args):
    conn = connect()
    root = HELP_ROOT.format(locale=args.locale)
    reference = latest_page(conn, root + REFERENCE_PAGE)
    if not reference:
        sys.exit("no reference page fetched yet; run `fetch` first")

    step_category = {}
    for position, (cat_slug, _) in enumerate(discover_categories(reference["raw_html"])):
        page = latest_page(conn, f"{root}{cat_slug}-script-steps.html")
        if not page:
            print(f"warning: category page for {cat_slug} not fetched", file=sys.stderr)
            continue
        body = main_content(page["raw_html"])
        cat_name = to_text(re.search(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S).group(1))
        description = re.search(r"<p>(.*?)</p>", body, flags=re.S)
        conn.execute("INSERT INTO script_step_categories (slug, position) VALUES (?, ?)"
                     " ON CONFLICT (slug) DO UPDATE SET position = excluded.position", (cat_slug, position))
        cat_id = conn.execute("SELECT id FROM script_step_categories WHERE slug = ?", (cat_slug,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO script_step_category_localizations (category_id, locale, name, description, help_page_id)"
            " VALUES (?, ?, ?, ?, ?) ON CONFLICT (category_id, locale) DO UPDATE SET"
            " name = excluded.name, description = excluded.description, help_page_id = excluded.help_page_id",
            (cat_id, args.locale, cat_name, to_text(description.group(1)) if description else None, page["id"]))
        for slug, _ in discover_steps(page["raw_html"]):
            if slug in step_category and step_category[slug] != cat_id:
                print(f"warning: {slug} is listed in more than one category; keeping the first", file=sys.stderr)
                continue
            step_category[slug] = cat_id

    parsed = unparsed_versions = missing = 0
    for slug, cat_id in step_category.items():
        page = latest_page(conn, f"{root}{slug}.html")
        if not page:
            missing += 1
            continue
        step = parse_step_page(page["raw_html"])
        if not step["name"]:
            print(f"warning: {slug}: no title found, skipped", file=sys.stderr)
            continue
        version_id = get_or_create_version(conn, step["originated"] or "")
        if step["originated"] and version_id is None:
            unparsed_versions += 1
            print(f"note: {slug}: originated-in text is not a version: {step['originated']!r}", file=sys.stderr)
        conn.execute(
            "INSERT INTO script_steps (slug, category_id, originated_in_version_id, originated_in_raw)"
            " VALUES (?, ?, ?, ?) ON CONFLICT (slug) DO UPDATE SET category_id = excluded.category_id,"
            " originated_in_version_id = excluded.originated_in_version_id,"
            " originated_in_raw = excluded.originated_in_raw",
            (slug, cat_id, version_id, step["originated"]))
        step_id = conn.execute("SELECT id FROM script_steps WHERE slug = ?", (slug,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO script_step_localizations (script_step_id, locale, name, purpose, help_page_id)"
            " VALUES (?, ?, ?, ?, ?) ON CONFLICT (script_step_id, locale) DO UPDATE SET"
            " name = excluded.name, purpose = excluded.purpose, help_page_id = excluded.help_page_id",
            (step_id, args.locale, step["name"], step["purpose"], page["id"]))
        for table in ("script_step_sections", "step_examples"):
            conn.execute(f"DELETE FROM {table} WHERE script_step_id = ? AND locale = ?", (step_id, args.locale))
        conn.execute("DELETE FROM step_compatibility WHERE script_step_id = ?", (step_id,))
        for position, (key, heading, text) in enumerate(step["sections"]):
            conn.execute("INSERT INTO script_step_sections VALUES (?, ?, ?, ?, ?, ?)",
                         (step_id, args.locale, position, key, heading, text))
        for position, (title, description, body) in enumerate(step["examples"]):
            conn.execute("INSERT INTO step_examples (script_step_id, locale, position, title, description, body)"
                         " VALUES (?, ?, ?, ?, ?, ?)", (step_id, args.locale, position, title, description, body))
        for product, supported in step["compat"]:
            conn.execute("INSERT INTO step_compatibility VALUES (?, ?, ?)", (step_id, product, supported))
        parsed += 1
    conn.commit()
    if missing:
        print(f"warning: {missing} listed step pages have not been fetched; run `fetch`", file=sys.stderr)
    print(f"parsed {parsed} steps in {len(set(step_category.values()))} categories"
          f" ({unparsed_versions} with a non-version 'originated' value)")


def cmd_status(_args):
    conn = connect()
    for table in ("help_pages", "script_step_categories", "script_steps", "script_step_sections",
                  "step_examples", "step_compatibility", "fm_versions"):
        print(f"{table:28} {conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]}")
    print("\nsteps per category:")
    for row in conn.execute(
            "SELECT l.name, COUNT(s.id) n FROM script_step_categories c"
            " JOIN script_step_category_localizations l ON l.category_id = c.id"
            " LEFT JOIN script_steps s ON s.category_id = c.id GROUP BY c.id ORDER BY c.position"):
        print(f"  {row['n']:4} {row['name']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--locale", default="en")
    fetch.add_argument("--delay", type=float, default=1.0, help="seconds between network requests")
    fetch.add_argument("--refresh", action="store_true", help="re-fetch pages we already have")
    fetch.add_argument("--limit", type=int, help="only fetch the first N step pages (for testing)")
    fetch.set_defaults(func=cmd_fetch)
    parse = sub.add_parser("parse")
    parse.add_argument("--locale", default="en")
    parse.set_defaults(func=cmd_parse)
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
