#!/usr/bin/env python3
"""
Curate and export the FileMaker calculation catalogue (section 10 of database_structure_brainstorming.md).

    python3 calc_catalogue.py curate                 # apply calc_curated.yaml to catalogue.sqlite
    python3 calc_catalogue.py report                 # what still needs a human: signatures, types, constants
    python3 calc_catalogue.py export [--out PATH] [--allow-dirty] [--allow-unreviewed]

Run `scrape_help.py fetch/parse --scope calc` first. `export` runs `curate` itself, so curated facts are never
lost to a re-parse. The export follows fm-calc-catalogue/v1 (schemas/fm-calc-catalogue.schema.json, vendored
from FMCuttingBoard, which owns the contract). It carries facts and links only: help prose (purposes,
parameter descriptions, error texts) stays in the database.

Needs PyYAML (like analyze.py); jsonschema is optional and used for validation when installed.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

import scrape_help
from scrape_help import BASE_DIR, HELP_ROOT, connect

CURATED_PATH = BASE_DIR / "calc_curated.yaml"
SCHEMA_PATH = BASE_DIR / "schemas" / "fm-calc-catalogue.schema.json"
DEFAULT_OUT = BASE_DIR / "export" / "fm-calc-catalogue.json"
SCHEMA_VERSION = "fm-calc-catalogue/v1"
DATA_TYPES = {"text", "number", "date", "time", "timestamp", "container", "boolean", "json", "any", "expression",
              "fieldReference", "variableBindings"}


# ── curate ────────────────────────────────────────────────────────────────────

def load_curated():
    return yaml.safe_load(CURATED_PATH.read_text(encoding="utf8")) or {}


def curate(conn, curated, locale="en", quiet=False):
    """Apply calc_curated.yaml. Idempotent; returns a list of warnings."""
    warnings = []
    root = HELP_ROOT.format(locale=locale)
    apply_operators(conn, curated.get("operators", []), root, warnings)
    conn.execute("DELETE FROM calc_syntax_rules")
    for key, value in (curated.get("syntax") or {}).items():
        conn.execute("INSERT INTO calc_syntax_rules VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))
    apply_constants(conn, curated.get("constants", []), warnings)
    apply_functions(conn, curated.get("functions") or {}, root, locale, warnings)
    for code, label in (curated.get("errorLabels") or {}).items():
        if conn.execute("UPDATE error_codes SET label = ? WHERE code = ?", (label, int(code))).rowcount == 0:
            warnings.append(f"errorLabels: code {code} is not on the error codes page")
    for name, summary in (curated.get("getConstantSummaries") or {}).items():
        if conn.execute("UPDATE get_constant_localizations SET summary = ? WHERE locale = ? AND get_constant_id ="
                        " (SELECT id FROM get_constants WHERE name = ?)", (summary, locale, name)).rowcount == 0:
            warnings.append(f"getConstantSummaries: no Get constant {name}")
    conn.commit()
    if not quiet:
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
    return warnings


def apply_operators(conn, operators, root, warnings):
    conn.execute("DELETE FROM calc_operators")
    for op in operators:
        conn.execute(
            "INSERT INTO calc_operators (symbol, alternates, name, kind, arity, precedence, associativity, help_url)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (op["symbol"], json.dumps(op.get("alternates", []), ensure_ascii=False), op["name"], op["kind"],
             op["arity"], op["precedence"], op["associativity"], op.get("helpUrl")))
    # Cross-check the curated precedence against help's "Order of evaluation" list (tightest first).
    page = scrape_help.latest_page(conn, root + "operators-in-formulas.html")
    if not page:
        warnings.append("operators page not fetched; precedence not cross-checked")
        return
    level = {}
    for position, symbols in enumerate(scrape_help.parse_order_of_evaluation(page["raw_html"])):
        for symbol in symbols:
            level.setdefault(symbol.lower(), position)
    ranked = []
    for op in operators:
        spellings = [op["symbol"], *op.get("alternates", [])]
        found = [level[s.lower()] for s in spellings if s.lower() in level]
        if not found:
            warnings.append(f"operator {op['symbol']!r} is not in help's order of evaluation")
        else:
            ranked.append((op["symbol"], found[0], op["precedence"]))
    for a_symbol, a_level, a_prec in ranked:
        for b_symbol, b_level, b_prec in ranked:
            if a_level < b_level and not a_prec > b_prec or a_level == b_level and a_prec != b_prec:
                warnings.append(f"precedence of {a_symbol!r} vs {b_symbol!r} disagrees with help's order of evaluation")


def apply_constants(conn, constants, warnings):
    for const in constants:
        row = conn.execute("SELECT id FROM calc_constants WHERE name = ?", (const["name"],)).fetchone()
        if not row:
            warnings.append(f"constant {const['name']} is not on the named constants page; added from curation")
            conn.execute("INSERT INTO calc_constants (name, group_key) VALUES (?, ?)",
                         (const["name"], const.get("group", "other")))
        since = (const.get("lifecycle") or {}).get("since")
        conn.execute(
            "UPDATE calc_constants SET group_key = COALESCE(?, group_key), value_json = ?, help_url = ?,"
            " originated_in_version_id = ? WHERE name = ?",
            (const.get("group"), json.dumps(const["value"]) if "value" in const else None, const.get("helpUrl"),
             scrape_help.get_or_create_version(conn, since) if since else None, const["name"]))


def apply_functions(conn, functions, root, locale, warnings):
    for name, spec in functions.items():
        row = conn.execute("SELECT id FROM functions WHERE name = ?", (name,)).fetchone()
        if not row:
            if "signature" not in spec:
                warnings.append(f"functions: {name} is not on the help site and has no curated signature")
                continue
            conn.execute("INSERT INTO functions (name, signature, signature_status) VALUES (?, ?, 'curated')",
                         (name, spec["signature"]))
            row = conn.execute("SELECT id FROM functions WHERE name = ?", (name,)).fetchone()
        function_id = row["id"]
        updates = {}
        for key, column in (("minArgs", "min_args"), ("maxArgs", "max_args"), ("returnType", "return_type"),
                            ("signature", "signature")):
            if key in spec:
                updates[column] = spec[key]
        if "category" in spec:
            cat = conn.execute("SELECT id FROM function_categories WHERE key = ?", (spec["category"],)).fetchone()
            if cat:
                updates["category_id"] = cat["id"]
            else:
                warnings.append(f"functions: {name}: unknown category {spec['category']!r}")
        lifecycle = spec.get("lifecycle") or {}
        if "since" in lifecycle:
            updates["originated_in_version_id"] = scrape_help.get_or_create_version(conn, lifecycle["since"])
            updates["originated_in_raw"] = lifecycle.get("sinceRaw", lifecycle["since"])
        if {"minArgs", "maxArgs", "parameters"} & spec.keys():
            updates["signature_status"] = "curated"
        if updates:
            conn.execute(f"UPDATE functions SET {', '.join(f'{c} = ?' for c in updates)} WHERE id = ?",
                         (*updates.values(), function_id))
        if "parameters" in spec:
            replace_parameters(conn, function_id, name, spec["parameters"], warnings)
        for param_name, param_type in (spec.get("parameterTypes") or {}).items():
            check_type(param_type, f"{name}.{param_name}", warnings)
            if conn.execute("UPDATE function_parameters SET type = ?, type_source = 'curated'"
                            " WHERE function_id = ? AND name = ?", (param_type, function_id, param_name)).rowcount == 0:
                warnings.append(f"functions: {name} has no parameter {param_name}")
        for param_name, allowed in (spec.get("allowedConstants") or {}).items():
            link_constants(conn, function_id, name, param_name, allowed, warnings)
        if "summary" in spec or "helpPage" in spec:
            page = scrape_help.latest_page(conn, root + spec["helpPage"]) if "helpPage" in spec else None
            conn.execute(
                "INSERT INTO function_localizations (function_id, locale, summary, help_page_id) VALUES (?, ?, ?, ?)"
                " ON CONFLICT (function_id, locale) DO UPDATE SET summary = COALESCE(excluded.summary, summary),"
                " help_page_id = COALESCE(excluded.help_page_id, help_page_id)",
                (function_id, locale, spec.get("summary"), page["id"] if page else None))


def replace_parameters(conn, function_id, function_name, parameters, warnings):
    old = {r["name"]: r["help_description"] for r in conn.execute(
        "SELECT name, help_description FROM function_parameters WHERE function_id = ?", (function_id,))}
    conn.execute("DELETE FROM function_parameter_constants WHERE parameter_id IN"
                 " (SELECT id FROM function_parameters WHERE function_id = ?)", (function_id,))
    conn.execute("DELETE FROM function_parameters WHERE function_id = ?", (function_id,))
    for position, param in enumerate(parameters):
        check_type(param["type"], f"{function_name}.{param['name']}", warnings)
        conn.execute(
            "INSERT INTO function_parameters (function_id, position, name, type, type_source, optional, repeatable,"
            " group_key, help_description) VALUES (?, ?, ?, ?, 'curated', ?, ?, ?, ?)",
            (function_id, position, param["name"], param["type"], param.get("optional", False),
             param.get("repeatable", False), param.get("group"), old.get(param["name"])))
        if "allowedConstants" in param:
            link_constants(conn, function_id, function_name, param["name"], param["allowedConstants"], warnings)


def link_constants(conn, function_id, function_name, param_name, allowed, warnings):
    """allowed is a list of constant names, or {group: 'json-type'}."""
    param = conn.execute("SELECT id FROM function_parameters WHERE function_id = ? AND name = ?",
                         (function_id, param_name)).fetchone()
    if not param:
        warnings.append(f"allowedConstants: {function_name} has no parameter {param_name}")
        return
    if isinstance(allowed, dict):
        rows = conn.execute("SELECT id FROM calc_constants WHERE group_key = ?", (allowed["group"],)).fetchall()
    else:
        rows = conn.execute(f"SELECT id FROM calc_constants WHERE name IN ({','.join('?' * len(allowed))})",
                            allowed).fetchall()
    if not rows:
        warnings.append(f"allowedConstants: nothing matches {allowed!r} for {function_name}.{param_name}")
    conn.execute("DELETE FROM function_parameter_constants WHERE parameter_id = ?", (param["id"],))
    for row in rows:
        conn.execute("INSERT INTO function_parameter_constants VALUES (?, ?)", (param["id"], row["id"]))


def check_type(type_name, where, warnings):
    if type_name not in DATA_TYPES:
        warnings.append(f"{where}: {type_name!r} is not a fm-calc-catalogue dataType")


def cmd_curate(_args):
    conn = connect()
    warnings = curate(conn, load_curated())
    print(f"curated ({len(warnings)} warnings)")


# ── report ────────────────────────────────────────────────────────────────────

def cmd_report(_args):
    conn = connect()
    warnings = curate(conn, load_curated(), quiet=True)
    rows = conn.execute("SELECT name, signature, signature_issues FROM functions"
                        " WHERE signature_status = 'needs-review' ORDER BY name").fetchall()
    print(f"functions needing signature review: {len(rows)}")
    for r in rows:
        print(f"  {r['name']:24} {r['signature']}\n  {'':24} -> {r['signature_issues']}")
    for label, sql in (
            ("functions without a return type", "SELECT name FROM functions WHERE return_type IS NULL"),
            ("functions without an originated-in version",
             "SELECT name FROM functions WHERE originated_in_version_id IS NULL"),
            ("Get constants without a return type", "SELECT name FROM get_constants WHERE return_type IS NULL"),
            ("Get constants without an originated-in version",
             "SELECT name FROM get_constants WHERE originated_in_version_id IS NULL"),
            ("constants without a curated value", "SELECT name FROM calc_constants WHERE value_json IS NULL")):
        names = [r[0] for r in conn.execute(sql + " ORDER BY 1")]
        print(f"\n{label}: {len(names)}")
        if names:
            print("  " + ", ".join(names))
    print("\nparameter types by source:")
    for r in conn.execute("SELECT type_source, type, COUNT(*) n FROM function_parameters"
                          " GROUP BY type_source, type ORDER BY type_source, n DESC"):
        print(f"  {r['type_source']:9} {r['type']:16} {r['n']}")
    print(f"\ncuration warnings: {len(warnings)}")
    for warning in warnings:
        print(f"  {warning}")


# ── export ────────────────────────────────────────────────────────────────────

def git(*args):
    return subprocess.run(["git", *args], cwd=BASE_DIR, capture_output=True, text=True, check=True).stdout.strip()


def generator_info():
    remote = git("remote", "get-url", "origin")
    repo = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", remote)
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    return {"repo": repo.group(1) if repo else remote, "commit": git("rev-parse", "HEAD"), "dirty": dirty}


def lifecycle(conn, version_id, raw, deprecated_id=None, removed_id=None):
    if version_id is None:
        return None
    versions = dict(conn.execute("SELECT id, version FROM fm_versions"))
    result = {"since": versions[version_id]}
    if raw and raw != result["since"]:
        result["sinceRaw"] = raw
    if deprecated_id:
        result["deprecatedIn"] = versions[deprecated_id]
    if removed_id:
        result["removedIn"] = versions[removed_id]
    return result


def compatibility(conn, table, key_column, key):
    rows = conn.execute(f"SELECT product, supported FROM {table} WHERE {key_column} = ? ORDER BY product", (key,))
    return {r["product"]: r["supported"] for r in rows}


def build_export(conn, curated, locale, allow_unreviewed):
    problems = []
    help_url = dict(conn.execute("SELECT id, url FROM help_pages"))

    categories = [
        {"key": r["key"], "label": r["name"], "helpUrl": help_url[r["help_page_id"]]}
        for r in conn.execute(
            "SELECT c.key, l.name, l.help_page_id FROM function_categories c JOIN function_category_localizations l"
            " ON l.category_id = c.id AND l.locale = ? ORDER BY c.position", (locale,))]

    functions = []
    for f in conn.execute(
            "SELECT f.*, c.key AS category, l.summary, l.help_page_id FROM functions f"
            " LEFT JOIN function_categories c ON c.id = f.category_id"
            " LEFT JOIN function_localizations l ON l.function_id = f.id AND l.locale = ?", (locale,)):
        if f["signature_status"] == "needs-review" and not allow_unreviewed:
            problems.append(f"{f['name']}: signature needs review ({f['signature_issues']})")
            continue
        life = lifecycle(conn, f["originated_in_version_id"], f["originated_in_raw"],
                         f["deprecated_in_version_id"], f["removed_in_version_id"])
        missing = [what for what, value in (("category", f["category"]), ("return type", f["return_type"]),
                                            ("min args", f["min_args"]), ("version", life),
                                            ("help page", f["help_page_id"])) if value is None]
        if missing:
            problems.append(f"{f['name']}: no {', '.join(missing)}")
            continue
        params = []
        for p in conn.execute("SELECT * FROM function_parameters WHERE function_id = ? ORDER BY position", (f["id"],)):
            param = {"name": p["name"], "type": p["type"], "optional": bool(p["optional"]),
                     "repeatable": bool(p["repeatable"])}
            if p["group_key"]:
                param["group"] = p["group_key"]
            allowed = [r[0] for r in conn.execute(
                "SELECT c.name FROM function_parameter_constants pc JOIN calc_constants c ON c.id = pc.constant_id"
                " WHERE pc.parameter_id = ? ORDER BY c.name", (p["id"],))]
            if allowed:
                param["allowedConstants"] = allowed
            params.append(param)
        entry = {"name": f["name"], "category": f["category"], "returnType": f["return_type"], "parameters": params,
                 "minArgs": f["min_args"], "maxArgs": f["max_args"], "signature": f["signature"],
                 "lifecycle": life}
        compat = compatibility(conn, "function_compatibility", "function_id", f["id"])
        if compat:
            entry["compatibility"] = compat
        entry["helpUrl"] = help_url[f["help_page_id"]]
        if f["summary"]:
            entry["summary"] = f["summary"]
        verified = verification(conn, f["id"], f["min_args"], f["max_args"])
        if verified:
            entry["verified"] = verified
        functions.append(entry)
    functions.sort(key=lambda e: (e["name"].lower(), e["name"]))

    get_constants = []
    for g in conn.execute(
            "SELECT g.*, l.summary, l.help_page_id FROM get_constants g"
            " LEFT JOIN get_constant_localizations l ON l.get_constant_id = g.id AND l.locale = ?", (locale,)):
        life = lifecycle(conn, g["originated_in_version_id"], g["originated_in_raw"],
                         g["deprecated_in_version_id"], g["removed_in_version_id"])
        if life is None:
            problems.append(f"Get ( {g['name']} ): no originated-in version")
            continue
        entry = {"name": g["name"], "returnType": g["return_type"] or "any", "lifecycle": life}
        compat = compatibility(conn, "get_constant_compatibility", "get_constant_id", g["id"])
        if compat:
            entry["compatibility"] = compat
        entry["helpUrl"] = help_url[g["help_page_id"]]
        if g["summary"]:
            entry["summary"] = g["summary"]
        get_constants.append(entry)
    get_constants.sort(key=lambda e: (e["name"].lower(), e["name"]))

    constants = []
    for c in conn.execute("SELECT * FROM calc_constants ORDER BY lower(name), name"):
        entry = {"name": c["name"], "group": c["group_key"],
                 "value": json.loads(c["value_json"]) if c["value_json"] is not None else None}
        life = lifecycle(conn, c["originated_in_version_id"], None)
        if life:
            entry["lifecycle"] = life
        url = c["help_url"] or help_url.get(c["help_page_id"])
        if url:
            entry["helpUrl"] = url
        constants.append(entry)

    operators = []
    for o in conn.execute("SELECT * FROM calc_operators ORDER BY precedence DESC, symbol"):
        entry = {"symbol": o["symbol"]}
        if json.loads(o["alternates"]):
            entry["alternates"] = json.loads(o["alternates"])
        entry.update(name=o["name"], kind=o["kind"], arity=o["arity"], precedence=o["precedence"],
                     associativity=o["associativity"])
        if o["help_url"]:
            entry["helpUrl"] = o["help_url"]
        operators.append(entry)

    syntax = {r["key"]: json.loads(r["value_json"]) for r in conn.execute("SELECT * FROM calc_syntax_rules")}
    error_codes = [{"code": r["code"], "label": r["label"], "helpUrl": help_url[r["help_page_id"]]}
                   for r in conn.execute("SELECT * FROM error_codes WHERE label IS NOT NULL ORDER BY code")]

    documented = curated.get("documentedFileMakerVersion") or conn.execute(
        "SELECT v.version FROM fm_versions v WHERE v.id IN (SELECT originated_in_version_id FROM functions"
        " UNION SELECT originated_in_version_id FROM get_constants) ORDER BY v.sort_key DESC LIMIT 1").fetchone()[0]
    catalogue = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": generator_info(),
        "locale": locale,
        "documentedFileMakerVersion": documented,
        "categories": categories,
        "functions": functions,
        "getConstants": get_constants,
        "constants": constants,
        "operators": operators,
        "syntax": syntax,
    }
    if error_codes:
        catalogue["errorCodes"] = error_codes
    return catalogue, problems


def verification(conn, function_id, min_args, max_args):
    """'verified' from function_verifications, for the newest FM version that has observations."""
    rows = conn.execute(
        "SELECT v.version, fv.arg_count, fv.is_valid FROM function_verifications fv"
        " JOIN fm_versions v ON v.id = fv.fm_version_id WHERE fv.function_id = ? ORDER BY v.sort_key DESC",
        (function_id,)).fetchall()
    if not rows:
        return None
    version = rows[0]["version"]
    valid = {r["arg_count"]: bool(r["is_valid"]) for r in rows if r["version"] == version}
    min_ok = valid.get(min_args) is True and (min_args == 0 or valid.get(min_args - 1) is False)
    if max_args is None:
        max_ok = valid.get(min_args + 1, True) is not False
    else:
        max_ok = valid.get(max_args) is True and valid.get(max_args + 1) is False
    return {"fileMakerVersion": version, "minArgs": min_ok, "maxArgs": max_ok}


def validate(catalogue):
    try:
        import jsonschema
    except ImportError:
        print("note: jsonschema is not installed; validate with"
              f" `npx --yes ajv-cli@5.0.0 validate --spec=draft7 -s {SCHEMA_PATH.relative_to(BASE_DIR)} -d <export>`")
        return True
    errors = sorted(jsonschema.Draft7Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf8")))
                    .iter_errors(catalogue), key=lambda e: list(e.path))
    for error in errors[:20]:
        print(f"schema: {'/'.join(map(str, error.path))}: {error.message}", file=sys.stderr)
    return not errors


def cmd_export(args):
    conn = connect()
    curated = load_curated()
    curate(conn, curated)
    catalogue, problems = build_export(conn, curated, "en", args.allow_unreviewed)
    for problem in problems:
        print(f"left out: {problem}", file=sys.stderr)
    if catalogue["generator"]["dirty"] and not args.allow_dirty:
        sys.exit("working tree has uncommitted changes; commit first (FMCuttingBoard rejects dirty exports),"
                 " or pass --allow-dirty for a local preview")
    if not validate(catalogue):
        sys.exit("export does not match the schema; nothing written")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"wrote {out}: {len(catalogue['functions'])} functions, {len(catalogue['getConstants'])} Get constants,"
          f" {len(catalogue['constants'])} constants, {len(catalogue['operators'])} operators,"
          f" {len(catalogue.get('errorCodes', []))} error codes ({len(problems)} left out)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("curate").set_defaults(func=cmd_curate)
    sub.add_parser("report").set_defaults(func=cmd_report)
    export = sub.add_parser("export")
    export.add_argument("--out", default=str(DEFAULT_OUT))
    export.add_argument("--allow-dirty", action="store_true", help="export from uncommitted changes (marked dirty)")
    export.add_argument("--allow-unreviewed", action="store_true",
                        help="include functions whose signature still needs review")
    export.set_defaults(func=cmd_export)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
