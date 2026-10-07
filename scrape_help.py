#!/usr/bin/env python3
"""
Scrape the FileMaker Pro help pages (script steps and calculations) into catalogue.sqlite.

Two stages, so parsing can be re-run without re-fetching:

    python3 scrape_help.py fetch  [--scope all|steps|calc] [--locale en] [--delay 1.0] [--refresh] [--limit N]
    python3 scrape_help.py parse  [--scope all|steps|calc] [--locale en]
    python3 scrape_help.py status

fetch  steps: crawls the "Script steps reference" page, each category page it links to, and every
              step page those list.
       calc:  crawls the "Functions reference" page, its category pages and every function and
              Get function page they list, plus the named constants, error codes and operators pages.
       Raw HTML is stored in help_pages (history is kept).
parse  fills the step tables (script_step_*) and the calculation tables (functions, get_constants,
       calc_constants, error_codes, ...) from the newest fetch of each page. Idempotent.
       Curated facts (calc_curated.yaml) are applied separately by calc_catalogue.py.

Standard library only. See database_structure_brainstorming.md for the schema plan (sections 9 and 10).
"""

import argparse
import hashlib
import html
import re
import sqlite3
import sys
import time
import urllib.error

import fm_signature
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

FUNCTIONS_PAGE = "functions-reference.html"
GET_CATEGORY = "get-functions"
# Single calculation-language pages: page -> help_pages.kind
CALC_PAGES = {
    "named-constants-keywords.html": "named-constants",
    "error-codes.html": "error-codes",
    "operators-in-formulas.html": "operators",
}


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


def discover_function_categories(reference_html):
    """Category pages of the functions reference, in order. The page's own mini-TOC is filled in by
    JavaScript, so they come from the navigation tree: the <ul> under the selected "Functions reference" node."""
    start = reference_html.find('class="selected">Functions reference')
    if start == -1:
        return []
    block = reference_html[start: reference_html.find("</ul>", start)]
    return [(slug, html.unescape(name).strip())
            for slug, name in re.findall(r'<a href="([a-z0-9-]+)\.html"[^>]*>([^<]+)<', block)]


def fetch_steps(fetcher, limit):
    reference = fetcher.get(REFERENCE_PAGE, "reference")
    categories = discover_categories(reference)
    print(f"{len(categories)} step categories")
    step_pages = []
    for cat_slug, _ in categories:
        category_html = fetcher.get(f"{cat_slug}-script-steps.html", "category")
        steps = discover_steps(category_html)
        print(f"{cat_slug}: {len(steps)} steps")
        step_pages += [slug for slug, _ in steps]
    if limit:
        step_pages = step_pages[:limit]
    for slug in dict.fromkeys(step_pages):
        fetcher.get(f"{slug}.html", "step")


def fetch_calc(fetcher, limit):
    reference = fetcher.get(FUNCTIONS_PAGE, "function-reference")
    categories = discover_function_categories(reference)
    print(f"{len(categories)} function categories")
    pages = {}
    for cat_slug, _ in categories:
        category_html = fetcher.get(f"{cat_slug}.html", "function-category")
        functions = discover_steps(category_html)  # same table layout as the step category pages
        print(f"{cat_slug}: {len(functions)} functions")
        for slug, _ in functions:
            pages.setdefault(slug, "get-function" if cat_slug == GET_CATEGORY else "function")
    for page, kind in CALC_PAGES.items():
        fetcher.get(page, kind)
    for slug, kind in list(pages.items())[:limit or None]:
        fetcher.get(f"{slug}.html", kind)


def cmd_fetch(args):
    conn = connect()
    fetcher = Fetcher(conn, args.locale, args.delay, args.refresh)
    if args.scope in ("all", "steps"):
        fetch_steps(fetcher, args.limit)
    if args.scope in ("all", "calc"):
        fetch_calc(fetcher, args.limit)
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


def parse_step_page(page_html, purpose_class="ref-purpose-script"):
    main = main_content(page_html)
    name = re.search(r"<h1[^>]*>(.*?)</h1>", main, flags=re.S)
    purpose = re.search(rf'<p class="{purpose_class}">(.*?)</p>', main, flags=re.S)
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
    if args.scope in ("all", "steps"):
        parse_steps(conn, args)
    if args.scope in ("all", "calc"):
        parse_calc(conn, args)


def parse_steps(conn, args):
    root = HELP_ROOT.format(locale=args.locale)
    reference = latest_page(conn, root + REFERENCE_PAGE)
    if not reference:
        sys.exit("no script steps reference page fetched yet; run `fetch --scope steps` first")

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


# ── parse stage: calculations ─────────────────────────────────────────────────

def function_category_key(slug):
    """'text-functions' -> 'text', 'json-functions-category' -> 'json'."""
    return re.sub(r"-functions(?:-category)?$", "", slug)


def section_html(main, key):
    """Raw HTML of the section under <h2 class="{key}-head">, up to the next <h2>."""
    head = re.search(rf'<h2 class="{key}-head"[^>]*>.*?</h2>', main, flags=re.S)
    if not head:
        return ""
    end = main.find("<h2", head.end())
    return main[head.end(): end if end != -1 else None]


def parse_function_page(page_html):
    """A function or Get function page: the step-page fields plus Format, Parameters and Data type returned."""
    page = parse_step_page(page_html, purpose_class="ref-purpose-func")
    main = main_content(page_html)
    # Usually <pre class="ref-format">, but some pages (Random) use a plain <p>
    format_text = next((text for key, _, text in page["sections"] if key == "ref-format"), "")
    lines = [line.strip() for line in format_text.splitlines() if line.strip()]
    page["format"] = lines[0] if lines else None
    page["format_extra"] = lines[1:]
    # Parameters are paragraphs like <p><code>text</code> - any text expression</p>
    page["params"] = []
    for para in re.findall(r"<p>\s*(<code>.*?)</p>", section_html(main, "ref-param"), flags=re.S):
        name = to_text(re.match(r"<code>(.*?)</code>", para, flags=re.S).group(1))
        description = to_text(para)[len(name):].lstrip(" -–—")
        page["params"].append((name, description))
    page["returns"] = next((text for key, _, text in page["sections"] if key == "ref-return"), None)
    return page


def table_rows(main):
    """Body rows of the tables in a page as lists of cell HTML."""
    return [re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)
            for row in re.findall(r'<tr class="[^"]*Body[^"]*">(.*?)</tr>', main, flags=re.S)]


def replace_sections(conn, page_id, sections):
    conn.execute("DELETE FROM calc_help_sections WHERE help_page_id = ?", (page_id,))
    for position, (key, heading, text) in enumerate(sections):
        conn.execute("INSERT INTO calc_help_sections VALUES (?, ?, ?, ?, ?)", (page_id, position, key, heading, text))


def store_function(conn, locale, slug, cat_id, page_id, page, version_id):
    sig = fm_signature.parse(page["format"] or "", expected_name=page["name"])
    issues = list(sig.issues)
    if not page["format"]:
        issues.append("no Format line on the page")
    if page["format_extra"]:
        issues.append(f"more than one Format line: {page['format_extra']!r}")
    return_type = fm_signature.map_return_type(page["returns"])
    if return_type is None:
        issues.append(f"unrecognised return type {page['returns']!r}")
    conn.execute(
        "INSERT INTO functions (slug, name, category_id, return_type, return_type_raw, signature, min_args, max_args,"
        " signature_status, signature_issues, originated_in_version_id, originated_in_raw)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (slug) DO UPDATE SET name = excluded.name,"
        " category_id = excluded.category_id, return_type = excluded.return_type,"
        " return_type_raw = excluded.return_type_raw, signature = excluded.signature,"
        " min_args = excluded.min_args, max_args = excluded.max_args,"
        " signature_status = excluded.signature_status, signature_issues = excluded.signature_issues,"
        " originated_in_version_id = excluded.originated_in_version_id,"
        " originated_in_raw = excluded.originated_in_raw",
        (slug, page["name"], cat_id, return_type, page["returns"], " ".join((page["format"] or "").split()),
         sig.min_args, sig.max_args, "needs-review" if issues else "parsed", "; ".join(issues) or None,
         version_id, page["originated"]))
    function_id = conn.execute("SELECT id FROM functions WHERE slug = ?", (slug,)).fetchone()["id"]
    conn.execute(
        "INSERT INTO function_localizations (function_id, locale, purpose, help_page_id) VALUES (?, ?, ?, ?)"
        " ON CONFLICT (function_id, locale) DO UPDATE SET purpose = excluded.purpose,"
        " help_page_id = excluded.help_page_id",
        (function_id, locale, page["purpose"], page_id))
    conn.execute("DELETE FROM function_parameter_constants WHERE parameter_id IN"
                 " (SELECT id FROM function_parameters WHERE function_id = ?)", (function_id,))
    conn.execute("DELETE FROM function_parameters WHERE function_id = ?", (function_id,))
    descriptions = {}
    for name, description in page["params"]:
        descriptions.setdefault(name, description)
        descriptions.setdefault(fm_signature.strip_number(name), description)
    for position, param in enumerate(sig.params):
        description = descriptions.get(param.name)
        conn.execute(
            "INSERT INTO function_parameters (function_id, position, name, type, type_source, optional, repeatable,"
            " group_key, help_description) VALUES (?, ?, ?, ?, 'inferred', ?, ?, ?, ?)",
            (function_id, position, param.name, fm_signature.infer_param_type(description, param.name), param.optional,
             param.repeatable, param.group, description))
    conn.execute("DELETE FROM function_compatibility WHERE function_id = ?", (function_id,))
    for product, supported in page["compat"]:
        conn.execute("INSERT INTO function_compatibility VALUES (?, ?, ?)", (function_id, product, supported))
    return not issues


def store_get_constant(conn, locale, slug, page_id, page, version_id):
    match = re.search(r"Get\s*\(\s*([A-Za-z0-9]+)\s*\)", page["format"] or page["name"])
    if not match:
        print(f"warning: {slug}: no Get ( name ) found, skipped", file=sys.stderr)
        return
    conn.execute(
        "INSERT INTO get_constants (slug, name, return_type, return_type_raw, originated_in_version_id,"
        " originated_in_raw) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (slug) DO UPDATE SET name = excluded.name,"
        " return_type = excluded.return_type, return_type_raw = excluded.return_type_raw,"
        " originated_in_version_id = excluded.originated_in_version_id,"
        " originated_in_raw = excluded.originated_in_raw",
        (slug, match.group(1), fm_signature.map_return_type(page["returns"]), page["returns"], version_id,
         page["originated"]))
    get_id = conn.execute("SELECT id FROM get_constants WHERE slug = ?", (slug,)).fetchone()["id"]
    conn.execute(
        "INSERT INTO get_constant_localizations (get_constant_id, locale, purpose, help_page_id) VALUES (?, ?, ?, ?)"
        " ON CONFLICT (get_constant_id, locale) DO UPDATE SET purpose = excluded.purpose,"
        " help_page_id = excluded.help_page_id",
        (get_id, locale, page["purpose"], page_id))
    conn.execute("DELETE FROM get_constant_compatibility WHERE get_constant_id = ?", (get_id,))
    for product, supported in page["compat"]:
        conn.execute("INSERT INTO get_constant_compatibility VALUES (?, ?, ?)", (get_id, product, supported))


def parse_named_constants(conn, page):
    count = 0
    for cells in table_rows(main_content(page["raw_html"])):
        if len(cells) < 2:
            continue
        name, group_raw = to_text(cells[0]), to_text(cells[1])
        notes = to_text(cells[2]) if len(cells) > 2 else None
        conn.execute(
            "INSERT INTO calc_constants (name, group_key, group_raw, help_notes, help_page_id) VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT (name) DO UPDATE SET group_key = excluded.group_key, group_raw = excluded.group_raw,"
            " help_notes = excluded.help_notes, help_page_id = excluded.help_page_id",
            (name, re.sub(r"[^a-z0-9]+", "-", group_raw.lower()).strip("-"), group_raw, notes, page["id"]))
        count += 1
    return count


def parse_error_codes(conn, page):
    count = 0
    for cells in table_rows(main_content(page["raw_html"])):
        code = re.match(r"-?\d+", to_text(cells[0])) if cells else None
        if not code or len(cells) < 2:
            continue
        conn.execute(
            "INSERT INTO error_codes (code, help_text, help_page_id) VALUES (?, ?, ?) ON CONFLICT (code)"
            " DO UPDATE SET help_text = excluded.help_text, help_page_id = excluded.help_page_id",
            (int(code.group()), to_text(cells[1]), page["id"]))
        count += 1
    return count


def parse_order_of_evaluation(page_html):
    """operators-in-formulas.html's ordered list -> [['/*', '*/', '//'], ..., ['OR', 'XOR']], tightest first."""
    main = main_content(page_html)
    items = re.findall(r"<li[^>]*>(.*?)</li>", main.split("Order of evaluation", 1)[-1], flags=re.S)
    return [[s.strip() for s in re.split(r",\s+", to_text(item)) if s.strip()] for item in items]


def parse_calc(conn, args):
    root = HELP_ROOT.format(locale=args.locale)
    reference = latest_page(conn, root + FUNCTIONS_PAGE)
    if not reference:
        sys.exit("no functions reference page fetched yet; run `fetch --scope calc` first")

    page_category = {}
    for position, (cat_slug, _) in enumerate(discover_function_categories(reference["raw_html"])):
        page = latest_page(conn, f"{root}{cat_slug}.html")
        if not page:
            print(f"warning: category page {cat_slug} not fetched", file=sys.stderr)
            continue
        cat_name = to_text(re.search(r"<h1[^>]*>(.*?)</h1>", main_content(page["raw_html"]), flags=re.S).group(1))
        conn.execute("INSERT INTO function_categories (slug, key, position) VALUES (?, ?, ?)"
                     " ON CONFLICT (slug) DO UPDATE SET key = excluded.key, position = excluded.position",
                     (cat_slug, function_category_key(cat_slug), position))
        cat_id = conn.execute("SELECT id FROM function_categories WHERE slug = ?", (cat_slug,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO function_category_localizations (category_id, locale, name, help_page_id) VALUES (?, ?, ?, ?)"
            " ON CONFLICT (category_id, locale) DO UPDATE SET name = excluded.name, help_page_id = excluded.help_page_id",
            (cat_id, args.locale, cat_name, page["id"]))
        for slug, _ in discover_steps(page["raw_html"]):
            if slug in page_category and page_category[slug][0] != cat_id:
                print(f"note: {slug} is listed in more than one category; keeping the first", file=sys.stderr)
                continue
            page_category[slug] = (cat_id, cat_slug == GET_CATEGORY)

    functions = get_constants = needs_review = missing = 0
    for slug, (cat_id, is_get) in page_category.items():
        page = latest_page(conn, f"{root}{slug}.html")
        if not page:
            missing += 1
            continue
        parsed = parse_function_page(page["raw_html"])
        if not parsed["name"]:
            print(f"warning: {slug}: no title found, skipped", file=sys.stderr)
            continue
        replace_sections(conn, page["id"], parsed["sections"])
        version_id = get_or_create_version(conn, parsed["originated"] or "")
        if is_get:
            store_get_constant(conn, args.locale, slug, page["id"], parsed, version_id)
            get_constants += 1
        else:
            needs_review += not store_function(conn, args.locale, slug, cat_id, page["id"], parsed, version_id)
            functions += 1

    extras = {}
    for page_name, kind in CALC_PAGES.items():
        page = latest_page(conn, root + page_name)
        if not page:
            print(f"warning: {page_name} not fetched", file=sys.stderr)
        elif kind == "named-constants":
            extras["named constants"] = parse_named_constants(conn, page)
        elif kind == "error-codes":
            extras["error codes"] = parse_error_codes(conn, page)
    conn.commit()
    if missing:
        print(f"warning: {missing} listed function pages have not been fetched; run `fetch --scope calc`",
              file=sys.stderr)
    print(f"parsed {functions} functions ({needs_review} need signature review), {get_constants} Get constants, "
          + ", ".join(f"{n} {what}" for what, n in extras.items()))


def cmd_status(_args):
    conn = connect()
    for table in ("help_pages", "script_step_categories", "script_steps", "script_step_sections",
                  "step_examples", "step_compatibility", "fm_versions", "function_categories", "functions",
                  "function_parameters", "get_constants", "calc_constants", "calc_operators", "error_codes"):
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
    fetch.add_argument("--scope", choices=("all", "steps", "calc"), default="all")
    fetch.add_argument("--locale", default="en")
    fetch.add_argument("--delay", type=float, default=1.0, help="seconds between network requests")
    fetch.add_argument("--refresh", action="store_true", help="re-fetch pages we already have")
    fetch.add_argument("--limit", type=int, help="only fetch the first N step / function pages (for testing)")
    fetch.set_defaults(func=cmd_fetch)
    parse = sub.add_parser("parse")
    parse.add_argument("--scope", choices=("all", "steps", "calc"), default="all")
    parse.add_argument("--locale", default="en")
    parse.set_defaults(func=cmd_parse)
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
