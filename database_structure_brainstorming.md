# Database Structure Brainstorming

Working notes for the schema of the new SQLite file that will catalogue everything we know about FileMaker script steps.

Status legend: **[proposed]** = first-pass suggestion, **[open]** = needs a decision from us, **[decided]** = settled in the Q&A (section 5), **[deferred]** = intentionally postponed.

Decisions so far (details in section 5):
- Data is queryable **by specific FM version** or **by most-recently-observed version**; versioning is driven by *observations*, not hand-maintained ranges.
- **Separate tables per XML format** (clipboard, SAXML, DDR).
- **Multiple locales from the start**, even though only `en` content exists today.
- Help content is **scraped into the DB**, with the raw HTML/markdown kept in a `help_pages` table so it can be re-parsed.
- `display_map.yaml` is a **one-time import, then retired**; `analyze.py` is also expected to be retired.
- The canonical checked-in form of the DB is a **deterministic SQL dump** (plus `schema.sql` and migrations); the `.sqlite` file is rebuilt from it.
- An **inventory.json-style export** is generated from the DB for sister repos (section 7); it need not match the old shape.
- A **functions catalogue** is expected later; nothing here should block it.
- Step identity/aliasing is **deferred**; option ↔ XML-element mapping needs **investigation**.

---

## 1. Goals

- One SQLite file is the single catalogue of FileMaker script-step knowledge.
- Each step is documented the way help.claris.com documents it (description, origin version, options, examples, compatibility, notes).
- For each step we also record *how it appears* in:
  - XML (clipboard `fmxmlsnippet`, SaveAsXML/SAXML, DDR), and
  - the Script Editor UI in FileMaker Pro.
- Representations are **versioned**, because XML shape and UI text can change between FileMaker releases.

### What we already have (to seed the DB)

| Existing asset                                                            | Feeds into                                                            |
|---------------------------------------------------------------------------|-----------------------------------------------------------------------|
| `to_analyze/script.xml` (207 steps, clipboard XML)                        | `xml_representations`, `xml_elements`                                 |
| `to_analyze/script.pdf` (printed Script Editor text)                      | `ui_representations`                                                  |
| `display_map.yaml` (labels, display location, true/false text per option) | `ui_options`                                                          |
| `output/inventory.json` (`stepDefinitions`)                               | one-time import / cross-check                                         |
| `system_with_all_script_steps/EverythingBagel.fmp12`                      | source for future SAXML / DDR exports                                 |
| help.claris.com pages                                                     | `script_steps`, `step_options`, `step_examples`, `step_compatibility` |

Note: today we only have **one** FileMaker version's worth of XML. The versioning columns need to exist now, but they will be mostly single-valued until we export from other versions.

---

## 2. Core idea: what / how it serializes / how it displays

```
script_steps                 WHAT the step is (language-neutral identity)
  ├─ script_step_localizations   name / description / notes per locale  ──► help_pages (raw scrape)
  ├─ step_options                the options the *help* documents (conceptual)
  │     ├─ step_option_localizations   label / description per locale
  │     └─ step_option_values          enum values
  ├─ step_examples               (per locale)
  ├─ step_compatibility
  ├─ clipboard_xml_representations   HOW it serializes: clipboard fmxmlsnippet
  │     └─ clipboard_xml_elements
  ├─ saxml_representations           HOW it serializes: Save a Copy as XML
  │     └─ saxml_elements
  ├─ ddr_representations             HOW it serializes: DDR
  │     └─ ddr_elements
  └─ ui_representations              HOW it displays in Script Editor (per locale)
        └─ ui_options                label / placement / true-false text per option

Every representation row ──► *_observations ──► sources ──► fm_versions
```

`step_options` is the conceptual option (e.g. "Skip data entry validation"). The `*_elements` tables and `ui_options` are the *renderings* of that option, and each can link back to it. This lets us ask "what does this option look like in XML vs. in the editor?" with a join. (How strict that link is, see open question 5.)

---

## 3. Proposed tables

### 3.1 `fm_versions` [proposed]

Reference table so every versioned thing points at a real release instead of a free-text string.

| column                    | type            | notes                                                              |
|---------------------------|-----------------|--------------------------------------------------------------------|
| `id`                      | INTEGER PK      |                                                                    |
| `version`                 | TEXT UNIQUE     | e.g. `19.6.1`, `21.0.1`                                            |
| `major`, `minor`, `patch` | INTEGER         | for correct ordering (string sort breaks at `19.10`)               |
| `marketing_name`          | TEXT            | e.g. "Claris FileMaker 2024"                                       |
| `released_on`             | TEXT (ISO date) | nullable                                                           |
| `sort_key`                | INTEGER         | derived `major*1e6 + minor*1e3 + patch`, indexed for range queries |

### 3.2 `script_steps` [proposed, updated]

One row per FileMaker script step. Holds only **language-neutral** facts; anything a human reads lives in `script_step_localizations` (3.2a).

| column                     | type                         | notes                                                                                                                            |
|----------------------------|------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `id`                       | INTEGER PK                   | surrogate                                                                                                                        |
| `fm_step_id`               | INTEGER UNIQUE, nullable     | FileMaker's numeric step ID (the `id` attr in XML). **Nullable**: help pages do not contain it, so the scraper creates steps first and the XML importer fills this in by matching names. Provisional natural key, see open question 3. |
| `slug`                     | TEXT UNIQUE                  | `commit-transaction`, matches help URL                                                                                           |
| `category_id`              | FK -> `script_step_categories` | **Replaces the old free-text `category` column** (see 3.2b). Scraped from the category page the step is listed on, e.g. Commit Transaction -> Control. |
| `control_flow_role`        | TEXT, nullable               | carried over from `inventory.json` (`kind.controlFlowRole`), e.g. `if`, `else`, `end_if`, `loop`                                  |
| `is_container_step`        | INTEGER                      | carried over from `inventory.json` (`kind.isContainerStep`)                                                                      |
| `is_terminator_step`       | INTEGER                      | carried over from `inventory.json` (`kind.isTerminatorStep`)                                                                     |
| `originated_in_version_id` | FK -> `fm_versions`          | "Originated in version" line on help page                                                                                        |
| `deprecated_in_version_id` | FK -> `fm_versions`, nullable |                                                                                                                                  |
| `removed_in_version_id`    | FK -> `fm_versions`, nullable |                                                                                                                                  |

### 3.2a `script_step_localizations` [decided: locale from day one]

| column              | type       | notes                                                                                  |
|---------------------|------------|----------------------------------------------------------------------------------------|
| `script_step_id`    | FK         | PK is (`script_step_id`, `locale`)                                                     |
| `locale`            | TEXT       | BCP-47-ish, `en` to start (FileMaker help also ships `de`, `fr`, `ja`, ...)             |
| `name`              | TEXT       | "Commit Transaction"                                                                   |
| `description`       | TEXT       | help-page "Description"                                                                |
| `options_text`      | TEXT       | raw help-page "Options" prose, kept verbatim even once `step_options` is structured    |
| `notes`             | TEXT       | help-page "Notes" section                                                              |
| `help_page_id`      | FK         | -> `help_pages` (3.11); the raw page this row was parsed from                          |

### 3.2b `script_step_categories` [implemented in migration 0001]

Categories are a real entity (they have their own help page and a description, and their names are localized), so they get a table instead of a text column. The help site currently has **14**: Control, Navigation, Editing, Fields, Records, Found Sets, Windows, Files, Accounts, Artificial intelligence, Spelling, PDF files, Open Menu Item, Miscellaneous (the earlier list in 3.2 was missing three of these).

`script_step_categories (id, slug UNIQUE, position)` and `script_step_category_localizations (category_id, locale, name, description, help_page_id)`. `position` is the order on the help site. The scraper warns if a step is ever listed under two categories (none so far; if it happens, this becomes a join table).

### 3.3 `step_options` [proposed, updated]

Conceptual options, as the help page describes them. Language-neutral columns here; `label`/`description` move to `step_option_localizations (step_option_id, locale, label, description)`.

| column                     | type         | notes                                                                              |
|----------------------------|--------------|------------------------------------------------------------------------------------|
| `id`                       | INTEGER PK   |                                                                                    |
| `script_step_id`           | FK           |                                                                                    |
| `key`                      | TEXT         | stable machine key, e.g. `skip_data_entry_validation`                              |
| `value_type`               | TEXT         | `boolean`, `enum`, `calculation`, `text`, `field`, `script`, `layout`, `number`, ... |
| `required`                 | INTEGER      | 0/1                                                                                |
| `default_value`            | TEXT         |                                                                                    |
| `position`                 | INTEGER      | order on the help page                                                             |
| `introduced_in_version_id` | FK, nullable | some options are added later than the step                                         |

Enum values (e.g. Go to Layout destination): `step_option_values (id, step_option_id, value)` plus a localized label table.

### 3.4 `step_examples` [proposed]

| column           | type       | notes                                    |
|------------------|------------|------------------------------------------|
| `id`             | INTEGER PK |                                          |
| `script_step_id` | FK         |                                          |
| `locale`         | TEXT       | `en` to start                            |
| `position`       | INTEGER    |                                          |
| `title`          | TEXT       | nullable                                 |
| `body`           | TEXT       | the example text/script as shown on help |

### 3.5 `step_compatibility` [proposed]

The help page has a compatibility table (Pro, Go, WebDirect, Server, Data API, Cloud, …). Either a wide table with one boolean per product, or narrow rows:

| column           | type    | notes                                                      |
|------------------|---------|------------------------------------------------------------|
| `script_step_id` | FK      |                                                            |
| `product`        | TEXT    | `pro`, `go`, `webdirect`, `server`, `data_api`, `cloud`, … |
| `supported`      | INTEGER | 0/1/NULL (unknown)                                         |
| `note`           | TEXT    | e.g. "partially supported"                                 |

Narrow rows win if new products appear over time. **[decided by the scraper: narrow rows.]** The help uses seven products with its own keys: `Pro`, `Go`, `WebD`, `Server`, `CWP`, `DAPI`, `Cloud`, and three values `Yes` / `No` / `Partial`. Migration 0001 stores those verbatim as TEXT (not 0/1), since "Partial" is real information.

### 3.6 / 3.7 XML representations: one table family per format [decided: separate tables]

SAXML, clipboard `fmxmlsnippet` and DDR differ a lot structurally, so each gets its own tables instead of a shared `format` column. Each family has three tables:

- `<fmt>_representations`: one row per distinct *shape* of a step in that format.
- `<fmt>_elements`: the element/attribute breakdown of one representation.
- `<fmt>_observations`: join table recording *where/when* we saw that shape (see section 4).

| family      | tables                                                                                          | status                                  |
|-------------|-------------------------------------------------------------------------------------------------|-----------------------------------------|
| clipboard   | `clipboard_xml_representations`, `clipboard_xml_elements`, `clipboard_xml_observations`         | have data today (`script.xml`)          |
| SAXML       | `saxml_representations`, `saxml_elements`, `saxml_observations`                                 | no data yet; export from the .fmp12     |
| DDR         | `ddr_representations`, `ddr_elements`, `ddr_observations`                                       | no data yet; lowest priority            |

Column sets will start identical (below) and are then free to diverge per format, e.g. SAXML will probably need parent-path/namespace columns that clipboard doesn't. Whether to generate the three DDL blocks from one template in `schema.sql` is an implementation detail for later.

#### `<fmt>_representations` [proposed, updated]

| column           | type       | notes                                                                                                                                  |
|------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `id`             | INTEGER PK |                                                                                                                                        |
| `script_step_id` | FK         |                                                                                                                                        |
| `shape_hash`     | TEXT       | hash of the normalized element/attribute structure (not values). UNIQUE with `script_step_id`: one row per distinct shape, no duplicates |
| `example_xml`    | TEXT       | a real, verbatim snippet of this shape                                                                                                 |
| `notes`          | TEXT       |                                                                                                                                        |

No `valid_from` / `valid_to` columns any more; version coverage comes from observations.

#### `<fmt>_elements` [proposed]

| column               | type         | notes                                                                                                         |
|----------------------|--------------|---------------------------------------------------------------------------------------------------------------|
| `id`                 | INTEGER PK   |                                                                                                               |
| `representation_id`  | FK           |                                                                                                               |
| `step_option_id`     | FK, nullable | which conceptual option this element carries (NULL for structural/unmapped elements). **Provisional**, see open question 5 |
| `xml_path`           | TEXT         | `Option/@state`, `Calculation/text()` (same convention as `display_map.yaml`)                                 |
| `value_type`         | TEXT         |                                                                                                               |
| `allowed_values`     | TEXT (JSON)  | e.g. `["True","False"]` or enum codes                                                                         |
| `default_value`      | TEXT         |                                                                                                               |
| `always_present`     | INTEGER      | 0/1; does FM emit it even when it's the default/hidden?                                                       |
| `position`           | INTEGER      | element order matters in FM XML                                                                               |

If question 5 resolves to many-to-many, the nullable FK is replaced by a `<fmt>_element_options (element_id, step_option_id)` link table; the rest of the table is unaffected, which is why it is safe to proceed before that investigation.

#### `<fmt>_observations` [decided: observation-based versioning]

| column              | type           | notes                                                  |
|---------------------|----------------|--------------------------------------------------------|
| `representation_id` | FK             | PK is (`representation_id`, `source_id`)               |
| `source_id`         | FK -> `sources` | carries the FM version (and file/date) of the export   |

### 3.8 `ui_representations` [proposed, updated]

How the step reads in the Script Editor. Same observation pattern as the XML families, plus locale.

| column             | type       | notes                                                                                                      |
|--------------------|------------|------------------------------------------------------------------------------------------------------------|
| `id`               | INTEGER PK |                                                                                                            |
| `script_step_id`   | FK         |                                                                                                            |
| `locale`           | TEXT       | `en` to start. UI text is localized, so locale is part of the shape's identity                             |
| `shape_hash`       | TEXT       | hash of the display template + option layout; UNIQUE with (`script_step_id`, `locale`)                     |
| `display_name`     | TEXT       | name as shown in the editor (can differ from the step name, cf. `displayName` in `display_map.yaml`)       |
| `display_template` | TEXT       | e.g. `Commit Transaction [ Skip data entry validation ; Force commit ]`, placeholders for option slots     |
| `example_text`     | TEXT       | a real line captured from a printout/PDF                                                                   |

`ui_observations (ui_representation_id, source_id)` mirrors the XML observation tables.

### 3.9 `ui_options` [proposed]

Replaces the per-option part of `display_map.yaml` (which is imported once and then retired).

| column                    | type         | notes                                          |
|---------------------------|--------------|------------------------------------------------|
| `id`                      | INTEGER PK   |                                                |
| `ui_representation_id`    | FK           |                                                |
| `step_option_id`          | FK, nullable | provisional, same caveat as the element tables |
| `label`                   | TEXT         |                                                |
| `display_location`        | TEXT         | `inline`, `continuation`, `dialog_only`        |
| `position`                | INTEGER      | order within the line                          |
| `omit_when_false`         | INTEGER      | 0/1                                            |
| `true_text`, `false_text` | TEXT         |                                                |
| `enum_display`            | TEXT (JSON)  | value -> display text, or move to a child table |

### 3.10 `sources` [proposed]

Provenance. Every fact that came from somewhere should say where. Observations point at a source, and the source points at the FM version, so **`sources` is what ties a representation to a version**.

| column          | type         | notes                                                                                   |
|-----------------|--------------|-----------------------------------------------------------------------------------------|
| `id`            | INTEGER PK   |                                                                                         |
| `kind`          | TEXT         | `help_page`, `clipboard_export`, `saxml_export`, `ddr_export`, `pdf_printout`, `manual` |
| `fm_version_id` | FK, nullable | version of FileMaker that produced it                                                   |
| `uri_or_path`   | TEXT         | URL or repo-relative file                                                               |
| `captured_at`   | TEXT         |                                                                                         |
| `sha256`        | TEXT         | nullable; for files                                                                     |

### 3.11 `help_pages` [decided: scrape and keep raw]

Raw scrape of help.claris.com so help content can be re-parsed without re-fetching, and parser changes never lose data.

| column         | type           | notes                                                                                                 |
|----------------|----------------|-------------------------------------------------------------------------------------------------------|
| `id`           | INTEGER PK     |                                                                                                       |
| `url`          | TEXT           | e.g. `https://help.claris.com/en/pro-help/content/commit-transaction.html`                            |
| `locale`       | TEXT           | `en` (the URL path carries the locale)                                                                |
| `help_version` | TEXT, nullable | which FileMaker release the help site documented at fetch time (the site is a moving "latest" target) |
| `fetched_at`   | TEXT           |                                                                                                       |
| `http_status`  | INTEGER        |                                                                                                       |
| `raw_html`     | TEXT           | verbatim response body                                                                                |
| `raw_markdown` | TEXT, nullable | optional cleaned conversion, if we produce one                                                        |
| `sha256`       | TEXT           | of `raw_html`; skip re-parsing when unchanged                                                         |

UNIQUE (`url`, `fetched_at`): keep history of fetches rather than overwrite. `script_step_localizations.help_page_id` points at the fetch the parsed text came from. Worth checking help.claris.com terms of use before bulk scraping (rate-limit politely either way).

### 3.12 Future: functions catalogue [decided: in scope later]

Not designed yet, but the schema above should not block it. Hooks that already exist:
- `step_options.value_type = 'calculation'` marks where a calculation can appear.
- Likely shape later: `functions` (+ localizations, + `function_parameters`), with the same observation-based XML/UI representation pattern, and a link table from `step_options` (or from script *instances*) to the functions they use.
- Calculations embed function names as text in XML, so function representations probably need their own tokenization notes. That is a separate brainstorm.

### 3.13 Step configurations and conditional options [proposed, from the EverythingBagel plan, see section 8]

A concrete example from the help pages: **Go to Record/Request/Page**. With `First` selected there are no further options; with `Next` (or `Previous`) the extra option **Exit after last** becomes available. The help page only says this in prose ("Exit after last ... if Next or Previous is selected"), so it is a candidate for the first `step_option_conditions` row: option `exit_after_last` depends on option `record` (the First/Last/Previous/Next/By Calculation choice) being `next` or `previous`, and the sample script needs at least a `First` configuration and a `Next` configuration to prove it from XML and UI.

Today the sample script has **one instance per step**, so "a step's XML shape" is implicitly "the shape of that one instance". That is not enough: many steps expose options *only when another option is set a particular way* (e.g. a dialog choice that reveals a target field, a checkbox that adds a sub-dialog). One instance cannot show those options. We will need **several configurations of the same step** in the sample file, and the schema has to know which configuration a representation came from.

New tables:

`step_configurations`: a named, deliberate setting of a step, as authored in the sample file.

| column           | type       | notes                                                                                                |
|------------------|------------|------------------------------------------------------------------------------------------------------|
| `id`             | INTEGER PK |                                                                                                      |
| `script_step_id` | FK         |                                                                                                      |
| `key`            | TEXT       | short stable name, e.g. `default`, `with-target-field`, `all-options-on`. UNIQUE with the step       |
| `description`    | TEXT       | what is being exercised and why                                                                      |
| `is_baseline`    | INTEGER    | exactly one per step: the configuration used for the "plain" representation                          |
| `setting_summary`| TEXT (JSON)| the option values chosen, as `{option_key: value}`, for humans and for diffing                       |
| `location`       | TEXT       | where it lives in the sample file (script name + step index) so the importer can find it again      |

Representation tables gain a nullable-until-needed `configuration_id` FK, and the uniqueness rule becomes (`script_step_id`, `configuration_id`, `shape_hash`). Observations are unchanged.

`step_option_conditions`: records "this option is only exposed when ...".

| column                | type         | notes                                                                                           |
|-----------------------|--------------|-------------------------------------------------------------------------------------------------|
| `id`                  | INTEGER PK   |                                                                                                 |
| `step_option_id`      | FK           | the option that appears conditionally                                                           |
| `depends_on_option_id`| FK           | the controlling option                                                                          |
| `operator`            | TEXT         | `equals`, `not_equals`, `is_set`, ...                                                           |
| `value`               | TEXT         | the controlling value                                                                           |
| `group_id`            | INTEGER, nullable | conditions sharing a group are AND-ed; separate groups are OR-ed (only if we find a real need) |
| `discovered_via_configuration_id` | FK, nullable | the configuration that proved it                                                   |

Both tables are provisional: we should not finalize them until the first few steps have been worked through in the sample file (section 8). Open sub-questions: are conditions always one controlling option, or sometimes chains (A reveals B reveals C)? Is "which options are visible" better stored as data (conditions) or derived by diffing the XML/UI of two configurations? Probably both: derive first, then record as a condition once understood.

---

## 4. Versioning strategy [decided]

Requirement: the data must be queryable **(a) for a specific FM version** and **(b) as of the most recently observed version**.

The earlier valid-range design (`valid_from`/`valid_to` on each representation) is replaced by **observations**:

- A representation row = one distinct shape (identified by `shape_hash`) for a step.
- An observation row = "this shape was seen in this source", and the source knows its FM version.
- When a new export is loaded: compute each step's `shape_hash`. If a row with that hash exists, add an observation; otherwise insert a new representation and an observation. Unchanged steps cost one tiny observation row, not a duplicate.

Queries (sketch):

```sql
-- (b) current shape: the representation seen at the highest observed version
SELECT r.* FROM clipboard_xml_representations r
JOIN clipboard_xml_observations o ON o.representation_id = r.id
JOIN sources s ON s.id = o.source_id
JOIN fm_versions v ON v.id = s.fm_version_id
WHERE r.script_step_id = :step
ORDER BY v.sort_key DESC LIMIT 1;

-- (a) shape as of version :V, "most recent observation at or before V"
... WHERE r.script_step_id = :step AND v.sort_key <= :V_sort_key
ORDER BY v.sort_key DESC LIMIT 1;

-- (a, strict) shape actually observed at exactly :V: same query with v.sort_key = :V_sort_key
```

Both "as of" and "exact" are useful and are different questions: "as of" *infers* that a shape holds until a later observation changes it, while "exact" returns only what we directly saw. Views (`current_*`, `*_as_of`) can wrap these once `schema.sql` exists.

This also answers the earlier inferred-vs-observed concern: we never store an inferred range, so we cannot store a wrong one. Gaps between exported versions simply show up as gaps in observations.

---

## 5. Open questions

Status key: **[decided]**, **[deferred]**, **[investigate]**. Original answers are quoted; "Plan impact" is how the plan above changed.

1. **Observed vs. inferred versions.** [decided]
   > I plan to have the data be queryable either by specific version, or by most-recently-observed version.

   Plan impact: replaced `valid_from`/`valid_to` with `<fmt>_observations` join tables (section 4). Both query styles are supported; `sources.fm_version_id` is the single place a version attaches.

2. **Which XML formats do we really want?** [decided]
   > Since they differ so much, I think separate tables would be better

   Plan impact: section 3.6 is now three table families (clipboard, SAXML, DDR). Only clipboard has data today. Open sub-question: which format do we load second, SAXML (likely, it is the current official export) or DDR?

3. **Step identity.** [deferred]
   > I can't confidently answer that. Let's defer this

   Plan impact: no `step_aliases` table for now. `fm_step_id` stays `UNIQUE` as a *provisional* natural key, and `script_steps` has a surrogate `id` so that, if the assumption turns out wrong, everything else keeps pointing at the surrogate. `inventory.json` already has a `names.aliases` field that we can consult when we revisit this. Trigger for revisiting: loading a second FM version's XML (any step whose ID or name differs will show up immediately).

4. **Localization.** [decided]
   > It's probably a good idea to store multiple locales from the start, even if we only have English content initially.

   Plan impact: human-readable text moved out of `script_steps` and `step_options` into `*_localizations` tables keyed by (`id`, `locale`). `ui_representations` and `help_pages` carry `locale`; examples need a locale column too (3.4, added). Only `en` rows exist initially.

5. **Option modelling.** [investigate]
   > I'm unsure, we will need to investigate this further.

   Plan impact: keep the nullable `step_option_id` FK in `*_elements` and `ui_options` as a provisional link. Suggested investigation, using data we already have: for all 207 steps in `script.xml`, count how many XML elements/attributes correspond to each displayed option in `display_map.yaml`. Any option with >1 element, or element with >1 option, is evidence for many-to-many. If everything is 1:1 or 1:N in one direction, the FK stays (on the right side). See next steps.

6. **Calculations and functions.** [decided: in scope later]
   > Yes, I had already started thinking about this also

   Plan impact: added 3.12 as a placeholder. No tables yet; the observation/localization patterns are meant to be reusable for a `functions` catalogue.

7. **Source of truth for help content.** [decided]
   > Scraping help.claris.com into the DB seems like a good approach, as it allows us to keep the raw HTML/markdown and re-parse it as needed.

   Plan impact: new `help_pages` table (3.11) holding the raw response; `help_url`/`help_fetched_at` removed from `script_steps` in favor of `script_step_localizations.help_page_id`. Parsing into `description`, `step_options`, `step_examples` and `step_compatibility` becomes a repeatable step that reads from `help_pages`.

8. **Migration of `display_map.yaml`.** [decided]
   > Likely best as a one time import, then we retire the YAML

   Plan impact: the importer is a one-shot script. Because the DB becomes the only home for that curated data, see question 9: the DB (or a text dump of it) must be under version control.

9. **Where does the DB get built?** [decided]
   > analyze.py will likely end up retired also. It might end up being best to check in a `schema.sql` and migrations.
   >
   > Go with the SQL dump

   Plan impact: the canonical, checked-in artifacts are `schema.sql`, numbered migrations, and a **deterministic SQL dump** of the whole catalogue (`sqlite3 catalogue.sqlite .dump`, with stable row ordering so diffs stay readable). The `.sqlite` file is rebuilt from the dump and is git-ignored. `analyze.py` is retired once the importer has run.

   Implications to design for:
   - A `make`-style pair of commands: `build` (dump -> `.sqlite`) and `dump` (`.sqlite` -> dump). Dump after every change that matters; consider a pre-commit check that the dump matches the DB.
   - Dump determinism: `.dump` order follows rowids/insertion, so write rows in a stable order and avoid volatile columns where possible. Raw HTML in `help_pages` makes the dump big and noisy; options are to dump that table to its own file (`help_pages.sql`) so step-catalogue diffs stay clean, or compress it. Decide when we see the real size.
   - Merge conflicts in a single large dump file are painful. Splitting the dump into one file per table (or per table family) keeps conflicts local. Leaning: one file per table in a `catalogue/` directory.

10. **Script instances / inventory.json.** [decided: we still need an inventory-style export]
    > I don't fully recall the purpose of inventory.json any longer, and might need a refresher
    >
    > we'll need something akin to the inventory.json even if it isn't identical. I've previously used this in order to help drive decisions in other sister repos.

    **Refresher** (from `docs/planned_shape.md`, the README and the current `output/inventory.json`):
    - `analyze.py` joins two inputs: the clipboard XML of one script (`to_analyze/script.xml`, one instance of every step type, 207 steps) and the printed PDF of that script.
    - `inventory.json` has two halves. **`stepDefinitions`** (204 entries, one per unique step ID) is the catalogue: names, kind flags, and each option's XML path and display info. **`scriptInstances`** (207 entries) is the concrete steps of that one sample script, with raw XML, parsed values and the matched PDF line.

    Plan impact: the DB is the source of truth and `inventory.json` becomes a **generated export** of it (new section 7). It is a *read-only derived artifact*: sister repos consume the JSON and never need to open SQLite, and nobody edits the JSON by hand. `scriptInstances` themselves are still importer input only (the verbatim XML becomes `example_xml`, the PDF line becomes `ui_representations.example_text`); the export can surface them as examples rather than as a separate half.

---

## 6. Next steps (revised)

1. ~~Decide the two remaining flags~~ Done: SQL dump (Q9); inventory-style JSON export (Q10).
2. ~~Find out what the sister repos read from `inventory.json`~~ Done for `fmscriptui` (section 7, "Consumers"): it was a one-time seed, not a live dependency. Still to confirm whether other sister repos exist.
3. **Option-mapping investigation** (Q5): script over `script.xml` + `display_map.yaml` that reports option-to-element cardinality. Settles FK vs. link-table before `schema.sql` is written.
4. **Write `schema.sql`** (plus migration 0001) from the sections above: reference tables (`fm_versions`, `sources`), `script_steps` + localizations, `step_*`, the clipboard XML family, `ui_*`, `help_pages`. Create the SAXML and DDR families later (their columns are guesses today).
5. **One-shot importer** from `inventory.json` + `display_map.yaml` + PDF-matched text into the clipboard XML family and `ui_*` tables, recording one `sources` row for the export and its FM version. `inventory.json` has `sourceVersion: null`, so we need to determine the FM version of `script.xml` / `EverythingBagel.fmp12` first.
6. **Dump tooling:** `build` / `dump` commands and the determinism rules from Q9; commit the first dump.
7. **Export script** (`export_inventory`): DB -> `inventory.json` (section 7). Diff its output against the current `output/inventory.json` as the acceptance test for the importer, since the two should agree on everything the old file carried.
8. **Help scraper** (separate script): fetch step pages into `help_pages`, then parse into `script_step_localizations`, `step_options`, `step_examples`, `step_compatibility`. Prototype on 3-4 steps first (Commit Transaction, Go to Layout, Set Variable, Perform Script).
9. **Then retire** `display_map.yaml` and `analyze.py`.
10. **Later:** SAXML export from `EverythingBagel.fmp12` and its table family; step identity (Q3) once a second FM version is loaded; functions catalogue (3.12; consider moving earlier, since `fmscriptui` hand-maintains its function lists).

---

## 7. Inventory export (`inventory.json` successor) [proposed]

Purpose: give other repos a stable, self-contained, machine-readable view of the catalogue to drive decisions, without coupling them to the SQLite schema.

**Principles**
- **Generated, never edited.** Produced from the DB by one script; checked in or published per sister-repo needs (open question below).
- **Versioned contract.** Keep a `schemaVersion` field (today: `fm-script-step-inventory/v1`). The DB schema can churn freely; the export's shape changes only deliberately, with a bump. Not required to equal the old shape, but **additive changes keep consumers working**, so keep the old field names where the data still exists.
- **Parameterized by the two version queries from section 4:** `--as-of <fm_version>` (default: most recently observed) and `--exact <fm_version>`, plus `--locale` (default `en`), and `--format clipboard|saxml|ddr` to pick which XML family populates the `xml` block.
- **Deterministic output** (sorted keys and stable ordering) so it diffs cleanly.
- **Provenance in the header:** which FM version the data is "as of", which sources contributed, DB dump commit/hash, generation time.

**Sketch of the shape** (old names kept where possible)

```json
{
  "schemaVersion": "fm-script-step-inventory/v2",
  "generatedFrom": { "dumpHash": "...", "asOfVersion": "21.0.1", "locale": "en", "xmlFormat": "clipboard" },
  "fileMaker": { "product": "FileMaker Pro", "observedVersions": ["21.0.1"] },
  "stepDefinitions": [
    {
      "stepKey": "commit-transaction",
      "fmStepId": 215,
      "names": { "xml": "...", "display": "...", "canonical": "Commit Transaction", "aliases": [] },
      "kind": { "category": "Control", "controlFlowRole": null, "isContainerStep": false, "isTerminatorStep": false },
      "origin": { "introducedIn": "18.0", "deprecatedIn": null, "removedIn": null },
      "compatibility": { "pro": true, "go": true, "webdirect": true, "server": true },
      "description": "...",
      "options": [
        { "key": "skip_data_entry_validation", "type": "boolean", "xmlPath": "Option/@state",
          "display": { "label": "...", "location": "inline", "omitWhenFalse": true, "trueText": "...", "falseText": null } }
      ],
      "xml":     { "exampleXml": "...", "observedIn": ["21.0.1"] },
      "display": { "template": "...", "exampleText": "..." },
      "examples": []
    }
  ]
}
```

Differences from v1 worth noting:
- Gains: help-derived `description`, `origin`, `compatibility`, `examples`, and per-step `observedIn` versions.
- `scriptInstances` is dropped as a top-level half; each definition carries its example XML and display text instead. If a consumer needs the old instances list, we can add an optional `--include-instances` flag later.
- `sources` block becomes `generatedFrom`, because sources are now many rows in the DB rather than one file.

**Consumers** [researched: `fmscriptui`]

I looked at `~/webdev/fmscriptui` (the `filemaker-script` fence renderer). Findings:

- It has **no runtime or build-time reference to `inventory.json`** (nothing in the repo mentions it). So `inventory.json` was a *kickoff/seed input* you used to write the `src/` files, not a live dependency. That means the export has no existing consumer contract to break, and freedom to reshape.
- What `src/` contains today is the **hand-written residue** of that kickoff, i.e. facts the catalogue should now own:

  | `fmscriptui` file | Hand-maintained data | Catalogue source |
  |---|---|---|
  | `src/render.js` | `BLOCK_OPEN` (`If`, `Loop`), `BLOCK_MID` (`Else If`, `Else`), `BLOCK_CLOSE` (`End If`, `End Loop`) | `script_steps.control_flow_role` (+ container/terminator flags). Note these sets are **incomplete**: no `Open Transaction`/`Commit` pairing, no `Exit Loop If`. The catalogue should be authoritative. |
  | `src/render.js` | `HIGHLIGHTED_STEPS` (a cosmetic subset, about 20 names) | A consumer-side styling choice. Could be derived from a tag/category in the export (e.g. "control flow", "transaction", "script call") rather than stored per step in the DB. |
  | `src/render.js`, `FENCE_FORMAT.md` | Step display names, the `Key: Value` option labels used in the fence | `ui_representations` / `ui_options` labels |
  | `src/filemaker-grammar.js` | ~hundreds of **calculation function names**, grouped by hand into categories (Math, Text, Date/Time, JSON, ...), plus keywords/constants | The future **functions catalogue** (3.12). Strong evidence it is needed: the lists are plainly incomplete (e.g. newer functions) and are consumed by three separate highlighters (hljs, fallback, CodeMirror). |
  | `improvements_brainstorming_and_roadmap.md` | Wants **round-tripping with `fmxmlsnippet`** (step IDs, option values), per-step metadata, and an LLM-friendly authoring format | `fm_step_id`, `xml_path` per option, and the clipboard XML family. This roadmap is a direct customer for the DB. |

What this means for the plan:

1. **The export should serve code generation, not just reading.** The use case is "generate/refresh source files in a sister repo". Beyond `inventory.json`, consider additional *targets* produced by the same export script, each a thin projection of the DB:
   - `inventory.json`: the general, complete dump (as sketched above).
   - Optional generated modules, e.g. `fm-steps.js` (name -> `{id, role, category}` and block open/mid/close sets) and `fm-functions.js` (function names by category), so `fmscriptui` can `import` them instead of keeping hand-edited sets. Only worth building once `fmscriptui` actually wants them.
2. **Keep styling concerns out of the DB.** `HIGHLIGHTED_STEPS` is a presentation decision. The DB provides facts (category, role); consumers decide colors. If a shared tag helps, store neutral semantic tags (`transaction`, `script-call`, `error-handling`) not "highlight".
3. **Include fields that support XML <-> fence conversion** (step id, option xml paths, enum values, display labels) since that is the roadmap direction, even though no one consumes them yet.
4. **Functions move up in priority** relative to my earlier "later" placement: they are the single biggest hand-maintained dataset in the sister repo. Still a separate brainstorm, but worth scheduling soon after the steps catalogue.

Remaining questions: (1) are there *other* sister repos besides `fmscriptui` that used `inventory.json`? (2) Should generated code files be committed in the consumer repo (simple, reviewable) or pulled at build time? (3) Is `export/` in this repo the right publish location, or should the consumer fetch from a tagged release?

---

## 8. Backlog (added items, not yet scheduled)

Items below were raised after the plan above was drafted. Each is a project in its own right; they are recorded here so the schema work does not accidentally block them.

### 8.1 Refine `EverythingBagel.fmp12` into a complete, maintainable test bed

Goal: the sample file is the **experiment rig** that produces all the observation data. If it is incomplete, the catalogue is incomplete, so keeping it good is what makes the whole system maintainable.

What's planned:
- You will open the file (and this repo) from **Windows** instead of WSL2, and likely install **ProofKit** into the file. We then work together, interactively, to make the script contain everything needed.
- Each step exists once today (207 steps in `OneOfEverything`). We extend it with **multiple configurations per step** (section 3.13), because some steps reveal options only when another option is set a certain way. Walking through the variations reveals what the UI exposes and what XML it emits.
- Output of the exercise: a richer sample script (or several), plus a record of each configuration in `step_configurations` and any discovered `step_option_conditions`.

Things to work out:
- **Script organization in the file:** one big script with variants appended, one script per step (`Step: Go to Layout` containing its configurations), or one script per configuration? Per-step scripts keep the clipboard export small and make the mapping step -> configurations obvious. A naming convention like `<StepName> :: <config-key>` would let the importer parse configuration keys from the script/step comments.
- **Self-describing configurations:** put a `# (comment)` step before each configuration with a machine-readable header (config key, intent), so the importer needs no side file. (Careful: comments themselves are steps and are sometimes empty or absent in PDF printouts; the PDF-matching quirks recorded in `analyze.py` still apply.)
- **Coverage tracking:** a view/report of steps and options with **zero** configurations exercising them, and options that have never been seen both on and off. This turns "is the rig complete?" into a query.
- **Exporting from the rig:** today we use clipboard XML plus a PDF printout. SAXML (`Save a Copy as XML`) can be generated from the file directly and likely replaces the manual clipboard step; DDR is the other option. The Script Editor UI text still needs a printout/screenshot/other capture. Possibly ProofKit gives a programmatic route; to investigate when we have it installed.
- **Windows/WSL2 workflow:** the repo is currently under WSL (`~/webdev`), and Windows will see it via `\\wsl.localhost\Ubuntu\...`. Concerns to settle: FileMaker working from a UNC path vs. a local copy, line endings (CRLF vs LF in checked-in XML and dumps; add `.gitattributes`), and whether to keep a single clone or two. Also, `.fmp12` is a binary file, so history diffs are meaningless; the meaningful artifacts are the XML exports we commit alongside it.
- **FileMaker version tracking:** every export must record the exact FM version that made it (see `sources.fm_version_id`). Re-exporting from a newer FileMaker is the trigger for new observations, so the process should be a repeatable checklist.

### 8.2 Turn the Claude Code skills into maintained, self-updating repos

**Decided: approach A** (skills as repos with generated reference files). Still to do: collect which skills used `inventory.json` (you are gathering that). Approach B's query CLI stays optional.

Context: `inventory.json` was also used as source material when creating Claude Code skills. Those skills currently hold a *copy* of knowledge that the catalogue is meant to own, so they will drift as the DB improves.

Two approaches (not mutually exclusive):

| Approach | How it works | Pros | Cons |
|---|---|---|---|
| **A. Skills as repos with generated reference files** | Each skill gets its own repo. A sync/export script (the section 7 export, with a skill-specific target) regenerates the skill's reference files (`references/*.md`, JSON) from the DB. A CI job or a manual `make sync` opens a commit/PR when the DB dump changes. | Skills stay small, offline, and fast; no runtime dependency on SQLite; changes are reviewable as diffs | Needs the generation pipeline and a trigger for updates; reference data is a snapshot |
| **B. Skills query the SQLite DB directly** | The skill ships a small helper (a CLI or script, e.g. `fmcat step "Go to Layout" --as-of 21.0`) that reads the DB (built from the checked-in dump). The skill's instructions tell Claude to call it rather than read static text. | Always current; supports precise as-of-version and locale queries; no large reference files in context | Needs the DB present and a runtime (sqlite is built into Python, so little risk), plus a stable query CLI; harder to use where the skill cannot run code |

Suggested path (to discuss, not decided): build the **query CLI** once, since it also gives *us* a convenient way to inspect the DB. Then skills can use B where code can run and A (generated snapshots) where they cannot, both fed by the same export code. "Self-update" then means: when the dump changes, a script regenerates snapshots and/or the DB the skills read.

Open questions: Which skills are we talking about (the `filemaker-dev` one, plus which others)? Do they live anywhere versioned today? How do skills get distributed to other machines or teammates (plugin marketplace, a repo clone, copying into `~/.claude/skills`)? Who triggers an update: a human running a command, a git hook on dump changes, or scheduled automation?

### 8.3 Backlog ordering (suggestion)

1. Finish the schema work in section 6 up to the one-shot importer (needs nothing new).
2. 8.1 EverythingBagel refinement, **in parallel** with the help scraper. It is the long pole, and it needs your hands (Windows + FileMaker), so start it early. The first useful milestone is small: pick 3-4 steps with obviously conditional options and work out the configuration scheme on those before touching all 207.
3. Query CLI (also needed by 8.2).
4. 8.2 skills-as-repos, once the export and CLI exist.
5. Functions catalogue (3.12), which feeds both `fmscriptui` and the skills.

---

## 9. Scraper: status and findings

First version is in the repo: `scrape_help.py` (stdlib only) plus `migrations/0001_help_catalogue.sql`. `catalogue.sqlite` is git-ignored (the dump workflow from Q9 is not built yet).

```
python3 scrape_help.py fetch    # crawl reference page -> 14 category pages -> step pages, store raw HTML in help_pages
python3 scrape_help.py parse    # help_pages -> categories, steps, localizations, sections, examples, compatibility
python3 scrape_help.py status   # row counts and steps per category
```

- **Polite and resumable:** one request per second, an identifying User-Agent, and robots.txt allows these paths (checked). `fetch` skips pages already stored unless `--refresh`; every refresh keeps the older copy.
- **Raw first, parse second:** `help_pages` holds the verbatim HTML plus the page's `article:modified_time`, so parser improvements never need the network.
- **Result of the first full run:** 231 pages fetched (1 reference, 14 category, 216 step), 216 steps parsed, all with a category and an origin version, 21 distinct FileMaker versions discovered into `fm_versions`.
- **Category is stored per step** (e.g. `commit-transaction` -> `control`, `go-to-record-request-page` -> `navigation`). The step page itself does not name its category; it comes from which category page lists the step.

### Schema deltas this forced (already reflected above)

| Change | Why |
|---|---|
| `script_steps.fm_step_id` is nullable | Help pages have no numeric step IDs; the XML importer fills them in by name. Natural key until then is `slug` (the URL basename). |
| New `script_step_categories` + localizations | 14 categories with their own pages and descriptions. |
| New `script_step_sections` (position, key, heading, body_text) | Lossless store of every section on a step page (description, options, notes, see-also, related, ...). Replaces the `options_text` / `notes` / `description` columns I had proposed on `script_step_localizations`, which are now just sections with keys `ref-options`, `notes`, `ref-desc`. Keys can repeat (e.g. several examples), so the primary key is position. |
| `step_compatibility` stores help's own product keys and `Yes`/`No`/`Partial` text | Matches the page; "Partial" must not be flattened to a boolean. |
| `help_pages` gained `kind` and `page_modified_at` | Distinguishes reference/category/step pages; records when Claris last edited the page. |
| `originated_in_raw` kept on `script_steps` | Some pages say things like "6.0 or earlier"; the version row gets 6.0 and the raw wording is preserved. |

### Findings worth knowing

- **Examples are real Script Editor text**, e.g. `Go to Record/Request/Page [First]` and `Loop [ Flush: Always ]`. That makes them a free source of UI display lines for `ui_representations.example_text`, and a cross-check for the PDF-derived text.
- **Conditional options are visible in the prose**, e.g. "Exit after last ... if Next or Previous is selected". Scanning the `ref-options` sections for phrases like "if ... is selected" / "available when" could pre-populate candidates for `step_option_conditions` and tell us which steps most need multiple configurations in the sample file.
- The help site has **216 steps**, while the sample script has **207** and `inventory.json` has 204 definitions, so the sample file is missing some steps (or the names differ). The importer's name-matching report will show exactly which.
- Compatibility spans seven products; the "Pro: No/Partial" cases (12 steps) are interesting for the sample file because they indicate steps that may not appear or behave differently in Pro.

### Not done yet in the scraper

1. `step_options` are **not** structured yet. The options section is free-form (a bulleted list of option descriptions), so structuring it is a separate, judgment-heavy pass (maybe LLM-assisted, reviewed by hand). For now it is searchable text in `script_step_sections`.
2. Only locale `en`. The `--locale` flag exists, but other locales may use different URL slugs for the same step; untested.
3. The SQL dump tooling, and the importer that fills `fm_step_id` from `script.xml`.

