# FM Script Inventory

A tool for building a complete, authoritative inventory of every FileMaker Pro script step — mapping each step's internal XML representation to its GUI display text.

## Goal

FileMaker Pro has a fixed set of script steps. Each step has two representations:

- **XML** — the internal structure FileMaker uses when copying steps to the clipboard (`fmxmlsnippet` format). This is the lossless, machine-readable source of truth.
- **Script Editor UI** — how FileMaker renders each step visually: the step name, inline option brackets, continuation lines, and dialog-only settings.

These two representations do not carry the same information. The XML contains option nodes that the script editor may never show inline (e.g., options only accessible via a dialog). This tool produces a JSON catalog capturing both: what FileMaker stores internally, and how each option appears in the UI.

The output is intended to be used as a **lookup map** by a consumer system that parses arbitrary FileMaker scripts and renders them in a display UI.

For rendering ` ```filemaker-script ` fenced markdown into that display UI (parser, `highlight.js` language definition, and stylesheet), use [`fmscriptui`](https://github.com/Blue-Kachina/fmscriptui) rather than vendoring a copy here.

## Inputs

| File | Required | Purpose |
|---|---|---|
| `to_analyze/script.xml` | Yes | fmxmlsnippet clipboard export of a "one of everything" script |
| `display_map.yaml` | Yes | Human-curated display semantics for each step's options |

**`to_analyze/script.xml`** — In FileMaker Pro, create a script that contains one instance of every script step (the `OneOfEverything` pattern). Select all steps, copy, paste into a text file. The result is an `fmxmlsnippet` XML document. This file drives the XML schema extraction.

**`display_map.yaml`** — A YAML file that records how each XML option maps to the script editor UI: the human-readable label, where it appears (inline, continuation, or dialog-only), display text for boolean and enum values, etc. Run `python3 analyze.py --gen-stubs` to generate scaffolded entries for any unmapped steps, then fill them in using the FM script editor as reference.

The tool also supports multi-script XML inputs (an `fmxmlsnippet` containing more than one `<Script>` element), which produces `scriptInstances` across all scripts.

## Output

`output/inventory.json`:

```json
{
  "schemaVersion": "fm-script-step-inventory/v1",
  "fileMaker": { "product": "FileMaker Pro", "sourceVersion": null, "locale": "en" },
  "sources": { "xml": { "type": "clipboard-fmxmlsnippet", "stepCount": 207 } },
  "stepDefinitions": [],
  "scriptInstances": []
}
```

**`stepDefinitions`** — one entry per unique script step type (keyed by FileMaker's numeric step ID), describing:
- The step's ID, slug key, and canonical name
- Its full XML schema (child elements, attributes, observed examples, and a template)
- Its display structure (how options appear in the UI, derived from `display_map.yaml`)
- Each option's type, XML source path, display location, labels, and allowed values

**`scriptInstances`** — one entry per step occurrence in the source script(s), with actual option values and the raw XML preserved. Instances reference their parent `stepDefinition` by `definitionKey`. The consumer system can use these for rendering specific scripts.

See [`docs/planned_shape.md`](docs/planned_shape.md) for the full JSON schema with annotated examples.

## How It Works

### 1. Parse the XML

The XML is a flat list of `<Step>` elements inside an `fmxmlsnippet`. Each step has:
- `@id` — FileMaker's stable numeric step ID (canonical)
- `@name` — the step's display name
- `@enable` — whether the step is active
- Child elements — the step's options and parameters

Steps are grouped by ID. One definition is built per unique ID; all occurrences in the input script(s) become `scriptInstances`.

### 2. Load the display map

`display_map.yaml` is loaded and indexed by step ID. For each option in a step definition, the display map provides:
- `label` — the human-readable name shown in the script editor (e.g., `NoInteract` → `"No dialog"`)
- `displayLocation` — where the option appears: `inline`, `continuation`, or `hidden-or-dialog-only`
- Boolean display text (`trueText`, `falseText`, `omitWhenFalse`)
- Enum display text for each allowed value (e.g., `ResizeToFit` → `"Resize to Fit"`)

Options without a display_map entry fall back to the XML attribute name as the label and `"unknown"` as the location.

### 3. Build definitions and emit JSON

For each unique step ID, a definition object is assembled from the XML schema and display map. Option keys from `display_map.yaml` are propagated into the corresponding `scriptInstances` values, so the consumer can go directly from `option.key` → `instance.values[key]` without any XML-path translation.

## Key Concepts

### XML is canonical

The script editor omits options that are hidden or only accessible via a dialog. For example, the script editor shows:

```
Insert from URL [ ]
    [ Select; No dialog ]
```

But the XML for the same step contains four option nodes:

```xml
<Step enable="True" id="160" name="Insert from URL">
  <NoInteract state="True"/>
  <DontEncodeURL state="False"/>
  <SelectAll state="True"/>
  <VerifySSLCertificates state="False"/>
</Step>
```

`DontEncodeURL` and `VerifySSLCertificates` are not visible in the script editor. Only the XML reveals they exist and what values they hold. The `display_map.yaml` records this — both are marked `hidden-or-dialog-only`.

### Options vs. parameters

Each step definition separates two concepts:

- **Options** — boolean flags or enum choices that control step behavior (e.g., "No dialog", "Restore", "Select"). These appear as XML child element attributes and are the primary content of `display_map.yaml`.
- **Parameters** — user-supplied values like field references, variable names, calculations, or file paths. These typically appear as XML `<Calculation>` children or object children.

### Display locations

Each option is classified by where it appears in the script editor:

| Location | Meaning |
|---|---|
| `inline` | Shown on the same line as the step name, inside `[ ]` |
| `continuation` | Shown on the next indented line, inside `[ ]` |
| `hidden-or-dialog-only` | Only accessible via the step's dialog; not visible in the script editor |

### The NoInteract pattern

A very common pattern: `<NoInteract state="True"/>` means "don't show a confirmation dialog". In the script editor this appears as `No dialog` (shown when `True`, omitted when `False`). Many steps follow this pattern. In `display_map.yaml`:

```yaml
- xmlPath: NoInteract/@state
  key: noInteract
  type: boolean
  label: No dialog
  displayLocation: inline
  omitWhenFalse: true
  trueText: No dialog
  falseText: null
```

## Filling in display_map.yaml

The display map is the primary human-knowledge artifact. To scaffold entries for all steps:

```sh
python3 analyze.py --gen-stubs
```

This appends one YAML entry per unmapped step to `display_map.yaml`, with all display fields set to `null`. Fill them in using FileMaker's script editor as the reference. After updating any entries, re-run `python3 analyze.py` and the JSON output updates immediately.

The file ships pre-filled for all 204 step types in FileMaker Pro 22. The main fields that may need per-step tuning are:
- `displayLocation` — `inline` vs `continuation` for boolean options
- `label` for steps where the XML attribute name differs significantly from the UI label
- `displayText` for enum values

## Requirements

- Python 3.10+
- [`pyyaml`](https://pyyaml.org/) — YAML parsing for `display_map.yaml`
- [`python-slugify`](https://github.com/un33k/python-slugify) — generates `stepKey` slugs from step names

Install dependencies:

```sh
pip install pyyaml python-slugify
```

## Usage

Generate `output/inventory.json`:

```sh
python3 analyze.py
```

Scaffold `display_map.yaml` entries for any steps not yet mapped:

```sh
python3 analyze.py --gen-stubs
```

The script prints a summary: script count, step count, unique step types, display_map coverage, and a note if any options still have unknown display locations.

## Project Structure

```
to_analyze/
  script.xml          # fmxmlsnippet clipboard export of the source script
display_map.yaml      # human-curated display semantics for all step options
output/
  inventory.json      # generated — step definitions and script instances
docs/
  planned_shape.md    # JSON schema reference with annotated examples
analyze.py            # main script
```
