-- 0003: options, provenance, and how steps serialize (clipboard XML) and display (Script Editor).
-- Filled by the one-shot importer (section 6 step 5) and, for step_options, by help parsing + curation.
-- See sections 3.3, 3.6-3.10, 3.13 and 4 of database_structure_brainstorming.md.
-- SAXML and DDR families come later (their columns are guesses today); they will copy the clipboard ones.

-- Kind flags carried over from inventory.json (kind.*).
ALTER TABLE script_steps ADD COLUMN control_flow_role TEXT;              -- 'if', 'else', 'end_if', 'loop', ...
ALTER TABLE script_steps ADD COLUMN is_container_step INTEGER NOT NULL DEFAULT 0;
ALTER TABLE script_steps ADD COLUMN is_terminator_step INTEGER NOT NULL DEFAULT 0;

-- Where a fact came from. Observations point here, and this points at the FM version.
CREATE TABLE sources (
    id            INTEGER PRIMARY KEY,
    kind          TEXT NOT NULL,                    -- 'clipboard_export' | 'saxml_export' | 'ddr_export' | 'pdf_printout' | 'manual'
    fm_version_id INTEGER REFERENCES fm_versions (id),
    uri_or_path   TEXT NOT NULL,                    -- repo-relative file or URL
    captured_at   TEXT,                             -- ISO 8601; when the export was made, if known
    sha256        TEXT,                             -- of the file
    notes         TEXT,
    UNIQUE (kind, uri_or_path, sha256)
);

-- Conceptual options, as help documents them (Q5: one option can span several XML leaves).
CREATE TABLE step_options (
    id                       INTEGER PRIMARY KEY,
    script_step_id           INTEGER NOT NULL REFERENCES script_steps (id),
    key                      TEXT NOT NULL,         -- 'skip_data_entry_validation'
    value_type               TEXT NOT NULL,         -- 'boolean' | 'enum' | 'calculation' | 'text' | 'field' | 'script' | 'layout' | 'number' | ...
    required                 INTEGER NOT NULL DEFAULT 0,
    default_value            TEXT,
    position                 INTEGER NOT NULL,      -- order on the help page
    introduced_in_version_id INTEGER REFERENCES fm_versions (id),
    UNIQUE (script_step_id, key)
);

CREATE TABLE step_option_localizations (
    step_option_id INTEGER NOT NULL REFERENCES step_options (id),
    locale         TEXT NOT NULL,
    label          TEXT NOT NULL,
    description    TEXT,
    help_page_id   INTEGER REFERENCES help_pages (id),
    PRIMARY KEY (step_option_id, locale)
);

CREATE TABLE step_option_values (
    id             INTEGER PRIMARY KEY,
    step_option_id INTEGER NOT NULL REFERENCES step_options (id),
    value          TEXT NOT NULL,                   -- language-neutral key, usually the XML value: 'OriginalLayout'
    position       INTEGER NOT NULL,
    UNIQUE (step_option_id, value)
);

CREATE TABLE step_option_value_localizations (
    step_option_value_id INTEGER NOT NULL REFERENCES step_option_values (id),
    locale               TEXT NOT NULL,
    label                TEXT NOT NULL,             -- 'original layout'
    PRIMARY KEY (step_option_value_id, locale)
);

-- A deliberate setting of a step in the sample file (3.13). Provisional until the 8.1 rig work;
-- today every step has one baseline configuration (its instance in OneOfEverything).
-- step_option_conditions waits until the first conditional options are worked through.
CREATE TABLE step_configurations (
    id              INTEGER PRIMARY KEY,
    script_step_id  INTEGER NOT NULL REFERENCES script_steps (id),
    key             TEXT NOT NULL,                  -- 'default', 'with-target-field', ...
    description     TEXT,
    is_baseline     INTEGER NOT NULL DEFAULT 0,
    setting_summary TEXT,                           -- JSON {option_key: value}
    location        TEXT,                           -- script name + step index in the sample file
    UNIQUE (script_step_id, key)
);
CREATE UNIQUE INDEX idx_step_configurations_baseline ON step_configurations (script_step_id) WHERE is_baseline = 1;

-- ---------------------------------------------------------------------------
-- Clipboard XML (fmxmlsnippet). One row per distinct shape; versions come from observations (section 4).
-- ---------------------------------------------------------------------------

CREATE TABLE clipboard_xml_representations (
    id               INTEGER PRIMARY KEY,
    script_step_id   INTEGER NOT NULL REFERENCES script_steps (id),
    configuration_id INTEGER REFERENCES step_configurations (id),
    shape_hash       TEXT NOT NULL,                 -- of the normalized element/attribute structure, not values
    example_xml      TEXT NOT NULL,                 -- a verbatim snippet of this shape
    notes            TEXT
);
-- NULLs are distinct in a plain UNIQUE, so the missing configuration is folded to 0.
CREATE UNIQUE INDEX idx_clipboard_xml_representations_shape
    ON clipboard_xml_representations (script_step_id, IFNULL(configuration_id, 0), shape_hash);

-- One row per XML leaf (attribute or text node), and per repeat (Q5).
CREATE TABLE clipboard_xml_elements (
    id                INTEGER PRIMARY KEY,
    representation_id INTEGER NOT NULL REFERENCES clipboard_xml_representations (id),
    step_option_id    INTEGER REFERENCES step_options (id),  -- NULL for structural or not-yet-mapped leaves
    xml_path          TEXT NOT NULL,                -- index-free: 'NewWndStyles/@Close', 'TargetFields/Field/@map'
    parent_path       TEXT,                         -- the containing element: 'NewWndStyles', 'TargetFields/Field'
    repeat_index      INTEGER NOT NULL DEFAULT 0,   -- 0-based among siblings of the innermost repeating element
    value_type        TEXT,
    allowed_values    TEXT,                         -- JSON array
    default_value     TEXT,
    example_value     TEXT,                         -- value in example_xml
    always_present    INTEGER,                      -- 0/1/NULL (unknown until two configurations are compared)
    position          INTEGER NOT NULL,             -- document order within the step
    UNIQUE (representation_id, xml_path, repeat_index)
);
CREATE INDEX idx_clipboard_xml_elements_option ON clipboard_xml_elements (step_option_id);

CREATE TABLE clipboard_xml_observations (
    representation_id INTEGER NOT NULL REFERENCES clipboard_xml_representations (id),
    source_id         INTEGER NOT NULL REFERENCES sources (id),
    PRIMARY KEY (representation_id, source_id)
);

-- ---------------------------------------------------------------------------
-- Script Editor display, per locale.
-- ---------------------------------------------------------------------------

CREATE TABLE ui_representations (
    id               INTEGER PRIMARY KEY,
    script_step_id   INTEGER NOT NULL REFERENCES script_steps (id),
    configuration_id INTEGER REFERENCES step_configurations (id),
    locale           TEXT NOT NULL,
    shape_hash       TEXT NOT NULL,                 -- of display template + option layout
    display_name     TEXT,                          -- when the editor shows a different name than the step's
    display_template TEXT,                          -- 'Commit Records/Requests [ {noInteract} ; ... ]'
    example_text     TEXT                           -- a real line captured from a printout
);
CREATE UNIQUE INDEX idx_ui_representations_shape
    ON ui_representations (script_step_id, IFNULL(configuration_id, 0), locale, shape_hash);

-- One row per printed segment (the ';'-separated parts in [ ... ]), and per repeat.
CREATE TABLE ui_options (
    id                   INTEGER PRIMARY KEY,
    ui_representation_id INTEGER NOT NULL REFERENCES ui_representations (id),
    step_option_id       INTEGER REFERENCES step_options (id),
    label                TEXT,
    display_location     TEXT NOT NULL,             -- 'inline' | 'continuation' | 'dialog_only'
    position             INTEGER NOT NULL,          -- order within the line
    repeat_index         INTEGER NOT NULL DEFAULT 0,
    omit_when_false      INTEGER,
    true_text            TEXT,
    false_text           TEXT,
    example_text         TEXT,                      -- the segment as printed: 'Close:Yes'
    UNIQUE (ui_representation_id, position, repeat_index)
);
CREATE INDEX idx_ui_options_option ON ui_options (step_option_id);

-- How an option value prints (replaces display_map's allowedValues/displayText).
CREATE TABLE ui_option_value_displays (
    ui_option_id INTEGER NOT NULL REFERENCES ui_options (id),
    value        TEXT NOT NULL,                     -- XML value: 'ResizeToFit'
    display_text TEXT NOT NULL,                     -- printed text: 'Resize to Fit'
    PRIMARY KEY (ui_option_id, value)
);

CREATE TABLE ui_observations (
    ui_representation_id INTEGER NOT NULL REFERENCES ui_representations (id),
    source_id            INTEGER NOT NULL REFERENCES sources (id),
    PRIMARY KEY (ui_representation_id, source_id)
);

-- ---------------------------------------------------------------------------
-- Views: the shape seen at the highest observed version (section 4, query b).
-- "As of version V" and "exactly at V" stay parameterized queries; see section 4.
-- ---------------------------------------------------------------------------

CREATE VIEW current_clipboard_xml_representations AS
SELECT id, script_step_id, configuration_id, shape_hash, example_xml, notes, observed_version
FROM (
    SELECT r.*, v.version AS observed_version,
           ROW_NUMBER() OVER (PARTITION BY r.script_step_id, IFNULL(r.configuration_id, 0)
                              ORDER BY v.sort_key DESC, r.id DESC) AS rn
    FROM clipboard_xml_representations r
    JOIN clipboard_xml_observations o ON o.representation_id = r.id
    JOIN sources s ON s.id = o.source_id
    JOIN fm_versions v ON v.id = s.fm_version_id
)
WHERE rn = 1;

CREATE VIEW current_ui_representations AS
SELECT id, script_step_id, configuration_id, locale, shape_hash, display_name, display_template, example_text,
       observed_version
FROM (
    SELECT r.*, v.version AS observed_version,
           ROW_NUMBER() OVER (PARTITION BY r.script_step_id, IFNULL(r.configuration_id, 0), r.locale
                              ORDER BY v.sort_key DESC, r.id DESC) AS rn
    FROM ui_representations r
    JOIN ui_observations o ON o.ui_representation_id = r.id
    JOIN sources s ON s.id = o.source_id
    JOIN fm_versions v ON v.id = s.fm_version_id
)
WHERE rn = 1;
