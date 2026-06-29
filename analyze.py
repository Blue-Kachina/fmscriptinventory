#!/usr/bin/env python3
"""
FM Script Inventory
Correlates a FileMaker "OneOfEverything" script XML export with its PDF
printed representation, producing a JSON catalog of step definitions and
script instances.

Usage:
    pip install pdfplumber
    python3 analyze.py
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pdfplumber
from slugify import slugify

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
XML_PATH = BASE_DIR / "to_analyze" / "script.xml"
PDF_PATH = BASE_DIR / "to_analyze" / "script.pdf"
OUTPUT_PATH = BASE_DIR / "output" / "inventory.json"

# ── XML parsing ───────────────────────────────────────────────────────────────

def _parse_child(elem):
    return {
        "tag": elem.tag,
        "attrs": dict(elem.attrib),
        "text": (elem.text or "").strip() or None,
        "children": [_parse_child(c) for c in elem],
    }


def parse_xml_steps(path):
    """Return a list of step dicts from an fmxmlsnippet XML file."""
    tree = ET.parse(str(path))
    root = tree.getroot()
    script = root.find("Script")
    if script is None:
        raise ValueError("No <Script> element found in fmxmlsnippet")
    steps = []
    for idx, elem in enumerate(script.findall("Step")):
        steps.append({
            "index": idx,
            "id": int(elem.get("id", 0)),
            "name": elem.get("name", ""),
            "enable": elem.get("enable", "True") == "True",
            "raw_xml": ET.tostring(elem, encoding="unicode"),
            "children": [_parse_child(c) for c in elem],
        })
    return steps

# ── PDF parsing ───────────────────────────────────────────────────────────────

_HEADER_RE = re.compile(r"^OneOfEverything$")
_FOOTER_RE = re.compile(r"EverythingBagel")
_CONT_RE = re.compile(r"^\[")
_INLINE_RE = re.compile(r"^(.*?)(\[.*\])\s*$")


def extract_pdf_lines(path):
    """
    Return (is_continuation, text) pairs for every content line in the PDF,
    filtering out per-page headers and footers.
    """
    lines = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for raw in text.split("\n"):
                line = raw.strip()
                if not line:
                    continue
                if _HEADER_RE.match(line) or _FOOTER_RE.search(line):
                    continue
                lines.append((bool(_CONT_RE.match(line)), line))
    return lines


def parse_pdf_steps(lines):
    """
    Group (is_continuation, text) pairs into printed step dicts.

    A step starts on any non-continuation line. Subsequent lines that start
    with '[' belong to that step as continuation option lines.
    """
    steps = []
    current = None
    for is_cont, text in lines:
        if is_cont:
            if current is not None:
                current["continuation_lines"].append(text)
                current["raw_lines"].append(text)
        else:
            if current is not None:
                steps.append(current)
            m = _INLINE_RE.match(text)
            name_part = m.group(1).strip() if m else text
            inline_part = m.group(2) if m else None
            current = {
                "index": len(steps),
                "name": name_part,
                "inline_options": inline_part,
                "continuation_lines": [],
                "raw_lines": [text],
            }
    if current is not None:
        steps.append(current)
    return steps

# ── Name matching helpers ─────────────────────────────────────────────────────

def normalize_name(name):
    return re.sub(r"\s+", " ", (name or "").strip())


def _is_empty_comment(xml_step):
    """True if this is id=89 with no text content — not printed in PDF."""
    if xml_step["id"] != 89:
        return False
    text_child = next((c for c in xml_step["children"] if c["tag"] == "Text"), None)
    return text_child is None or not (text_child.get("text") or "").strip()


def _pdf_name_for_comment(xml_step):
    """Expected PDF step name for a non-empty # (comment) step."""
    text_child = next((c for c in xml_step["children"] if c["tag"] == "Text"), None)
    text = (text_child.get("text") or "") if text_child else ""
    return f"#{text.strip()}" if text.strip() else "#"


def _steps_match(xml_step, pdf_step):
    """Return (confidence, notes) for a candidate pair."""
    xml_name = normalize_name(xml_step["name"])
    pdf_name = normalize_name(pdf_step["name"])

    if xml_step["id"] == 89:
        expected = normalize_name(_pdf_name_for_comment(xml_step))
        if pdf_name == expected or pdf_name.startswith("#"):
            return 1.0, []
        return 0.5, [f"Comment name mismatch: expected {expected!r}, got {pdf_name!r}"]

    if xml_name == pdf_name:
        return 1.0, []

    return 0.5, [f"Name mismatch: xml={xml_name!r} pdf={pdf_name!r}"]

# ── Sequential matching ───────────────────────────────────────────────────────

def match_steps(xml_steps, pdf_steps):
    """
    Walk both lists in parallel by position (sequential matching).

    Empty # (comment) steps are skipped in the PDF — they create visual
    spacing but produce no printed line. Steps with no PDF counterpart
    (e.g. PDF truncated before XML ends) receive confidence 0.0.
    """
    matches = []
    pdf_idx = 0
    for xml_step in xml_steps:
        if _is_empty_comment(xml_step):
            matches.append({
                "xml": xml_step,
                "printed": None,
                "confidence": 0.9,
                "notes": ["Empty comment step — not rendered in printed PDF"],
            })
            continue

        if pdf_idx >= len(pdf_steps):
            matches.append({
                "xml": xml_step,
                "printed": None,
                "confidence": 0.0,
                "notes": ["No corresponding printed step — PDF may be truncated"],
            })
            continue

        pdf_step = pdf_steps[pdf_idx]
        confidence, notes = _steps_match(xml_step, pdf_step)
        matches.append({
            "xml": xml_step,
            "printed": pdf_step,
            "confidence": confidence,
            "notes": notes,
        })
        pdf_idx += 1

    return matches

# ── Value extraction ──────────────────────────────────────────────────────────

def _to_typed_value(child):
    """Convert a parsed child element to a typed Python value (best-effort)."""
    if not child["children"] and child["text"] is None:
        if "state" in child["attrs"]:
            return child["attrs"]["state"] == "True"
        elif "value" in child["attrs"]:
            val = child["attrs"]["value"]
            if val in ("True", "False"):
                return val == "True"
            return val
        elif child["attrs"]:
            return dict(child["attrs"])
        return None
    elif child["text"] is not None and not child["children"]:
        return child["text"]
    else:
        result = {}
        if child["attrs"]:
            result.update(child["attrs"])
        if child["text"]:
            result["_text"] = child["text"]
        for c in child["children"]:
            result[c["tag"]] = _to_typed_value(c)
        return result

# ── Script instances ──────────────────────────────────────────────────────────

def build_instances(matches):
    """Build the scriptInstances list from matched steps."""
    instances = []
    for match in matches:
        xml_step = match["xml"]
        printed = match["printed"]
        values = {c["tag"]: _to_typed_value(c) for c in xml_step["children"]}
        instances.append({
            "instanceId": f"oneofeverything.step.{xml_step['index']}",
            "stepIndex": xml_step["index"],
            "enabled": xml_step["enable"],
            "fmStepId": xml_step["id"],
            "name": xml_step["name"],
            "raw": {
                "xml": xml_step["raw_xml"],
                "printedLines": printed["raw_lines"] if printed else [],
            },
            "values": values,
            "mapping": {
                "matchStrategy": "sequential-name-normalized",
                "confidence": match["confidence"],
                "notes": match["notes"],
            },
        })
    return instances

# ── Step definitions ──────────────────────────────────────────────────────────

def _infer_child_type(child):
    if "state" in child["attrs"]:
        return "boolean"
    if "value" in child["attrs"]:
        val = child["attrs"]["value"]
        return "boolean" if val in ("True", "False") else "enum"
    if any(c["tag"] == "Calculation" for c in child["children"]):
        return "calculation"
    if child["children"]:
        return "object"
    if child["text"] is not None:
        return "text"
    return "unknown"


def _option_key(tag):
    """Lowercase first letter of an XML tag to get a camelCase option key."""
    return tag[0].lower() + tag[1:] if tag else tag


def _rebuild_child_xml(child):
    """Reconstruct a compact XML string for a child element."""
    tag = child["tag"]
    attrs_str = "".join(f' {k}="{v}"' for k, v in child["attrs"].items())
    if not child["children"] and child["text"] is None:
        return f"<{tag}{attrs_str}/>"
    inner = (child["text"] or "") + "".join(_rebuild_child_xml(c) for c in child["children"])
    return f"<{tag}{attrs_str}>{inner}</{tag}>"


def _build_xml_template(xml_step):
    """Build a template string with {{placeholder}} variables for simple attrs."""
    parts = []
    for child in xml_step["children"]:
        tag = child["tag"]
        key = _option_key(tag)
        if "state" in child["attrs"] and not child["children"] and child["text"] is None:
            parts.append(f'<{tag} state="{{{{{key}State}}}}"/>')
        elif "value" in child["attrs"] and not child["children"] and child["text"] is None:
            parts.append(f'<{tag} value="{{{{{key}Value}}}}"/>')
        else:
            parts.append(_rebuild_child_xml(child))
    inner = "".join(parts)
    name_escaped = xml_step["name"].replace('"', "&quot;")
    return f'<Step enable="{{{{enabled}}}}" id="{xml_step["id"]}" name="{name_escaped}">{inner}</Step>'


def _union_children(all_children_lists):
    """Return one child schema per unique tag name (union across instances)."""
    seen = {}
    for children in all_children_lists:
        for child in children:
            if child["tag"] not in seen:
                seen[child["tag"]] = child
    return list(seen.values())


def _gather_enum_values(step_matches, tag):
    values = set()
    for m in step_matches:
        for c in m["xml"]["children"]:
            if c["tag"] == tag and "value" in c["attrs"]:
                values.add(c["attrs"]["value"])
    return sorted(values)


def _build_option(child, step_matches):
    tag = child["tag"]
    key = _option_key(tag)
    ctype = _infer_child_type(child)

    opt = {
        "key": key,
        "label": tag,
        "type": ctype,
        "source": {},
        "display": {
            "location": "unknown",
            "inferenceConfidence": "low",
        },
    }

    if ctype == "boolean" and "state" in child["attrs"]:
        opt["source"]["xmlPath"] = f"{tag}/@state"
        opt["allowedValues"] = [True, False]
        opt["default"] = False
    elif ctype == "boolean" and "value" in child["attrs"]:
        opt["source"]["xmlPath"] = f"{tag}/@value"
        opt["allowedValues"] = [True, False]
    elif ctype == "enum":
        opt["source"]["xmlPath"] = f"{tag}/@value"
        opt["allowedValues"] = _gather_enum_values(step_matches, tag)
    elif ctype == "text":
        opt["source"]["xmlPath"] = f"{tag}/text()"
    elif ctype == "calculation":
        opt["source"]["xmlPath"] = f"{tag}/Calculation"
    elif ctype == "object":
        opt["source"]["xmlPath"] = tag

    return opt


def build_definitions(matches):
    """Build stepDefinitions by grouping matched steps by fmStepId."""
    by_id = defaultdict(list)
    for m in matches:
        by_id[m["xml"]["id"]].append(m)

    definitions = []
    for step_id, step_matches in sorted(by_id.items()):
        xml_step = step_matches[0]["xml"]
        canonical_name = normalize_name(xml_step["name"])
        step_key = slugify(canonical_name) or f"step-{step_id}"

        children = _union_children([m["xml"]["children"] for m in step_matches])
        printed_steps = [m["printed"] for m in step_matches if m["printed"] is not None]

        observed_xmls = [{"xml": m["xml"]["raw_xml"]} for m in step_matches[:3]]
        observed_printed = []
        for ps in printed_steps:
            observed_printed.extend(ps["raw_lines"])

        printed_name = normalize_name(printed_steps[0]["name"]) if printed_steps else None

        # Display parts — structured breakdown of the first observed printed step
        display_parts = []
        if printed_steps:
            ps = printed_steps[0]
            display_parts.append({"type": "stepName", "value": canonical_name})
            if ps["inline_options"] is not None:
                display_parts.append({
                    "type": "inlineOptions",
                    "brackets": True,
                    "value": ps["inline_options"],
                })
            for cl in ps["continuation_lines"]:
                display_parts.append({
                    "type": "continuationOptions",
                    "brackets": True,
                    "value": cl,
                })

        definitions.append({
            "stepKey": step_key,
            "fmStepId": step_id,
            "names": {
                "xml": xml_step["name"],
                "printed": printed_name,
                "canonical": canonical_name,
                "aliases": [],
            },
            "kind": {
                "category": None,
                "controlFlowRole": None,
                "isContainerStep": False,
                "isTerminatorStep": False,
            },
            "xml": {
                "stepAttributes": {
                    "enable": {"type": "boolean", "xmlAttribute": "@enable", "default": True},
                    "id": {"type": "integer", "xmlAttribute": "@id"},
                    "name": {"type": "string", "xmlAttribute": "@name"},
                },
                "template": _build_xml_template(xml_step),
                "children": [
                    {
                        "path": c["tag"],
                        "type": _infer_child_type(c),
                        "attributes": {
                            k: {"observed": v} for k, v in c["attrs"].items()
                        },
                        "hasText": c["text"] is not None,
                        "hasChildren": bool(c["children"]),
                    }
                    for c in children
                ],
                "observedExamples": observed_xmls,
            },
            "display": {
                "printedTemplate": None,
                "parts": display_parts,
                "observedPrinted": observed_printed,
            },
            "options": [_build_option(c, step_matches) for c in children],
            "parameters": [],
            "validation": {
                "requiredOptions": [],
                "mutuallyExclusive": [],
                "dependencies": [],
            },
            "mapping": {
                "matchStrategy": "sequential-name-normalized",
                "confidence": min(m["confidence"] for m in step_matches),
                "instanceCount": len(step_matches),
                "notes": [],
            },
            "notes": [],
        })

    return definitions

# ── Output ────────────────────────────────────────────────────────────────────

def emit_output(definitions, instances, xml_steps, pdf_steps):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": "fm-script-step-inventory/v1",
        "fileMaker": {
            "product": "FileMaker Pro",
            "sourceVersion": None,
            "locale": "en",
            "platform": None,
        },
        "sources": {
            "xml": {
                "type": "clipboard-fmxmlsnippet",
                "file": str(XML_PATH.relative_to(BASE_DIR)),
                "stepCount": len(xml_steps),
            },
            "printed": {
                "type": "script-print-pdf",
                "file": str(PDF_PATH.relative_to(BASE_DIR)),
                "stepCount": len(pdf_steps),
            },
        },
        "stepDefinitions": definitions,
        "scriptInstances": instances,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return OUTPUT_PATH

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Parsing XML …")
    xml_steps = parse_xml_steps(XML_PATH)
    print(f"  {len(xml_steps)} steps")

    print("Extracting PDF text …")
    pdf_lines = extract_pdf_lines(PDF_PATH)
    pdf_steps = parse_pdf_steps(pdf_lines)
    print(f"  {len(pdf_steps)} printed steps")

    print("Matching …")
    matches = match_steps(xml_steps, pdf_steps)

    conf_bins: dict[str, int] = defaultdict(int)
    for m in matches:
        c = m["confidence"]
        label = "1.0" if c == 1.0 else ("0.9" if c >= 0.9 else ("0.5" if c >= 0.5 else "0.0"))
        conf_bins[label] += 1
    print(f"  Confidence distribution: {dict(sorted(conf_bins.items(), reverse=True))}")

    low = [m for m in matches if 0.0 < m["confidence"] < 1.0 and m["printed"] is not None]
    if low:
        print("  Low-confidence matches:")
        for m in low:
            print(f"    [{m['confidence']}] {m['xml']['name']!r}: {m['notes']}")

    no_pdf = [m for m in matches if m["printed"] is None and m["confidence"] == 0.0]
    if no_pdf:
        print(f"  {len(no_pdf)} XML steps have no printed counterpart (PDF truncated):")
        for m in no_pdf:
            print(f"    {m['xml']['name']!r}")

    print("Building definitions …")
    definitions = build_definitions(matches)
    print(f"  {len(definitions)} unique step types")

    print("Building instances …")
    instances = build_instances(matches)

    print("Writing output …")
    out = emit_output(definitions, instances, xml_steps, pdf_steps)
    print(f"  → {out}")


if __name__ == "__main__":
    main()
