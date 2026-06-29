# FM Script Inventory

A tool for building a complete, authoritative inventory of every FileMaker Pro script step — mapping each step's internal XML representation to its GUI display text.

## Goal

FileMaker Pro has a fixed set of script steps. Each step has two representations:

- **XML** — the internal structure FileMaker uses when copying steps to the clipboard (`fmxmlsnippet` format). This is the lossless, machine-readable source of truth.
- **PDF** — the human-readable printed script, which shows how FileMaker renders each step in its GUI.

These two representations do not carry the same information. The XML contains option nodes that the printed script may never display. This tool correlates the two, producing a JSON catalog that captures both: what FileMaker stores, and what FileMaker shows.

The intended input is a single FileMaker script named something like **"OneOfEverything"** — a script that contains one instance of every available script step. Given the XML and PDF exports of that script, this tool produces a step-by-step inventory.

## Inputs

Place both files in `to_analyze/` before running:

| File | How to produce it |
|---|---|
| `to_analyze/script.xml` | In FileMaker Pro, select all steps in the script, copy, then paste into a text file. The result is an `fmxmlsnippet` XML document. |
| `to_analyze/script.pdf` | In FileMaker Pro Script Workspace, use **File > Print** (or the print icon) to print the script to a PDF file. |

Both files must come from the **same script** and the **same FileMaker version**.

## Output

The tool produces a JSON document with two top-level arrays:

```json
{
  "schemaVersion": "fm-script-step-inventory/v1",
  "fileMaker": { "product": "FileMaker Pro", "sourceVersion": null, "locale": "en" },
  "sources": { "xml": { ... }, "printed": { ... } },
  "stepDefinitions": [],
  "scriptInstances": []
}
```

**`stepDefinitions`** — one entry per unique script step type, describing:
- The step's numeric ID and canonical name
- Its full XML structure (child elements, attributes, and a template)
- Its display structure (how options appear in the printed script)
- Each option's type, XML path, display location, and allowed values

**`scriptInstances`** — one entry per step occurrence in the source script, with the actual values observed and the raw XML and printed text preserved.

See [`docs/planned_shape.md`](docs/planned_shape.md) for the full JSON schema with annotated examples.

## How It Works

### 1. Parse the XML

The XML is a flat list of `<Step>` elements inside an `<fmxmlsnippet>`. Each step has:
- `@id` — FileMaker's stable numeric step ID
- `@name` — the step's display name
- `@enable` — whether the step is active
- Child elements — the step's options and parameters

### 2. Parse the PDF

The printed script is extracted as text. Parsing rules:

- A new step begins on a non-indented line.
- Indented lines beginning with `[` are continuation option lines belonging to the previous step.
- Page headers, footers, and page numbers are ignored.
- Names are normalized: trim whitespace, collapse repeated spaces.

### 3. Map XML steps to printed steps

Steps are matched **sequentially by position**, not by name alone (names can repeat — comments, for example, all share the same step ID). The match is confirmed by comparing normalized names. A confidence score is recorded:

| Score | Meaning |
|---|---|
| 1.0 | Name matches and position matches |
| 0.8 | Alias matched |
| 0.5 | Position matched but printed name is absent or ambiguous |

### 4. Build step definitions

For each unique step ID, a definition object is built from the observed XML structure, the printed display text, and the resolved option mappings. The XML is treated as canonical; the printed text is treated as the rendering profile.

### 5. Emit JSON

The final output is written as a JSON file containing both the step definitions and the per-instance script observations.

## Key Concepts

### XML is canonical

The printed script omits options that are hidden or only accessible via a dialog. For example:

```
Insert from URL [ ]
    [ Select; No dialog ]
```

The XML for the same step contains four option nodes:

```xml
<Step enable="True" id="160" name="Insert from URL">
  <NoInteract state="True"/>
  <DontEncodeURL state="False"/>
  <SelectAll state="True"/>
  <VerifySSLCertificates state="False"/>
</Step>
```

`DontEncodeURL` and `VerifySSLCertificates` are not visible in the printed output. Only the XML reveals they exist.

### Options vs. parameters

Each step definition separates two concepts:

- **Options** — boolean flags or enum choices that control step behavior (e.g., "No dialog", "Select all"). These appear as XML child element attributes.
- **Parameters** — user-supplied values like field references, variable names, calculations, or file paths. These may appear as XML child text content or as nested `<Calculation>` elements.

### Display locations

Each option is classified by where it appears in the printed output:

| Location | Meaning |
|---|---|
| `inline` | Shown on the same line as the step name, inside `[ ]` |
| `continuation` | Shown on the next indented line, inside `[ ]` |
| `dialog` | Only accessible via a dialog; not shown in the printed script |
| `hidden-or-dialog-only` | Never shown in the printed script |

## Project Structure

```
to_analyze/
  script.xml        # fmxmlsnippet clipboard export of the source script
  script.pdf        # printed script PDF from FileMaker
docs/
  planned_shape.md  # full JSON schema specification with examples
```
