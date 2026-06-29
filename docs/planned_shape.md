# Ultimate JSON Shape for Inventorying FileMaker Pro Script Steps

## Context

This document proposes a JSON structure for inventorying FileMaker Pro script steps using two complementary source formats:

1. **FileMaker clipboard XML** — the richer, machine-readable source of truth.
2. **Printed Script PDF** — the human-facing GUI representation of the same script.

The goal is to map XML script steps to printed script steps, preserve FileMaker's executable step structure, and also retain how each step and its options are displayed in FileMaker Pro's GUI.

The recommended model is not just an array of rendered script lines. It should be an array of **step definitions / step observations** that can round-trip between:

- FileMaker clipboard XML
- Printed GUI text
- Parsed normalized options
- Your own stable inventory layer

The XML should be treated as the canonical source. The printed script should be treated as a display/rendering profile.

---

## Recommended Top-Level JSON Shape

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
      "scriptName": "OneOfEverything",
      "rawAvailable": true
    },
    "printed": {
      "type": "script-print-pdf",
      "scriptName": "OneOfEverything",
      "rawAvailable": true
    }
  },
  "steps": []
}
```

The most important part is each object inside `steps`.

---

## Recommended Step Object Shape

```json
{
  "stepKey": "set-error-capture",
  "fmStepId": 86,
  "names": {
    "xml": "Set Error Capture",
    "printed": "Set Error Capture",
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
      "enable": {
        "type": "boolean",
        "xmlAttribute": "@enable",
        "default": true
      },
      "id": {
        "type": "integer",
        "xmlAttribute": "@id"
      },
      "name": {
        "type": "string",
        "xmlAttribute": "@name"
      }
    },
    "template": "<Step enable=\"{{enabled}}\" id=\"86\" name=\"Set Error Capture\"><Set state=\"{{setState}}\"/></Step>",
    "children": [
      {
        "path": "Set",
        "attributes": {
          "state": {
            "type": "boolean",
            "default": false
          }
        },
        "text": null,
        "required": true
      }
    ],
    "observedExamples": [
      {
        "xml": "<Step enable=\"True\" id=\"86\" name=\"Set Error Capture\"><Set state=\"True\"/></Step>"
      }
    ]
  },
  "display": {
    "printedTemplate": "Set Error Capture [ {{setState|onOff}} ]",
    "parts": [
      {
        "type": "stepName",
        "value": "Set Error Capture"
      },
      {
        "type": "inlineOptions",
        "brackets": true,
        "separator": "; ",
        "items": [
          {
            "optionKey": "setState",
            "when": "always",
            "format": "{{value|onOff}}"
          }
        ]
      }
    ],
    "observedPrinted": [
      "Set Error Capture [ On ]"
    ]
  },
  "options": [
    {
      "key": "setState",
      "label": "Set",
      "type": "boolean",
      "source": {
        "xmlPath": "Set/@state"
      },
      "display": {
        "location": "inline",
        "trueText": "On",
        "falseText": "Off",
        "template": "{{value|onOff}}"
      },
      "default": false,
      "allowedValues": [true, false]
    }
  ],
  "parameters": [],
  "validation": {
    "requiredOptions": ["setState"],
    "mutuallyExclusive": [],
    "dependencies": []
  },
  "mapping": {
    "matchStrategy": "sequential-name-normalized",
    "confidence": 1,
    "xmlStepIndex": null,
    "printedStepIndex": null,
    "notes": []
  },
  "notes": []
}
```

This shape separates:

- What FileMaker stores
- What FileMaker displays
- How your system should understand the option semantically

---

## Why the XML Must Be Canonical

The XML and printed script do not contain the same amount of information.

For example, the printed script might show:

```text
Insert from URL [ ]
    [ Select; No dialog ]
```

But the XML may contain several independent option nodes:

```xml
<Step enable="True" id="160" name="Insert from URL">
  <NoInteract state="True"/>
  <DontEncodeURL state="False"/>
  <SelectAll state="True"/>
  <VerifySSLCertificates state="False"/>
</Step>
```

The printed script shows `Select` and `No dialog`, but it may not expose every XML child option. Therefore, the display text should not be the source of truth.

---

## Stronger Example: `Insert from URL`

```json
{
  "stepKey": "insert-from-url",
  "fmStepId": 160,
  "names": {
    "xml": "Insert from URL",
    "printed": "Insert from URL",
    "canonical": "Insert from URL",
    "aliases": []
  },
  "kind": {
    "category": "field-editing",
    "controlFlowRole": null,
    "isContainerStep": false,
    "isTerminatorStep": false
  },
  "xml": {
    "template": "<Step enable=\"{{enabled}}\" id=\"160\" name=\"Insert from URL\"><NoInteract state=\"{{noDialog}}\"/><DontEncodeURL state=\"{{dontEncodeUrl}}\"/><SelectAll state=\"{{selectTargetContents}}\"/><VerifySSLCertificates state=\"{{verifySslCertificates}}\"/></Step>",
    "children": [
      {
        "path": "NoInteract",
        "attributes": {
          "state": {
            "type": "boolean"
          }
        },
        "required": false
      },
      {
        "path": "DontEncodeURL",
        "attributes": {
          "state": {
            "type": "boolean"
          }
        },
        "required": false
      },
      {
        "path": "SelectAll",
        "attributes": {
          "state": {
            "type": "boolean"
          }
        },
        "required": false
      },
      {
        "path": "VerifySSLCertificates",
        "attributes": {
          "state": {
            "type": "boolean"
          }
        },
        "required": false
      }
    ],
    "observedExamples": [
      {
        "xml": "<Step enable=\"True\" id=\"160\" name=\"Insert from URL\"><NoInteract state=\"True\"/><DontEncodeURL state=\"False\"/><SelectAll state=\"True\"/><VerifySSLCertificates state=\"False\"/></Step>"
      }
    ]
  },
  "display": {
    "printedTemplate": "Insert from URL [ ]\n    [ {{selectTargetContents|select}}; {{noDialog|noDialog}} ]",
    "parts": [
      {
        "type": "stepName",
        "value": "Insert from URL"
      },
      {
        "type": "inlineOptions",
        "brackets": true,
        "items": []
      },
      {
        "type": "continuationOptions",
        "brackets": true,
        "separator": "; ",
        "items": [
          {
            "optionKey": "selectTargetContents",
            "when": "true",
            "text": "Select"
          },
          {
            "optionKey": "noDialog",
            "when": "true",
            "text": "No dialog"
          }
        ]
      }
    ],
    "observedPrinted": [
      "Insert from URL [ ]",
      "[ Select; No dialog ]"
    ]
  },
  "options": [
    {
      "key": "noDialog",
      "label": "No dialog",
      "type": "boolean",
      "source": {
        "xmlPath": "NoInteract/@state"
      },
      "display": {
        "location": "continuation",
        "trueText": "No dialog",
        "falseText": null,
        "omitWhenFalse": true
      }
    },
    {
      "key": "selectTargetContents",
      "label": "Select",
      "type": "boolean",
      "source": {
        "xmlPath": "SelectAll/@state"
      },
      "display": {
        "location": "continuation",
        "trueText": "Select",
        "falseText": null,
        "omitWhenFalse": true
      }
    },
    {
      "key": "dontEncodeUrl",
      "label": "Do not automatically encode URL",
      "type": "boolean",
      "source": {
        "xmlPath": "DontEncodeURL/@state"
      },
      "display": {
        "location": "hidden-or-dialog-only"
      }
    },
    {
      "key": "verifySslCertificates",
      "label": "Verify SSL Certificates",
      "type": "boolean",
      "source": {
        "xmlPath": "VerifySSLCertificates/@state"
      },
      "display": {
        "location": "hidden-or-dialog-only"
      }
    }
  ],
  "parameters": [
    {
      "key": "target",
      "label": "Target",
      "type": "field-or-variable",
      "source": {
        "xmlPath": null
      },
      "display": {
        "placeholderWhenMissing": ""
      },
      "required": false
    },
    {
      "key": "url",
      "label": "URL",
      "type": "calculation-or-text",
      "source": {
        "xmlPath": null
      },
      "required": false
    },
    {
      "key": "curlOptions",
      "label": "cURL options",
      "type": "calculation",
      "source": {
        "xmlPath": "CURLOptions/Calculation"
      },
      "required": false
    }
  ],
  "validation": {
    "requiredOptions": [],
    "mutuallyExclusive": [],
    "dependencies": []
  },
  "mapping": {
    "matchStrategy": "sequential-name-normalized",
    "confidence": 1,
    "notes": [
      "Printed output shows Select and No dialog, but does not expose every XML child option."
    ]
  },
  "notes": []
}
```

---

## Add an Instance Layer for Real Scripts

The catalog above describes a **step type**. When parsing an actual FileMaker script, you also need the actual step occurrence.

```json
{
  "instanceId": "oneofeverything.step.160",
  "stepIndex": 160,
  "enabled": true,
  "definitionKey": "insert-from-url",
  "fmStepId": 160,
  "name": "Insert from URL",
  "raw": {
    "xml": "<Step enable=\"True\" id=\"160\" name=\"Insert from URL\">...</Step>",
    "printedLines": [
      "Insert from URL [ ]",
      "[ Select; No dialog ]"
    ]
  },
  "values": {
    "noDialog": true,
    "selectTargetContents": true,
    "dontEncodeUrl": false,
    "verifySslCertificates": false,
    "target": null,
    "url": null,
    "curlOptions": null
  },
  "rendered": {
    "printed": "Insert from URL [ ]\n    [ Select; No dialog ]",
    "compact": "Insert from URL [ Select; No dialog ]"
  },
  "children": []
}
```

This lets you maintain both:

```json
{
  "stepDefinitions": [],
  "scriptInstances": []
}
```

---

## Mapping Strategy from XML to Printed PDF

Use **order first**, then normalized name.

Do not map by name alone. A script can contain repeated comments, repeated steps, and control-flow structures. The printed script can also contain blank lines, page headers, page footers, and continuation option lines.

Recommended process:

```text
1. Parse XML into Step[].
2. Parse printed PDF into logical printed steps:
   - A new step starts on a non-indented line.
   - Indented bracket lines belong to the previous step.
   - Ignore page headers and footers.
3. Normalize names:
   - "#Comment" -> "# (comment)"
   - trim whitespace
   - collapse repeated spaces
   - remove harmless trailing spaces, e.g. "Configure RAG Account "
4. Walk both lists sequentially.
5. Match each XML step to the next printed logical step.
6. Store confidence:
   - 1.0 = same normalized name and same sequence
   - 0.8 = alias matched
   - 0.5 = sequence matched but printed name is absent or ambiguous
7. Preserve raw XML and raw printed lines even when parsed values are incomplete.
```

---

## The Option Object Should Be the Heart of the Model

Most FileMaker script step complexity is option mapping. Standardize every option like this:

```json
{
  "key": "noDialog",
  "label": "No dialog",
  "type": "boolean",
  "source": {
    "xmlPath": "NoInteract/@state",
    "xmlValueMap": {
      "True": true,
      "False": false
    }
  },
  "display": {
    "location": "inline | continuation | dialog | hidden-or-dialog-only",
    "trueText": "No dialog",
    "falseText": null,
    "omitWhenFalse": true,
    "template": "{{trueText}}",
    "order": 20
  },
  "default": false,
  "allowedValues": [true, false],
  "required": false,
  "notes": []
}
```

### Enum Option Example

```json
{
  "key": "windowState",
  "label": "Window state",
  "type": "enum",
  "source": {
    "xmlPath": "WindowState/@value"
  },
  "allowedValues": [
    {
      "value": "ResizeToFit",
      "printed": "Resize to Fit"
    },
    {
      "value": "Minimize",
      "printed": "Minimize"
    },
    {
      "value": "Maximize",
      "printed": "Maximize"
    }
  ],
  "display": {
    "location": "continuation",
    "template": "{{value.printed}}"
  }
}
```

### Nested Option Group Example

For complex nested options, such as PDF options, keep the nesting:

```json
{
  "key": "pdfOptions",
  "label": "PDF Options",
  "type": "object",
  "source": {
    "xmlPath": "PDFOptions"
  },
  "properties": {
    "source": {
      "type": "enum",
      "source": {
        "xmlPath": "PDFOptions/@source"
      }
    },
    "security": {
      "type": "object",
      "source": {
        "xmlPath": "PDFOptions/Security"
      }
    },
    "view": {
      "type": "object",
      "source": {
        "xmlPath": "PDFOptions/View"
      }
    }
  },
  "display": {
    "location": "dialog",
    "summaryTemplate": "{{source|pdfSourceSummary}}"
  }
}
```

---

## Fields to Always Include on Every Step Definition

```json
{
  "stepKey": "",
  "fmStepId": null,
  "names": {
    "xml": "",
    "printed": "",
    "canonical": "",
    "aliases": []
  },
  "kind": {
    "category": null,
    "controlFlowRole": null,
    "isContainerStep": false,
    "isTerminatorStep": false
  },
  "xml": {
    "template": "",
    "stepAttributes": {},
    "children": [],
    "observedExamples": []
  },
  "display": {
    "printedTemplate": "",
    "parts": [],
    "observedPrinted": []
  },
  "options": [],
  "parameters": [],
  "validation": {
    "requiredOptions": [],
    "mutuallyExclusive": [],
    "dependencies": []
  },
  "mapping": {
    "matchStrategy": "",
    "confidence": null,
    "notes": []
  },
  "notes": []
}
```

---

## Final Recommendation

Use the XML as the **lossless canonical source**, and treat the printed PDF as a **display renderer profile**.

The printed version is excellent for learning what FileMaker's GUI chooses to show. However, it is not complete enough to recreate a step safely. The XML contains the actual persistent step structure, including options that may not be visible in the printed script.

A strong final model should therefore separate:

```json
{
  "stepDefinitions": [],
  "scriptInstances": [],
  "displayProfiles": [],
  "sourceFiles": []
}
```

That gives you room to grow into:

- Multiple FileMaker versions
- Multiple languages/locales
- XML round-tripping
- GUI display rendering
- Diffing scripts semantically
- Generating documentation
- Validating script step options
- Building a FileMaker script-step inventory database
