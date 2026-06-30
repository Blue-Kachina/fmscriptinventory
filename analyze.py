#!/usr/bin/env python3
"""
FM Script Inventory
Parses a FileMaker fmxmlsnippet XML file and merges with a human-curated
display_map.yaml to produce inventory.json — a step definition map for
rendering FileMaker scripts in a UI.

Usage:
    pip install pyyaml python-slugify
    python3 analyze.py              # generate output/inventory.json
    python3 analyze.py --gen-stubs  # append display_map.yaml stubs for unmapped steps
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import yaml
from slugify import slugify

BASE_DIR = Path(__file__).parent
XML_PATH = BASE_DIR / "to_analyze" / "script.xml"
DISPLAY_MAP_PATH = BASE_DIR / "display_map.yaml"
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
    """Parse an fmxmlsnippet XML file; return list of {scriptName, steps} dicts.

    Handles both single-Script and multi-Script snippets.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()
    script_elems = root.findall("Script")
    if not script_elems:
        raise ValueError("No <Script> element found in fmxmlsnippet")
    result = []
    for script_elem in script_elems:
        script_name = script_elem.get("name", "")
        steps = []
        for idx, elem in enumerate(script_elem.findall("Step")):
            steps.append({
                "index": idx,
                "id": int(elem.get("id", 0)),
                "name": elem.get("name", ""),
                "enable": elem.get("enable", "True") == "True",
                "raw_xml": ET.tostring(elem, encoding="unicode"),
                "children": [_parse_child(c) for c in elem],
            })
        result.append({"scriptName": script_name, "steps": steps})
    return result


# ── Type / value helpers ──────────────────────────────────────────────────────

def normalize_name(name):
    return re.sub(r"\s+", " ", (name or "").strip())


def _option_key(tag):
    """Lowercase first letter of an XML tag to produce a camelCase option key."""
    return tag[0].lower() + tag[1:] if tag else tag


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
    # Elements with both @id and @name are named FM object references (Script, Layout, Field, etc.)
    if "id" in child["attrs"] and "name" in child["attrs"]:
        return "reference"
    return "unknown"


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


def _rebuild_child_xml(child):
    tag = child["tag"]
    attrs_str = "".join(f' {k}="{v}"' for k, v in child["attrs"].items())
    if not child["children"] and child["text"] is None:
        return f"<{tag}{attrs_str}/>"
    inner = (child["text"] or "") + "".join(_rebuild_child_xml(c) for c in child["children"])
    return f"<{tag}{attrs_str}>{inner}</{tag}>"


def _build_xml_template(xml_step):
    """Build a template string with {{placeholder}} slots for simple option attrs."""
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
    """Return one representative child per unique tag name (union across instances)."""
    seen = {}
    for children in all_children_lists:
        for child in children:
            if child["tag"] not in seen:
                seen[child["tag"]] = child
    return list(seen.values())


# ── Display map ───────────────────────────────────────────────────────────────

def load_display_map(path):
    """Load display_map.yaml; return dict keyed by stepId (int)."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []
    return {
        e["stepId"]: e
        for e in entries
        if isinstance(e, dict) and "stepId" in e
    }


def _stub_option_entry(child, ctype, enum_values=None):
    """Build a stub display_map option entry from a parsed XML child."""
    tag = child["tag"]
    key = _option_key(tag)
    if ctype == "boolean":
        xml_path = f"{tag}/@state" if "state" in child["attrs"] else f"{tag}/@value"
        return {
            "xmlPath": xml_path,
            "key": key,
            "type": "boolean",
            "label": None,
            "displayLocation": None,
            "omitWhenFalse": None,
            "trueText": None,
            "falseText": None,
        }
    elif ctype == "enum":
        return {
            "xmlPath": f"{tag}/@value",
            "key": key,
            "type": "enum",
            "label": None,
            "displayLocation": None,
            "allowedValues": [
                {"xmlValue": v, "displayText": None}
                for v in (enum_values or [])
            ],
        }
    elif ctype == "calculation":
        return {
            "xmlPath": f"{tag}/Calculation",
            "key": key,
            "type": "calculation",
            "label": None,
            "displayLocation": None,
        }
    elif ctype == "text":
        return {
            "xmlPath": f"{tag}/text()",
            "key": key,
            "type": "text",
            "label": None,
            "displayLocation": None,
        }
    elif ctype == "reference":
        return {
            "xmlPath": f"{tag}/@name",
            "key": key,
            "type": "reference",
            "label": None,
            "displayLocation": None,
        }
    else:
        return {
            "xmlPath": tag,
            "key": key,
            "type": ctype,
            "label": None,
            "displayLocation": None,
        }


def generate_display_map_stubs(definitions_by_id, all_steps_by_id, existing_map):
    """Return new stub entries for step IDs not yet in existing_map."""
    stubs = []
    for step_id in sorted(definitions_by_id.keys()):
        if step_id in existing_map:
            continue
        defn = definitions_by_id[step_id]
        step_list = all_steps_by_id.get(step_id, [])
        option_stubs = []
        for child in defn["_union_children"]:
            ctype = _infer_child_type(child)
            tag = child["tag"]
            enum_values = None
            if ctype == "enum":
                enum_values = sorted({
                    c["attrs"]["value"]
                    for step in step_list
                    for c in step["children"]
                    if c["tag"] == tag and "value" in c["attrs"]
                })
            option_stubs.append(_stub_option_entry(child, ctype, enum_values))
        stubs.append({
            "stepId": step_id,
            "stepName": defn["names"]["xml"],
            "displayName": None,
            "options": option_stubs,
        })
    return stubs


# ── Step definitions ──────────────────────────────────────────────────────────

def _find_dm_opt(map_entry, tag):
    """Return the display_map option entry matching this XML tag, or None."""
    if not map_entry:
        return None
    for o in (map_entry.get("options") or []):
        xml_path = o.get("xmlPath", "")
        if xml_path.split("/")[0] == tag:
            return o
    return None


def _build_option(child, map_entry, enum_values=None):
    """Build an option dict merging XML-inferred schema with display_map data."""
    tag = child["tag"]
    ctype = _infer_child_type(child)

    dm_opt = _find_dm_opt(map_entry, tag)

    # Prefer the semantic key from display_map; fall back to XML-tag-derived key
    key = (dm_opt or {}).get("key") or _option_key(tag)
    label = (dm_opt or {}).get("label") or tag
    display_location = (dm_opt or {}).get("displayLocation")

    opt = {
        "key": key,
        "label": label,
        "type": ctype,
        "source": {},
        "display": {
            "location": display_location or "unknown",
        },
    }

    if ctype == "boolean":
        xml_path = f"{tag}/@state" if "state" in child["attrs"] else f"{tag}/@value"
        opt["source"]["xmlPath"] = xml_path
        opt["allowedValues"] = [True, False]
        opt["default"] = False
        if dm_opt:
            if dm_opt.get("trueText") is not None:
                opt["display"]["trueText"] = dm_opt["trueText"]
            if dm_opt.get("falseText") is not None:
                opt["display"]["falseText"] = dm_opt["falseText"]
            if dm_opt.get("omitWhenFalse") is not None:
                opt["display"]["omitWhenFalse"] = dm_opt["omitWhenFalse"]
    elif ctype == "enum":
        opt["source"]["xmlPath"] = f"{tag}/@value"
        if dm_opt and dm_opt.get("allowedValues"):
            opt["allowedValues"] = dm_opt["allowedValues"]
        elif enum_values:
            opt["allowedValues"] = enum_values
    elif ctype == "text":
        opt["source"]["xmlPath"] = f"{tag}/text()"
    elif ctype == "calculation":
        opt["source"]["xmlPath"] = f"{tag}/Calculation"
    elif ctype == "object":
        opt["source"]["xmlPath"] = tag
    elif ctype == "reference":
        opt["source"]["xmlPath"] = f"{tag}/@name"

    return opt


def build_definitions(all_steps_by_id, display_map):
    """Group steps by fmStepId and build one definition per unique step type.

    Returns (definitions_list, definitions_by_id).
    definitions_by_id entries carry an internal '_union_children' key used
    by generate_display_map_stubs; it is stripped before JSON output.
    """
    definitions = []
    definitions_by_id = {}

    for step_id in sorted(all_steps_by_id.keys()):
        step_list = all_steps_by_id[step_id]
        representative = step_list[0]
        canonical_name = normalize_name(representative["name"])
        step_key = slugify(canonical_name) or f"step-{step_id}"

        union_children = _union_children([s["children"] for s in step_list])

        enum_values_by_tag = {}
        for child in union_children:
            if _infer_child_type(child) == "enum":
                enum_values_by_tag[child["tag"]] = sorted({
                    c["attrs"]["value"]
                    for step in step_list
                    for c in step["children"]
                    if c["tag"] == child["tag"] and "value" in c["attrs"]
                })

        map_entry = display_map.get(step_id)
        display_name = (map_entry or {}).get("displayName") or None

        observed_xmls = [{"xml": s["raw_xml"]} for s in step_list[:3]]

        options = [
            _build_option(c, map_entry, enum_values_by_tag.get(c["tag"]))
            for c in union_children
        ]

        # Build display.parts from options with known displayLocations
        parts = [{"type": "stepName", "value": display_name or canonical_name}]
        inline_items = [
            {"optionKey": o["key"], "label": o["label"]}
            for o in options if o["display"].get("location") == "inline"
        ]
        cont_items = [
            {"optionKey": o["key"], "label": o["label"]}
            for o in options if o["display"].get("location") == "continuation"
        ]
        if inline_items:
            parts.append({"type": "inlineOptions", "brackets": True, "items": inline_items})
        if cont_items:
            parts.append({"type": "continuationOptions", "brackets": True, "items": cont_items})

        defn = {
            "stepKey": step_key,
            "fmStepId": step_id,
            "names": {
                "xml": representative["name"],
                "display": display_name,
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
                "template": _build_xml_template(representative),
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
                    for c in union_children
                ],
                "observedExamples": observed_xmls,
            },
            "display": {
                "displayName": display_name,
                "parts": parts,
            },
            "options": options,
            "parameters": [],
            "validation": {
                "requiredOptions": [],
                "mutuallyExclusive": [],
                "dependencies": [],
            },
            "notes": [],
            "_union_children": union_children,
        }

        definitions.append(defn)
        definitions_by_id[step_id] = defn

    return definitions, definitions_by_id


# ── Script instances ──────────────────────────────────────────────────────────

def build_instances(scripts, definitions_by_id):
    """Build one instance record per step occurrence across all parsed scripts."""
    instances = []
    for script in scripts:
        script_slug = slugify(script["scriptName"]) or "script"
        for step in script["steps"]:
            defn = definitions_by_id.get(step["id"])
            # Map tag → option key so instance values align with definition option keys
            tag_to_key = {}
            if defn:
                for opt in defn["options"]:
                    src_path = opt.get("source", {}).get("xmlPath", "")
                    src_tag = src_path.split("/")[0] if src_path else ""
                    if src_tag:
                        tag_to_key[src_tag] = opt["key"]
            values = {
                tag_to_key.get(c["tag"], _option_key(c["tag"])): _to_typed_value(c)
                for c in step["children"]
            }
            instances.append({
                "instanceId": f"{script_slug}.step.{step['index']}",
                "scriptName": script["scriptName"],
                "stepIndex": step["index"],
                "enabled": step["enable"],
                "fmStepId": step["id"],
                "name": step["name"],
                "definitionKey": defn["stepKey"] if defn else None,
                "raw": {"xml": step["raw_xml"]},
                "values": values,
            })
    return instances


# ── Output ────────────────────────────────────────────────────────────────────

def emit_output(definitions, instances, scripts):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_defs = [{k: v for k, v in d.items() if not k.startswith("_")} for d in definitions]
    total_steps = sum(len(s["steps"]) for s in scripts)
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
                "scriptCount": len(scripts),
                "stepCount": total_steps,
            },
        },
        "stepDefinitions": clean_defs,
        "scriptInstances": instances,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return OUTPUT_PATH


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    gen_stubs = "--gen-stubs" in sys.argv

    print("Parsing XML …")
    scripts = parse_xml_steps(XML_PATH)
    total_steps = sum(len(s["steps"]) for s in scripts)
    print(f"  {len(scripts)} script(s), {total_steps} total steps")

    all_steps_by_id = defaultdict(list)
    for script in scripts:
        for step in script["steps"]:
            all_steps_by_id[step["id"]].append(step)
    print(f"  {len(all_steps_by_id)} unique step types")

    print("Loading display map …")
    display_map = load_display_map(DISPLAY_MAP_PATH)
    mapped = sum(1 for sid in all_steps_by_id if sid in display_map)
    print(f"  {mapped}/{len(all_steps_by_id)} step types have display map entries")

    print("Building definitions …")
    definitions, definitions_by_id = build_definitions(dict(all_steps_by_id), display_map)

    if gen_stubs:
        print("Generating display_map.yaml stubs …")
        stubs = generate_display_map_stubs(
            definitions_by_id, dict(all_steps_by_id), display_map
        )
        if stubs:
            mode = "a" if DISPLAY_MAP_PATH.exists() and DISPLAY_MAP_PATH.stat().st_size > 0 else "w"
            with open(DISPLAY_MAP_PATH, mode, encoding="utf-8") as f:
                if mode == "a":
                    f.write("\n")
                yaml.dump(
                    stubs, f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
            print(f"  Wrote {len(stubs)} stubs → {DISPLAY_MAP_PATH.name}")
        else:
            print("  All steps already mapped — nothing to stub")
        return

    print("Building instances …")
    instances = build_instances(scripts, definitions_by_id)

    print("Writing output …")
    out = emit_output(definitions, instances, scripts)
    print(f"  → {out}")

    unknown_count = sum(
        1 for d in definitions
        for o in d["options"]
        if o["display"].get("location") == "unknown"
    )
    if unknown_count:
        print(f"\n  {unknown_count} option(s) still have unknown display location.")
        print("  Run --gen-stubs to scaffold display_map.yaml entries.")


if __name__ == "__main__":
    main()
