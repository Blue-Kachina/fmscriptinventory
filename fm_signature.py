"""
Parse a help page's Format line into structured parameters and argument counts.

    parse("Case ( test1 ; result1 {; test2 ; result2 ; ... ; defaultResult } )")
    -> name 'Case', min_args 2, max_args None,
       params test (repeatable, group 'test-result'), result (repeatable, same group), defaultResult (optional)

Help's notation: `;` separates arguments, `{ }` marks optional parts, `...` marks repetition, and numbered names
(`test1`, `test2`) are instances of one repeating parameter. Anything else (`[ ]` blocks, `name = value`
bindings, unbalanced braces) is reported in `issues`; such functions get their parameters from
calc_curated.yaml instead.

Standard library only, no database access, so it can be tested on its own.
"""

import re
from dataclasses import dataclass, field

NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.]*")
PARAM_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*")
ELLIPSIS = ("...", "…")


@dataclass
class Param:
    name: str
    optional: bool
    repeatable: bool = False
    group: str | None = None


@dataclass
class Signature:
    name: str | None
    params: list = field(default_factory=list)
    min_args: int | None = None
    max_args: int | None = None   # None = unlimited (when not issues)
    issues: list = field(default_factory=list)

    @property
    def confident(self):
        return not self.issues


def parse(format_line, expected_name=None):
    text = " ".join(format_line.replace("\xa0", " ").split())
    match = re.fullmatch(r"(%s)\s*(?:\((.*)\))?" % NAME.pattern, text)
    if not match:
        return Signature(None, issues=[f"format line not recognised: {text!r}"])
    sig = Signature(match.group(1))
    if expected_name and sig.name != expected_name:
        sig.issues.append(f"format names {sig.name!r}, page title is {expected_name!r}")
    inner = match.group(2)
    if inner is None or not inner.strip():
        sig.min_args = sig.max_args = 0
        return sig
    if "[" in inner or "]" in inner:
        sig.issues.append("contains [ ] blocks")
    if "=" in inner:
        sig.issues.append("contains name = value bindings")

    segments = split_segments(inner, sig.issues)
    unlimited = any(has_ellipsis(s) for s, _ in segments)
    bases = []
    for raw, optional in segments:
        base = raw
        for mark in ELLIPSIS:
            base = base.replace(mark, "")
        base = base.strip("[] ").strip()
        bases.append(base)
        if base and not PARAM_NAME.fullmatch(base):
            sig.issues.append(f"unexpected parameter text {raw!r}")

    # Numbered names only mean "the same parameter again" when the signature repeats.
    names = [strip_number(b) if unlimited else b for b in bases]
    counts = {}
    for n in names:
        if n:
            counts[n] = counts.get(n, 0) + 1
    repeated = {n for n, c in counts.items() if c > 1} if unlimited else set()
    for i, (raw, _) in enumerate(segments):
        if not has_ellipsis(raw):
            continue
        if names[i]:
            repeated.add(names[i])
        elif i > 0 and names[i - 1]:          # a lone "..." repeats the argument before it
            repeated.add(names[i - 1])
    if unlimited and not repeated:
        sig.issues.append("has ... but no repeating parameter could be identified")
    group = "-".join(n for n in dict.fromkeys(names) if n in repeated) if len(repeated) > 1 else None

    seen = {}
    for (raw, optional), n in zip(segments, names):
        if not n or n in seen:
            continue
        seen[n] = Param(n, optional, n in repeated, group if n in repeated else None)
    sig.params = list(seen.values())

    required = [n for (raw, optional), n in zip(segments, names) if n and not optional]
    sig.min_args = len(required)
    sig.max_args = None if unlimited else len([n for n in names if n])
    first_optional = next((i for i, (_, opt) in enumerate(segments) if opt), None)
    if first_optional is not None and any(not opt for _, opt in segments[first_optional:]):
        sig.issues.append("required argument after an optional one")
    return sig


def split_segments(inner, issues):
    """'a ; b {; c ; d... }' -> [('a', False), ('b', False), ('c', True), ('d...', True)].
    A segment is optional when its first character sits inside { }."""
    segments, current, depth, start_depth, parens = [], "", 0, None, 0
    for ch in inner:
        if ch in "()":                         # a nested call such as TextColor's RGB ( red ; green ; blue )
            parens += 1 if ch == "(" else -1
            current += ch
        elif parens:
            current += ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                issues.append("unbalanced { }")
                depth = 0
        elif ch == ";":
            if current.strip():
                segments.append((current.strip(), start_depth > 0))
            elif segments or current:
                issues.append("empty argument")
            current, start_depth = "", None
        else:
            if start_depth is None and not ch.isspace():
                start_depth = depth
            current += ch
    if current.strip():
        segments.append((current.strip(), start_depth > 0))
    if depth:
        issues.append("unbalanced { }")
    return segments


def has_ellipsis(text):
    return any(mark in text for mark in ELLIPSIS)


def strip_number(name):
    return re.sub(r"\d+$", "", name) or name


# ── data types ────────────────────────────────────────────────────────────────

TYPE_WORDS = [
    ("timestamp", r"\btimestamps?\b"),
    ("container", r"\bcontainers?\b"),
    ("json", r"\bJSON\b"),
    ("date", r"\bdates?\b"),
    ("time", r"\btimes?\b"),
    ("number", r"\bnumeric\b|\bnumbers?\b"),
    ("text", r"\btext\b"),
    ("boolean", r"\bBoolean\b|\bTrue\b|\bFalse\b"),
]
RETURN_TYPES = {"text", "number", "date", "time", "timestamp", "container"}


def infer_param_type(description, name=""):
    """Best guess from help's parameter description: the type word that comes first in its first sentence
    ('any numeric expression ... from the start of the text' -> 'number'). Three or more different types
    ('any number, date, time or timestamp expression') give 'any'; a parameter named like 'json' is json.
    These are hints for review, so function_parameters.type_source records them as 'inferred'."""
    if "json" in name.lower():
        return "json"
    first = re.split(r"(?<=[.;])\s", description or "", maxsplit=1)[0]
    found = {}
    for type_name, pattern in TYPE_WORDS:
        match = re.search(pattern, first)
        if match:
            found[type_name] = match.start()
    if not found or len(found) >= 3:
        return "any"
    return min(found, key=found.get)


def map_return_type(raw):
    """'text' -> 'text'; 'text, number, date, time, timestamp, container' -> 'any'. None when unrecognised."""
    words = {w.strip().lower() for w in re.split(r",|\bor\b", raw or "") if w.strip()}
    if not words or not words <= RETURN_TYPES:
        return None
    return words.pop() if len(words) == 1 else "any"
