#!/usr/bin/env python3
"""
One-shot importer (section 6 step 5): the OneOfEverything sample -> catalogue.sqlite.

    python3 import_sample.py [--fm-version 22.0] [--dry-run]

Reads
  to_analyze/script.xml   clipboard XML       -> clipboard_xml_representations / _elements / _observations
  to_analyze/script.pdf   Script Editor print  -> ui_representations / ui_options / ui_observations
  display_map.yaml        option labels etc.   -> provisional step_options (origin 'display_map'),
                                                  ui_options display fields, ui_option_value_displays
  step_curated.yaml       kind flags           -> script_steps.control_flow_role / is_container_step / ...
and fills script_steps.fm_step_id by matching XML step names to the scraped help steps.
(inventory.json's kind flags were empty for every step, so they are curated instead.)

Every XML step instance becomes a step_configurations row (the first instance of a step is its baseline).
Element rows are one per XML leaf and per repeat (Q5). Re-running replaces everything this importer owns
(the tables above, display_map options, and its two sources rows) in one transaction; help-scraped data is
untouched. Run `scrape_help.py parse` first so script_steps exists.

Needs PyYAML and pdfplumber. On Windows:
    uv run --no-project --with pyyaml --with pdfplumber import_sample.py
"""

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime

import yaml

import investigate_options as io_
from scrape_help import BASE_DIR, connect

XML_FILE = "to_analyze/script.xml"
PDF_FILE = "to_analyze/script.pdf"
DISPLAY_MAP = BASE_DIR / "display_map.yaml"
CURATED = BASE_DIR / "step_curated.yaml"
LOCALE = "en"
SCRIPT_NAME = "OneOfEverything"
PDF_STAMP = re.compile(r"(\w+ \d{1,2}, \d{4} \d{1,2}:\d{2}:\d{2}) \S+\.fmp12")
LOCATIONS = {"inline": "inline", "continuation": "continuation", "hidden-or-dialog-only": "dialog_only"}


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def short_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def norm_name(name):
    return re.sub(r"\s+", " ", name).strip().lower()


# ── XML ───────────────────────────────────────────────────────────────────────

def xml_shape(elem):
    """Structure without values: tags, attribute names, text presence. A run of same-tag siblings
    collapses to one, so a step with 4 or 6 import fields has the same shape."""
    children, prev = [], None
    for child in elem:
        if child.tag != prev:
            children.append(xml_shape(child))
        prev = child.tag
    return [elem.tag, sorted(elem.attrib), bool((elem.text or "").strip()), children]


def xml_leaves(step):
    """(xml_path, parent_path, repeat_index, value) for every attribute and text under the step,
    in document order. Paths are index-free; repeat_index is the position among same-tag siblings
    of the innermost element on the path that repeats."""
    out = []

    def walk(elem, path, repeat):
        for attr, val in elem.attrib.items():
            out.append((f"{path}/@{attr}", path, repeat, val))
        text = (elem.text or "").strip()
        if text:
            out.append((f"{path}/text()", path, repeat, elem.text))
        counts = Counter(c.tag for c in elem)
        seen = Counter()
        for child in elem:
            idx = seen[child.tag]
            seen[child.tag] += 1
            walk(child, f"{path}/{child.tag}" if path else child.tag, idx if counts[child.tag] > 1 else repeat)

    for child in step:
        walk(child, child.tag, 0)
    return out


def leaf_type(xml_path, value):
    if xml_path.endswith("Calculation/text()"):
        return "calculation"
    attr = xml_path.rsplit("/@", 1)[1] if "/@" in xml_path else None
    if value in ("True", "False"):
        return "boolean"
    if attr in ("id", "name", "table", "UUID"):
        return "reference"
    if attr == "value":
        return "enum"
    if re.fullmatch(r"-?\d+", value or ""):
        return "number"
    return "text"


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fm-version", default="22.0", help="FileMaker version that produced script.xml/.pdf")
    ap.add_argument("--dry-run", action="store_true", help="roll back instead of committing")
    args = ap.parse_args()

    conn = connect()
    report = defaultdict(list)

    version = conn.execute("SELECT id FROM fm_versions WHERE version = ?", (args.fm_version,)).fetchone()
    if not version:
        sys.exit(f"fm_versions has no {args.fm_version}; add it first")
    version_id = version[0]

    steps = io_.parse_steps(BASE_DIR / XML_FILE)
    dm = {e["stepId"]: e for e in yaml.safe_load(DISPLAY_MAP.read_text(encoding="utf-8"))}
    curated = yaml.safe_load(CURATED.read_text(encoding="utf-8")) or {}
    pdf_lines = io_.pdf_lines(BASE_DIR / PDF_FILE)
    printed, unmatched_lines = io_.match_pdf_to_steps(steps, pdf_lines)
    report["unmatched PDF lines"] = unmatched_lines
    stamp = next((m.group(1) for ln in _raw_pdf_text() for m in [PDF_STAMP.search(ln)] if m), None)
    pdf_captured = datetime.strptime(stamp, "%B %d, %Y %H:%M:%S").isoformat() if stamp else None

    # Help step names -> script_steps.id; the help adds platform suffixes the XML lacks: 'Speak (macOS)'.
    by_name = {}
    for sid, name in conn.execute(
            "SELECT script_step_id, name FROM script_step_localizations WHERE locale = ?", (LOCALE,)):
        by_name[norm_name(name)] = sid
        by_name.setdefault(norm_name(re.sub(r"\s*\((macOS|OS X|Windows)\)$", "", name)), sid)

    with conn:  # one transaction
        if args.dry_run:
            conn.execute("SAVEPOINT dry")
        wipe(conn)
        src_xml = add_source(conn, "clipboard_export", XML_FILE, version_id, None)
        src_pdf = add_source(conn, "pdf_printout", PDF_FILE, version_id, pdf_captured)

        option_ids = {}        # (script_step_id, display_map key) -> step_options.id
        config_count = Counter()
        matched_ids = set()
        for index, ((step, main_text, conts)) in enumerate(printed):
            xml_name = step.get("name")
            fm_id = int(step.get("id"))
            ss_id = by_name.get(norm_name(xml_name))
            if ss_id is None:
                report["XML steps with no help step"].append(f"{xml_name} (id {fm_id})")
                continue
            matched_ids.add(ss_id)
            set_fm_step_id(conn, ss_id, fm_id, report)
            dm_opts = (dm.get(fm_id) or {}).get("options") or []
            if ss_id not in config_count:  # first instance: create this step's provisional options
                for pos, o in enumerate(dm_opts):
                    option_ids[(ss_id, o["key"])] = add_option(conn, ss_id, o, pos)

            # configuration
            n = config_count[ss_id]
            config_count[ss_id] += 1
            leaves = xml_leaves(step)
            values = defaultdict(list)
            for path, _, _, val in leaves:
                values[path.split("/")[0]].append(val)
            summary = {o["key"]: _one(values.get(o["xmlPath"].split("/")[0], [])) for o in dm_opts}
            cur = conn.execute(
                "INSERT INTO step_configurations (script_step_id, key, description, is_baseline, setting_summary,"
                " location) VALUES (?, ?, ?, ?, ?, ?)",
                (ss_id, "baseline" if n == 0 else f"instance-{n + 1}",
                 "As found in the OneOfEverything sample script", int(n == 0),
                 json.dumps(summary, sort_keys=True), f"{SCRIPT_NAME}#{index}"))
            config_id = cur.lastrowid

            # clipboard XML
            example = ET.tostring(step, encoding="unicode").strip()
            rep_id = conn.execute(
                "INSERT INTO clipboard_xml_representations (script_step_id, configuration_id, shape_hash, example_xml)"
                " VALUES (?, ?, ?, ?)", (ss_id, config_id, short_hash(xml_shape(step)), example)).lastrowid
            conn.execute("INSERT INTO clipboard_xml_observations VALUES (?, ?)", (rep_id, src_xml))
            opt_by_tag = {o["xmlPath"].split("/")[0]: o for o in dm_opts}
            for pos, (path, parent, repeat, val) in enumerate(leaves):
                o = opt_by_tag.get(path.split("/")[0])
                allowed = None
                if o and o["xmlPath"] == path:
                    if o.get("type") == "boolean":
                        allowed = ["True", "False"]
                    elif o.get("allowedValues"):
                        allowed = [v["xmlValue"] for v in o["allowedValues"]]
                conn.execute(
                    "INSERT INTO clipboard_xml_elements (representation_id, step_option_id, xml_path, parent_path,"
                    " repeat_index, value_type, allowed_values, example_value, position)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (rep_id, option_ids.get((ss_id, o["key"])) if o else None, path, parent, repeat,
                     leaf_type(path, val), json.dumps(allowed) if allowed else None, val, pos))

            # Script Editor
            if main_text is None:
                report["steps not found in the PDF"].append(f"{xml_name} #{index}")
                continue
            add_ui(conn, ss_id, config_id, src_pdf, main_text, conts, dm_opts, option_ids, values, report)

        apply_kind_flags(conn, curated.get("kind") or {})
        report["help steps missing from the sample"] = [
            slug for sid, slug in conn.execute("SELECT id, slug FROM script_steps ORDER BY slug")
            if sid not in matched_ids]

        print_report(conn, report)
        if args.dry_run:
            conn.execute("ROLLBACK TO dry")
            conn.execute("RELEASE dry")
            print("\ndry run: rolled back")


def _raw_pdf_text():
    import pdfplumber
    with pdfplumber.open(BASE_DIR / PDF_FILE) as pdf:
        return (pdf.pages[0].extract_text() or "").splitlines()


def _one(vals):
    return vals[0] if len(vals) == 1 else (vals or None)


def wipe(conn):
    """Delete everything this importer owns, children first."""
    for sql in [
        "DELETE FROM ui_option_value_displays",
        "DELETE FROM ui_options",
        "DELETE FROM ui_observations",
        "DELETE FROM ui_representations",
        "DELETE FROM clipboard_xml_elements",
        "DELETE FROM clipboard_xml_observations",
        "DELETE FROM clipboard_xml_representations",
        "DELETE FROM step_configurations",
        "DELETE FROM step_option_value_localizations WHERE step_option_value_id IN (SELECT v.id FROM"
        " step_option_values v JOIN step_options o ON o.id = v.step_option_id WHERE o.origin = 'display_map')",
        "DELETE FROM step_option_values WHERE step_option_id IN (SELECT id FROM step_options WHERE origin = 'display_map')",
        "DELETE FROM step_option_localizations WHERE step_option_id IN (SELECT id FROM step_options WHERE origin = 'display_map')",
        "DELETE FROM step_options WHERE origin = 'display_map'",
        f"DELETE FROM sources WHERE uri_or_path IN ('{XML_FILE}', '{PDF_FILE}')",
    ]:
        conn.execute(sql)


def add_source(conn, kind, rel_path, version_id, captured_at):
    return conn.execute(
        "INSERT INTO sources (kind, fm_version_id, uri_or_path, captured_at, sha256, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (kind, version_id, rel_path, captured_at, sha256_file(BASE_DIR / rel_path),
         "OneOfEverything in EverythingBagel.fmp12; made with FileMaker Pro 22 (patch level not recorded)")).lastrowid


def set_fm_step_id(conn, ss_id, fm_id, report):
    clash = conn.execute("SELECT slug FROM script_steps WHERE fm_step_id = ? AND id != ?", (fm_id, ss_id)).fetchone()
    if clash:
        report["fm_step_id clashes"].append(f"id {fm_id} already on {clash[0]}")
        return
    conn.execute("UPDATE script_steps SET fm_step_id = ? WHERE id = ?", (fm_id, ss_id))


def apply_kind_flags(conn, kind):
    """step_curated.yaml `kind` -> script_steps; every step not listed is reset to no role / false / false."""
    slugs = {r[0] for r in conn.execute("SELECT slug FROM script_steps")}
    unknown = sorted(set(kind) - slugs)
    if unknown:
        sys.exit(f"step_curated.yaml: unknown step slugs {unknown}")
    conn.execute("UPDATE script_steps SET control_flow_role = NULL, is_container_step = 0, is_terminator_step = 0")
    for slug, k in kind.items():
        conn.execute(
            "UPDATE script_steps SET control_flow_role = ?, is_container_step = ?, is_terminator_step = ?"
            " WHERE slug = ?",
            (k.get("controlFlowRole"), int(bool(k.get("container"))), int(bool(k.get("terminator"))), slug))


def add_option(conn, ss_id, o, pos):
    oid = conn.execute(
        "INSERT INTO step_options (script_step_id, key, value_type, position, origin) VALUES (?, ?, ?, ?, 'display_map')",
        (ss_id, o["key"], o.get("type") or "text", pos)).lastrowid
    conn.execute("INSERT INTO step_option_localizations (step_option_id, locale, label) VALUES (?, ?, ?)",
                 (oid, LOCALE, o.get("label") or o["key"]))
    for vpos, v in enumerate(o.get("allowedValues") or []):
        conn.execute("INSERT INTO step_option_values (step_option_id, value, position) VALUES (?, ?, ?)",
                     (oid, v["xmlValue"], vpos))
    return oid


def add_ui(conn, ss_id, config_id, src_pdf, main_text, conts, dm_opts, option_ids, values, report):
    segs = []
    for block, where in [(main_text, "inline")] + [(c, "continuation") for c in conts]:
        body = io_.bracket_body(block)
        if body is not None:
            segs += [(s, where) for s in io_.split_segments(body)]
    by_key_values = {o["key"]: values.get(o["xmlPath"].split("/")[0], []) for o in dm_opts}
    labelled = [(seg, where, re.match(r"^([^\"“:]+):", seg)) for seg, where in segs]
    shape = [[where, m.group(1).strip() if m else "*"] for seg, where, m in labelled]
    example = "\n".join([main_text] + conts)
    ui_id = conn.execute(
        "INSERT INTO ui_representations (script_step_id, configuration_id, locale, shape_hash, example_text)"
        " VALUES (?, ?, ?, ?, ?)", (ss_id, config_id, LOCALE, short_hash(shape), example)).lastrowid
    conn.execute("INSERT INTO ui_observations VALUES (?, ?)", (ui_id, src_pdf))

    used = set()
    pos = 0
    for seg, where, m in labelled:
        hits = io_.attribute_segment(seg, dm_opts, by_key_values)
        o = next((x for x in dm_opts if x["key"] in hits), None) if len(hits) == 1 else None
        if len(hits) > 1:
            report["segments matching several options"].append(f"{seg!r} -> {sorted(hits)}")
        if o:
            used.add(o["key"])
        add_ui_option(conn, ui_id, ss_id, o, option_ids, m.group(1).strip() if m else None, where, pos, seg)
        pos += 1
    for o in dm_opts:  # options the line does not show: false-and-omitted, dialog-only, or not attributed
        if o["key"] not in used:
            add_ui_option(conn, ui_id, ss_id, o, option_ids, o.get("label"),
                          LOCATIONS.get(o.get("displayLocation"), o.get("displayLocation") or "dialog_only"),
                          pos, None)
            pos += 1


def add_ui_option(conn, ui_id, ss_id, o, option_ids, label, where, pos, example):
    o = o or {}
    uo = conn.execute(
        "INSERT INTO ui_options (ui_representation_id, step_option_id, label, display_location, position,"
        " omit_when_false, true_text, false_text, example_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ui_id, option_ids.get((ss_id, o.get("key"))), label or o.get("label"), where, pos,
         None if o.get("omitWhenFalse") is None else int(o["omitWhenFalse"]),
         o.get("trueText"), o.get("falseText"), example)).lastrowid
    for v in o.get("allowedValues") or []:
        if v.get("displayText") is not None:
            conn.execute("INSERT INTO ui_option_value_displays VALUES (?, ?, ?)", (uo, v["xmlValue"], v["displayText"]))


def print_report(conn, report):
    print("Imported:")
    for table in ["sources", "step_options", "step_configurations", "clipboard_xml_representations",
                  "clipboard_xml_elements", "ui_representations", "ui_options", "ui_option_value_displays"]:
        print(f"  {table:32} {conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]}")
    print(f"  {'script_steps with fm_step_id':32} "
          f"{conn.execute('SELECT COUNT(*) FROM script_steps WHERE fm_step_id IS NOT NULL').fetchone()[0]}")
    for title, rows in report.items():
        print(f"\n{title} ({len(rows)})")
        for r in rows:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
