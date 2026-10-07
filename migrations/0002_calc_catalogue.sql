-- 0002: the calculations catalogue (functions, Get constants, named constants, operators, syntax, error codes).
-- Filled by `scrape_help.py parse` (help pages) and `calc_catalogue.py curate` (calc_curated.yaml).
-- See section 10 of database_structure_brainstorming.md.

CREATE TABLE function_categories (
    id       INTEGER PRIMARY KEY,
    slug     TEXT NOT NULL UNIQUE,                  -- help URL basename: 'text-functions', 'json-functions-category'
    key      TEXT NOT NULL UNIQUE,                  -- export key: 'text', 'json', 'get'
    position INTEGER NOT NULL                       -- order on the help site
);

CREATE TABLE function_category_localizations (
    category_id  INTEGER NOT NULL REFERENCES function_categories (id),
    locale       TEXT NOT NULL,
    name         TEXT NOT NULL,                     -- 'Text functions'
    help_page_id INTEGER REFERENCES help_pages (id),
    PRIMARY KEY (category_id, locale)
);

CREATE TABLE functions (
    id                       INTEGER PRIMARY KEY,
    slug                     TEXT UNIQUE,           -- help URL basename; NULL for curated-only entries (Get)
    name                     TEXT NOT NULL UNIQUE,  -- exactly as typed in a calculation: 'JSONSetElement'
    category_id              INTEGER REFERENCES function_categories (id),
    return_type              TEXT,                  -- export dataType: 'text', 'number', 'any', ...
    return_type_raw          TEXT,                  -- help wording: 'text, number, date, time, timestamp, container'
    signature                TEXT NOT NULL,         -- help's Format line verbatim
    min_args                 INTEGER,
    max_args                 INTEGER,               -- NULL = unlimited (or not parsed; see signature_status)
    signature_status         TEXT NOT NULL,         -- 'parsed' | 'needs-review' | 'curated'
    signature_issues         TEXT,                  -- why the parser was not confident, '; '-separated
    originated_in_version_id INTEGER REFERENCES fm_versions (id),
    originated_in_raw        TEXT,
    deprecated_in_version_id INTEGER REFERENCES fm_versions (id),
    removed_in_version_id    INTEGER REFERENCES fm_versions (id)
);

CREATE TABLE function_localizations (
    function_id  INTEGER NOT NULL REFERENCES functions (id),
    locale       TEXT NOT NULL,
    purpose      TEXT,                              -- help's one-line summary (Claris text: never exported)
    summary      TEXT,                              -- our own short wording, exported (<= 300 chars)
    help_page_id INTEGER REFERENCES help_pages (id),
    PRIMARY KEY (function_id, locale)
);

CREATE TABLE function_parameters (
    id                INTEGER PRIMARY KEY,
    function_id       INTEGER NOT NULL REFERENCES functions (id),
    position          INTEGER NOT NULL,
    name              TEXT NOT NULL,                -- 'numberOfCharacters'; numbering stripped ('test1' -> 'test')
    type              TEXT NOT NULL,                -- export dataType
    type_source       TEXT NOT NULL,                -- 'inferred' (from the help description) | 'curated'
    optional          INTEGER NOT NULL,             -- 0/1
    repeatable        INTEGER NOT NULL,             -- 0/1
    group_key         TEXT,                         -- parameters sharing a group repeat together
    help_description  TEXT,                         -- help wording (never exported)
    UNIQUE (function_id, position)
);

CREATE TABLE function_compatibility (
    function_id INTEGER NOT NULL REFERENCES functions (id),
    product     TEXT NOT NULL,                      -- help's own keys, as in step_compatibility
    supported   TEXT NOT NULL,                      -- 'Yes' | 'No' | 'Partial'
    PRIMARY KEY (function_id, product)
);

-- Observation-based, like section 4: one row per (function, FM version, argument count) that was tried.
CREATE TABLE function_verifications (
    function_id   INTEGER NOT NULL REFERENCES functions (id),
    fm_version_id INTEGER NOT NULL REFERENCES fm_versions (id),
    arg_count     INTEGER NOT NULL,
    is_valid      INTEGER NOT NULL,                 -- IsValidExpression result, 0/1
    observed_at   TEXT NOT NULL,
    PRIMARY KEY (function_id, fm_version_id, arg_count)
);

-- Arguments of Get ( ... ): 'AccountName'.
CREATE TABLE get_constants (
    id                       INTEGER PRIMARY KEY,
    slug                     TEXT NOT NULL UNIQUE,  -- 'get-accountname'
    name                     TEXT NOT NULL UNIQUE,
    return_type              TEXT,
    return_type_raw          TEXT,
    originated_in_version_id INTEGER REFERENCES fm_versions (id),
    originated_in_raw        TEXT,
    deprecated_in_version_id INTEGER REFERENCES fm_versions (id),
    removed_in_version_id    INTEGER REFERENCES fm_versions (id)
);

CREATE TABLE get_constant_localizations (
    get_constant_id INTEGER NOT NULL REFERENCES get_constants (id),
    locale          TEXT NOT NULL,
    purpose         TEXT,
    summary         TEXT,
    help_page_id    INTEGER REFERENCES help_pages (id),
    PRIMARY KEY (get_constant_id, locale)
);

CREATE TABLE get_constant_compatibility (
    get_constant_id INTEGER NOT NULL REFERENCES get_constants (id),
    product         TEXT NOT NULL,
    supported       TEXT NOT NULL,
    PRIMARY KEY (get_constant_id, product)
);

-- Every h2 section of a function or Get page, losslessly (like script_step_sections).
CREATE TABLE calc_help_sections (
    help_page_id INTEGER NOT NULL REFERENCES help_pages (id),
    position     INTEGER NOT NULL,
    section_key  TEXT NOT NULL,                     -- 'ref-format', 'ref-param', 'ref-desc', ...
    heading      TEXT NOT NULL,
    body_text    TEXT NOT NULL,
    PRIMARY KEY (help_page_id, position)
);

-- Named constants: True/False, JSON types, text styles, reserved keywords ...
CREATE TABLE calc_constants (
    id                       INTEGER PRIMARY KEY,
    name                     TEXT NOT NULL UNIQUE,
    group_key                TEXT NOT NULL,         -- 'boolean', 'json-type', 'text-style'
    group_raw                TEXT,                  -- help's Category column
    value_json               TEXT,                  -- curated: '1', '"x"', NULL when not a plain value
    help_notes               TEXT,                  -- help's Notes column (never exported)
    originated_in_version_id INTEGER REFERENCES fm_versions (id),
    help_page_id             INTEGER REFERENCES help_pages (id),
    help_url                 TEXT                   -- curated link (e.g. the function page that uses it)
);

CREATE TABLE function_parameter_constants (
    parameter_id INTEGER NOT NULL REFERENCES function_parameters (id),
    constant_id  INTEGER NOT NULL REFERENCES calc_constants (id),
    PRIMARY KEY (parameter_id, constant_id)
);

CREATE TABLE calc_operators (
    id            INTEGER PRIMARY KEY,
    symbol        TEXT NOT NULL UNIQUE,             -- primary spelling: '≠'
    alternates    TEXT NOT NULL DEFAULT '[]',       -- JSON array: '["<>"]'
    name          TEXT NOT NULL,
    kind          TEXT NOT NULL,                    -- 'arithmetic' | 'text' | 'comparison' | 'logical' | ...
    arity         INTEGER NOT NULL,
    precedence    INTEGER NOT NULL,                 -- higher binds tighter
    associativity TEXT NOT NULL,                    -- 'left' | 'right' | 'none'
    help_url      TEXT
);

-- Small key/value table for syntax facts; values are JSON.
CREATE TABLE calc_syntax_rules (
    key        TEXT PRIMARY KEY,                    -- 'argumentSeparator', 'stringEscapes', ...
    value_json TEXT NOT NULL
);

CREATE TABLE error_codes (
    code                     INTEGER PRIMARY KEY,
    help_text                TEXT,                  -- help's description (Claris text: never exported)
    label                    TEXT,                  -- our own short label, exported when set
    originated_in_version_id INTEGER REFERENCES fm_versions (id),
    help_page_id             INTEGER REFERENCES help_pages (id)
);
