#!/usr/bin/env python3
"""
Option-mapping investigation (open question 5 in database_structure_brainstorming.md).

Question: is the link between a conceptual option and its renderings (XML elements,
Script Editor segments) 1:1, 1:N, or many-to-many?

Inputs (all already in the repo):
  to_analyze/script.xml   clipboard XML, one instance of every step
  to_analyze/script.pdf   the same script printed from the Script Editor
  display_map.yaml        one entry per option: xmlPath (top-level tag), label, displayLocation

Caveat: display_map.yaml was generated with one option per *top-level* XML child, so at
that level XML -> option is 1:1 by construction. The evidence therefore comes from
  - XML leaves (attributes, text, nested elements) under each option's element, and
  - UI segments (the `;`-separated parts inside `[ ... ]` on the printed line).

Usage:
  python3 investigate_options.py            # summary + details
  python3 investigate_options.py --summary  # summary only

Needs PyYAML and pdfplumber.
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber
import yaml

ROOT = Path(__file__).resolve().parent
XML_PATH = ROOT / "to_analyze" / "script.xml"
PDF_PATH = ROOT / "to_analyze" / "script.pdf"
DISPLAY_MAP = ROOT / "display_map.yaml"

# Attribute values that say nothing about which option produced them.
NOISE_VALUES = {"", "True", "False", "0", "1"}
# Attributes that identify a referenced object together with its name (one logical value).
REF_ID_ATTRS = {"id", "UUID"}


# ---------------------------------------------------------------------------
# XML side
# ---------------------------------------------------------------------------

def xml_leaves(elem, prefix):
    """Every attribute and non-empty text under elem, as (path, value)."""
    out = []
    for attr, val in elem.attrib.items():
        out.append((f"{prefix}/@{attr}", val))
    text = (elem.text or "").strip()
    if text:
        out.append((f"{prefix}/text()", text))
    for child in elem:
        out.extend(xml_leaves(child, f"{prefix}/{child.tag}"))
    return out


def logical_values(elem, prefix):
    """Leaves collapsed into logical values: an element's id + name (+ table) is one reference."""
    out = []
    attrs = dict(elem.attrib)
    if "name" in attrs:
        name = attrs.pop("name")
        table = attrs.pop("table", None)
        for a in REF_ID_ATTRS:
            attrs.pop(a, None)
        out.append((f"{prefix}[ref]", f"{table}::{name}" if table else name))
    for attr, val in attrs.items():
        out.append((f"{prefix}/@{attr}", val))
    text = (elem.text or "").strip()
    if text:
        out.append((f"{prefix}/text()", text))
    for child in elem:
        out.extend(logical_values(child, f"{prefix}/{child.tag}"))
    return out


def parse_steps(path):
    root = ET.parse(path).getroot()
    return [s for s in root.iter("Step")]


# ---------------------------------------------------------------------------
# UI side (PDF)
# ---------------------------------------------------------------------------

FOOTER_RE = re.compile(r"\.fmp12 - .* -\d+-$")


def pdf_lines(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or FOOTER_RE.search(line) or line == "OneOfEverything":
            continue
        lines.append(line)
    return lines


def norm(s):
    return re.sub(r"\s+", "", s).replace("“", '"').replace("”", '"').lower()


def display_name(step):
    return "#" if step.get("name") == "# (comment)" else step.get("name").strip()


def match_pdf_to_steps(steps, lines):
    """A line opens a step if it starts with a step name (longest match wins, so `Else If`
    beats `Else`); otherwise it is a wrap (joined) or a continuation block (starts with '[').
    The nth printed occurrence of a name is paired with the nth XML step of that name, so
    the printout's order does not have to match the XML's."""
    names = sorted({display_name(s) for s in steps}, key=len, reverse=True)
    printed = []  # [name, main_text, [continuations]]
    unmatched = []
    for ln in lines:
        nln = norm(ln)
        name = next((n for n in names if nln.startswith(norm(n))
                     # a name must end at a word boundary: `Copy` must not claim `Copy All Records/Requests`
                     and (len(nln) == len(norm(n)) or not nln[len(norm(n))].isalnum() or n == "#")), None)
        if name is not None and not ln.startswith("["):
            printed.append([name, ln, []])
        elif not printed:
            unmatched.append(ln)
        elif ln.startswith("["):
            printed[-1][2].append(ln)
        elif printed[-1][2]:
            printed[-1][2][-1] += " " + ln
        else:
            printed[-1][1] += " " + ln
    by_name = defaultdict(list)
    for p in printed:
        by_name[p[0]].append(p)
    result = []
    for step in steps:
        queue = by_name.get(display_name(step))
        if queue:
            _, main, conts = queue.pop(0)
            result.append((step, main, conts))
        else:
            result.append((step, None, []))
    return result, unmatched


def bracket_body(text):
    """Contents of the first top-level [ ... ] (honouring nested brackets and quotes), or None."""
    start = text.find("[")
    if start < 0:
        return None
    depth, quote = 0, False
    for j in range(start, len(text)):
        c = text[j]
        if c in '"“”':
            quote = not quote
        elif not quote and c == "[":
            depth += 1
        elif not quote and c == "]":
            depth -= 1
            if depth == 0:
                return text[start + 1:j]
    return text[start + 1:]


def split_segments(body):
    segs, cur, depth, quote = [], "", 0, False
    for c in body:
        if c in '"“”':
            quote = not quote
        if not quote and c in "[(":
            depth += 1
        if not quote and c in "])":
            depth -= 1
        if c == ";" and depth == 0 and not quote:
            segs.append(cur.strip())
            cur = ""
        else:
            cur += c
    segs.append(cur.strip())
    return [s for s in segs if s]


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

def attribute_segment(seg, options, values_by_option):
    """Which options does this UI segment render? By label ('Label:' prefix or the whole
    segment equal to the label / trueText) or by an XML value equal to its value part.
    A label names its option, so exactly one label match wins over value matches
    (`Flow: <unknown>` is `flow`, even though `text` also holds `<unknown>`)."""
    label_hits, value_hits = set(), set()
    nseg = norm(seg)
    # The value part: after "Label:" if there is one; quotes dropped so `"$file"` equals `$file`.
    nval = norm(seg.split(":", 1)[1]) if re.match(r"^[^\"“:]+:", seg) else nseg
    nval = nval.strip('"')
    for opt in options:
        key = opt["key"]
        for txt in (opt.get("label"), opt.get("trueText"), opt.get("falseText")):
            if txt and (nseg == norm(txt) or nseg.startswith(norm(txt) + ":")):
                label_hits.add(key)
        for val in values_by_option.get(key, []):
            if val in NOISE_VALUES:
                continue
            if norm(val).strip('"') in (nval, nseg):
                value_hits.add(key)
    if len(label_hits) == 1:
        return label_hits
    return label_hits | value_hits


def main():
    summary_only = "--summary" in sys.argv
    steps = parse_steps(XML_PATH)
    dm = {e["stepId"]: e for e in yaml.safe_load(DISPLAY_MAP.read_text(encoding="utf-8"))}

    # ---- XML side ----
    opts_per_tag = []         # (step, tag, [option keys]) where >1 option shares one element
    multi_leaf = []           # (step, option, leaves, logical)
    repeated_tags = []        # (step, tag, count)
    unmapped_tags = []        # (step, tag) XML child with no option
    missing_in_xml = []       # (step, option) option whose tag is absent from the sample
    leaf_hist, logical_hist = Counter(), Counter()
    values = {}               # (step_id, option key) -> [values]

    for step in steps:
        sid = int(step.get("id"))
        entry = dm.get(sid, {"options": []})
        options = entry.get("options") or []
        by_tag = defaultdict(list)
        for o in options:
            by_tag[o["xmlPath"].split("/")[0]].append(o)
        tags = Counter(c.tag for c in step)
        for tag, n in tags.items():
            if n > 1:
                repeated_tags.append((step.get("name"), tag, n))
            if tag not in by_tag:
                unmapped_tags.append((step.get("name"), tag))
        for tag, olist in by_tag.items():
            if len(olist) > 1:
                opts_per_tag.append((step.get("name"), tag, [o["key"] for o in olist]))
            elems = [c for c in step if c.tag == tag]
            if not elems:
                for o in olist:
                    missing_in_xml.append((step.get("name"), o["key"]))
                continue
            leaves = [lf for e in elems for lf in xml_leaves(e, tag)]
            logical = [lv for e in elems for lv in logical_values(e, tag)]
            for o in olist:
                leaf_hist[len(leaves)] += 1
                logical_hist[len(logical)] += 1
                values[(sid, o["key"])] = [v for _, v in logical]
                if len(logical) > 1:
                    multi_leaf.append((step.get("name"), o["key"], [p for p, _ in leaves], [p for p, _ in logical]))

    # ---- UI side ----
    matched, unmatched_lines = match_pdf_to_steps(steps, pdf_lines(PDF_PATH))
    seg_multi = []    # segment rendering >1 option
    opt_multi = []    # option rendered in >1 segment
    seg_none = []     # segment no option claims
    no_pdf = []
    seg_total = 0
    for step, main_text, conts in matched:
        sid = int(step.get("id"))
        name = step.get("name")
        options = (dm.get(sid) or {}).get("options") or []
        if main_text is None:
            no_pdf.append(name)
            continue
        vals = {o["key"]: values.get((sid, o["key"]), []) for o in options}
        segs = []
        for block, where in [(main_text, "inline")] + [(c, "continuation") for c in conts]:
            body = bracket_body(block)
            if body is not None:
                segs += [(s, where) for s in split_segments(body)]
        seen = defaultdict(list)
        for seg, where in segs:
            seg_total += 1
            hits = attribute_segment(seg, options, vals)
            if len(hits) > 1:
                seg_multi.append((name, seg, sorted(hits)))
            elif not hits:
                seg_none.append((name, seg, where))
            for h in hits:
                seen[h].append(seg)
        for key, sl in seen.items():
            if len(sl) > 1:
                opt_multi.append((name, key, sl))

    # ---- report ----
    n_opts = sum(len((dm.get(int(s.get("id"))) or {}).get("options") or []) for s in steps)
    print("# Option mapping investigation (Q5)\n")
    print(f"Steps in script.xml: {len(steps)}; display_map options for them: {n_opts}; "
          f"PDF steps matched: {len(steps) - len(no_pdf)}; UI segments: {seg_total}\n")
    print("## XML side")
    print(f"- Options sharing one XML element (option N:1 element): {len(opts_per_tag)}")
    print(f"- Options whose element holds >1 logical value (option 1:N leaves): {len(multi_leaf)}")
    print(f"  raw leaves per option: {dict(sorted(leaf_hist.items()))}")
    print(f"  logical values per option: {dict(sorted(logical_hist.items()))}")
    print(f"- Repeated top-level tags in one step: {len(repeated_tags)}")
    print(f"- XML children with no display_map option: {len(unmapped_tags)}")
    print(f"- display_map options absent from the sample XML: {len(missing_in_xml)}")
    print("\n## UI side")
    print(f"- Segments rendering >1 option (segment N:1): {len(seg_multi)}")
    print(f"- Options rendered in >1 segment (option 1:N segments): {len(opt_multi)}")
    print(f"- Segments no option claims: {len(seg_none)}")
    print(f"- Steps not found in the PDF: {len(no_pdf)}; unmatched PDF lines: {len(unmatched_lines)}")
    if summary_only:
        return

    def section(title, rows, fmt):
        print(f"\n### {title} ({len(rows)})")
        for r in rows:
            print("- " + fmt(r))

    section("Options sharing one XML element", opts_per_tag, lambda r: f"{r[0]}: <{r[1]}> -> {r[2]}")
    section("Options spanning several logical XML values", multi_leaf,
            lambda r: f"{r[0]} / {r[1]}: {r[3]}")
    section("Repeated top-level tags", repeated_tags, lambda r: f"{r[0]}: <{r[1]}> x{r[2]}")
    section("XML children without an option", unmapped_tags, lambda r: f"{r[0]}: <{r[1]}>")
    section("Options absent from the sample XML", missing_in_xml, lambda r: f"{r[0]}: {r[1]}")
    section("UI segments rendering several options", seg_multi, lambda r: f"{r[0]}: `{r[1]}` -> {r[2]}")
    section("Options rendered in several UI segments", opt_multi, lambda r: f"{r[0]} / {r[1]}: {r[2]}")
    section("UI segments no option claims", seg_none, lambda r: f"{r[0]} ({r[2]}): `{r[1]}`")
    section("Steps not found in the PDF", no_pdf, str)
    section("Unmatched PDF lines", unmatched_lines, str)


if __name__ == "__main__":
    main()
