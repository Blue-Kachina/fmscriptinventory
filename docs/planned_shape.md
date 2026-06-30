# JSON Schema Reference: FM Script Step Inventory

## Architecture

This project produces a JSON catalog of every FileMaker Pro script step, mapping each step's internal XML structure to its script editor display representation.

Two inputs drive the output:

1. **`to_analyze/script.xml`** — a FileMaker clipboard export (`fmxmlsnippet`) of a script containing one instance of every step. This is the lossless, machine-readable source of truth. Options that are hidden or dialog-only are still present in the XML even when they're invisible in the script editor.

2. **`display_map.yaml`** — a human-curated YAML file that records display semantics for each step's options: the UI label, where the option appears (inline, continuation, or dialog-only), and the display text for boolean and enum values.

The XML is canonical. The display map is the rendering profile. Neither alone is sufficient.

---

## Top-Level JSON Shape

```json
{
  "schemaVersion": "fm-script-step-inventory/v1",
  "fileMaker": {
    "product": "FileMaker Pro",
    "sourceVersion": null,
    "locale": "en",
    "platform": null
  },
  "sources": {
    "xml": {
      "type": "clipboard-fmxmlsnippet",
      "file": "to_analyze/script.xml",
      "scriptCount": 1,
      "stepCount": 207
    }
  },
  "stepDefinitions": [],
  "scriptInstances": []
}
```

---

## Step Definition Object

One entry per unique FileMaker step ID. The full shape with all fields:

```json
{
  "stepKey": "set-error-capture",
  "fmStepId": 86,
  "names": {
    "xml": "Set Error Capture",
    "display": null,
    "canonical": "Set Error Capture",
    "aliases": []
  },
  "kind": {
    "category": null,
    "controlFlowRole": null,
    "isContainerStep": false,
    "isTerminatorStep": false
  },
  "xml": {
    "stepAttributes": {
      "enable": { "type": "boolean", "xmlAttribute": "@enable", "default": true },
      "id":     { "type": "integer", "xmlAttribute": "@id" },
      "name":   { "type": "string",  "xmlAttribute": "@name" }
    },
    "template": "<Step enable=\"{{enabled}}\" id=\"86\" name=\"Set Error Capture\"><Set state=\"{{setState}}\"/></Step>",
    "children": [
      {
        "path": "Set",
        "type": "boolean",
        "attributes": { "state": { "observed": "True" } },
        "hasText": false,
        "hasChildren": false
      }
    ],
    "observedExamples": [
      { "xml": "<Step enable=\"True\" id=\"86\" name=\"Set Error Capture\"><Set state=\"True\"/></Step>" }
    ]
  },
  "display": {
    "displayName": null,
    "parts": [
      { "type": "stepName", "value": "Set Error Capture" },
      {
        "type": "inlineOptions",
        "brackets": true,
        "items": [{ "optionKey": "set", "label": "Set error capture" }]
      }
    ]
  },
  "options": [
    {
      "key": "set",
      "label": "Set error capture",
      "type": "boolean",
      "source": { "xmlPath": "Set/@state" },
      "display": {
        "location": "inline",
        "trueText": "On",
        "falseText": "Off"
      },
      "allowedValues": [true, false],
      "default": false
    }
  ],
  "parameters": [],
  "validation": {
    "requiredOptions": [],
    "mutuallyExclusive": [],
    "dependencies": []
  },
  "notes": []
}
```

### names

| Field | Source | Description |
|---|---|---|
| `xml` | XML `@name` | Step name as stored in the fmxmlsnippet |
| `display` | `display_map.yaml` `displayName` | Override for steps where the UI name differs from the XML name (usually `null`) |
| `canonical` | normalized `xml` | Whitespace-collapsed version used as the slug base |
| `aliases` | manual | Alternative names this step may appear as |

### display.parts

An array describing the visual structure of the step in the script editor:

| Type | Description |
|---|---|
| `stepName` | The step's display name (first element always) |
| `inlineOptions` | Options shown in `[ ]` on the same line as the step name |
| `continuationOptions` | Options shown in `[ ]` on the next indented line |

`parts` is auto-built from the options that have a known `displayLocation`. It updates on each `analyze.py` run as `display_map.yaml` is filled in.

---

## Example: Insert from URL (complex step)

```json
{
  "stepKey": "insert-from-url",
  "fmStepId": 160,
  "names": {
    "xml": "Insert from URL",
    "display": null,
    "canonical": "Insert from URL",
    "aliases": []
  },
  "xml": {
    "template": "<Step enable=\"{{enabled}}\" id=\"160\" name=\"Insert from URL\"><NoInteract state=\"{{noInteractState}}\"/><DontEncodeURL state=\"{{dontEncodeURLState}}\"/><SelectAll state=\"{{selectAllState}}\"/><VerifySSLCertificates state=\"{{verifySSLCertificatesState}}\"/></Step>",
    "children": [
      { "path": "NoInteract",           "type": "boolean", "attributes": { "state": { "observed": "True" } },  "hasText": false, "hasChildren": false },
      { "path": "DontEncodeURL",        "type": "boolean", "attributes": { "state": { "observed": "False" } }, "hasText": false, "hasChildren": false },
      { "path": "SelectAll",            "type": "boolean", "attributes": { "state": { "observed": "True" } },  "hasText": false, "hasChildren": false },
      { "path": "VerifySSLCertificates","type": "boolean", "attributes": { "state": { "observed": "False" } }, "hasText": false, "hasChildren": false }
    ],
    "observedExamples": [
      { "xml": "<Step enable=\"True\" id=\"160\" name=\"Insert from URL\"><NoInteract state=\"True\"/><DontEncodeURL state=\"False\"/><SelectAll state=\"True\"/><VerifySSLCertificates state=\"False\"/></Step>" }
    ]
  },
  "display": {
    "displayName": null,
    "parts": [
      { "type": "stepName", "value": "Insert from URL" },
      {
        "type": "continuationOptions",
        "brackets": true,
        "items": [
          { "optionKey": "noInteract", "label": "No dialog" },
          { "optionKey": "selectAll",  "label": "Select" }
        ]
      }
    ]
  },
  "options": [
    {
      "key": "noInteract",
      "label": "No dialog",
      "type": "boolean",
      "source": { "xmlPath": "NoInteract/@state" },
      "display": { "location": "continuation", "trueText": "No dialog", "omitWhenFalse": true },
      "allowedValues": [true, false],
      "default": false
    },
    {
      "key": "dontEncodeURL",
      "label": "Do not automatically encode URL",
      "type": "boolean",
      "source": { "xmlPath": "DontEncodeURL/@state" },
      "display": { "location": "hidden-or-dialog-only" },
      "allowedValues": [true, false],
      "default": false
    },
    {
      "key": "selectAll",
      "label": "Select",
      "type": "boolean",
      "source": { "xmlPath": "SelectAll/@state" },
      "display": { "location": "continuation", "trueText": "Select", "omitWhenFalse": true },
      "allowedValues": [true, false],
      "default": false
    },
    {
      "key": "verifySSLCertificates",
      "label": "Verify SSL Certificates",
      "type": "boolean",
      "source": { "xmlPath": "VerifySSLCertificates/@state" },
      "display": { "location": "hidden-or-dialog-only" },
      "allowedValues": [true, false],
      "default": false
    }
  ],
  "parameters": [],
  "notes": [
    "NoInteract=True means the dialog is suppressed. The XML attribute name is inverted relative to the display label 'No dialog'."
  ]
}
```

The key insight here: the script editor shows `[ Select; No dialog ]` in a continuation line, but the XML has four child elements — two of which (`DontEncodeURL`, `VerifySSLCertificates`) are completely invisible in the script editor. The display map records this split.

---

## The Option Object

Every option follows this shape:

```json
{
  "key": "noInteract",
  "label": "No dialog",
  "type": "boolean",
  "source": {
    "xmlPath": "NoInteract/@state"
  },
  "display": {
    "location": "inline | continuation | hidden-or-dialog-only",
    "trueText": "No dialog",
    "falseText": null,
    "omitWhenFalse": true
  },
  "default": false,
  "allowedValues": [true, false]
}
```

| Field | Description |
|---|---|
| `key` | Camel-case identifier (from `display_map.yaml` if provided; otherwise derived from XML tag) |
| `label` | Human-readable name as shown in the script editor dialog |
| `type` | `boolean`, `enum`, `calculation`, `text`, `object`, or `unknown` |
| `source.xmlPath` | XPath-like pointer to the value within the step's XML children |
| `display.location` | Where the option appears in the script editor |
| `display.trueText` | Text shown when the boolean is `true` (boolean only) |
| `display.falseText` | Text shown when the boolean is `false` (boolean only; `null` = not shown) |
| `display.omitWhenFalse` | If `true`, the option is not mentioned when its value is `false` |
| `allowedValues` | `[true, false]` for booleans; array of `{xmlValue, displayText}` for enums |

### Enum option example

```json
{
  "key": "windowState",
  "label": "Window state",
  "type": "enum",
  "source": { "xmlPath": "WindowState/@value" },
  "display": { "location": "inline" },
  "allowedValues": [
    { "xmlValue": "ResizeToFit", "displayText": "Resize to Fit" },
    { "xmlValue": "Minimize",    "displayText": "Minimize" },
    { "xmlValue": "Maximize",    "displayText": "Maximize" }
  ]
}
```

---

## Script Instance Object

One instance per step occurrence in the source script(s). Instances reference their parent definition by `definitionKey` and store pre-parsed option values keyed by the definition's option keys.

```json
{
  "instanceId": "oneofeverything.step.47",
  "scriptName": "OneOfEverything",
  "stepIndex": 47,
  "enabled": true,
  "fmStepId": 160,
  "name": "Insert from URL",
  "definitionKey": "insert-from-url",
  "raw": {
    "xml": "<Step enable=\"True\" id=\"160\" name=\"Insert from URL\"><NoInteract state=\"True\"/><DontEncodeURL state=\"False\"/><SelectAll state=\"True\"/><VerifySSLCertificates state=\"False\"/></Step>"
  },
  "values": {
    "noInteract": true,
    "dontEncodeURL": false,
    "selectAll": true,
    "verifySSLCertificates": false
  }
}
```

`values` keys match the option `key` fields in the parent step definition, so a consumer can look up display rules without any XML-path translation:

```
definition.options[i].key  →  instance.values[key]  →  display rule from definition.options[i].display
```

---

## display_map.yaml Format

The display map is the human-knowledge layer. One entry per step ID:

```yaml
- stepId: 160
  stepName: Insert from URL
  displayName: null         # override if UI name differs from XML name
  options:
    - xmlPath: NoInteract/@state
      key: noInteract                  # derived from XML tag name; update to semantic key if desired
      type: boolean
      label: No dialog                 # human-readable UI label
      displayLocation: continuation    # inline | continuation | hidden-or-dialog-only
      omitWhenFalse: true
      trueText: No dialog
      falseText: null
    - xmlPath: DontEncodeURL/@state
      key: dontEncodeURL
      type: boolean
      label: Do not automatically encode URL
      displayLocation: hidden-or-dialog-only
      omitWhenFalse: null
      trueText: null
      falseText: null
    - xmlPath: SelectAll/@state
      key: selectAll
      type: boolean
      label: Select
      displayLocation: continuation
      omitWhenFalse: true
      trueText: Select
      falseText: null
    - xmlPath: VerifySSLCertificates/@state
      key: verifySSLCertificates
      type: boolean
      label: Verify SSL Certificates
      displayLocation: hidden-or-dialog-only
      omitWhenFalse: null
      trueText: null
      falseText: null
```

For enum options:

```yaml
    - xmlPath: WindowState/@value
      key: windowState
      type: enum
      label: Window state
      displayLocation: inline
      allowedValues:
        - xmlValue: ResizeToFit
          displayText: Resize to Fit
        - xmlValue: Minimize
          displayText: Minimize
        - xmlValue: Maximize
          displayText: Maximize
```

---

## Why the XML Must Be Canonical

The script editor display is a lossy view of the step's configuration. Two important cases:

**1. Hidden options.** Options like `VerifySSLCertificates` and `DontEncodeURL` are only accessible via the step's configuration dialog. They do not appear in the script editor's inline or continuation display at all. The XML always contains them; the display map marks them `hidden-or-dialog-only`.

**2. Inverted labels.** `<NoInteract state="True"/>` means "don't show a dialog". The script editor shows this as `No dialog` — an inverted label. The display map records the mapping: XML `True` → display `"No dialog"` (omit when False).

The consumer must read option values from the XML (via `source.xmlPath`) and translate them to display text using the step definition. Never parse the script editor's display text as the source of truth.

---

## Future Growth Areas

The current schema has placeholder fields intended for future extension:

- `kind.category`, `kind.controlFlowRole`, `kind.isContainerStep`, `kind.isTerminatorStep` — step classification (control flow, field, window, file, etc.)
- `parameters` — user-supplied values like field references, variable names, or file paths (currently empty; distinct from boolean/enum options)
- `validation.requiredOptions`, `validation.mutuallyExclusive`, `validation.dependencies` — option constraint rules
- `names.aliases` — alternative step names across FileMaker versions or locales
- `display.displayName` — for the rare case where the script editor UI name differs from the XML `@name`

The schema also naturally extends to:

- Multiple FileMaker versions (different step IDs, renamed options)
- Multiple locales (different display text)
- Semantic script diffing (compare two scripts by step definition, not raw text)
- XML round-tripping (generate valid XML from a definition + values)
