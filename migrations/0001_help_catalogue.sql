-- 0001: tables needed by the help.claris.com scraper.
-- Later migrations add step_options, the XML/UI representation families, sources, etc.
-- See database_structure_brainstorming.md for the full plan.

CREATE TABLE fm_versions (
    id             INTEGER PRIMARY KEY,
    version        TEXT NOT NULL UNIQUE,            -- '19.6.1'
    major          INTEGER NOT NULL,
    minor          INTEGER NOT NULL,
    patch          INTEGER NOT NULL,
    marketing_name TEXT,
    released_on    TEXT,
    sort_key       INTEGER NOT NULL                 -- major*1000000 + minor*1000 + patch
);
CREATE INDEX idx_fm_versions_sort_key ON fm_versions (sort_key);

-- One raw fetch of one page. History is kept: a re-fetch inserts a new row.
CREATE TABLE help_pages (
    id               INTEGER PRIMARY KEY,
    url              TEXT NOT NULL,
    locale           TEXT NOT NULL,
    kind             TEXT NOT NULL,                 -- 'reference' | 'category' | 'step'
    fetched_at       TEXT NOT NULL,                 -- ISO 8601 UTC
    http_status      INTEGER NOT NULL,
    page_modified_at TEXT,                          -- <meta property="article:modified_time">
    raw_html         TEXT NOT NULL,
    sha256           TEXT NOT NULL,                 -- of raw_html
    UNIQUE (url, fetched_at)
);
CREATE INDEX idx_help_pages_url ON help_pages (url);

CREATE TABLE script_step_categories (
    id       INTEGER PRIMARY KEY,
    slug     TEXT NOT NULL UNIQUE,                  -- 'control', 'found-sets', 'pdf-files'
    position INTEGER NOT NULL                       -- order on the help site
);

CREATE TABLE script_step_category_localizations (
    category_id  INTEGER NOT NULL REFERENCES script_step_categories (id),
    locale       TEXT NOT NULL,
    name         TEXT NOT NULL,                     -- 'Control script steps'
    description  TEXT,
    help_page_id INTEGER REFERENCES help_pages (id),
    PRIMARY KEY (category_id, locale)
);

CREATE TABLE script_steps (
    id                       INTEGER PRIMARY KEY,
    slug                     TEXT NOT NULL UNIQUE,  -- 'commit-transaction' (help URL basename)
    fm_step_id               INTEGER UNIQUE,        -- NULL until the XML importer matches it up
    category_id              INTEGER REFERENCES script_step_categories (id),
    originated_in_version_id INTEGER REFERENCES fm_versions (id),
    originated_in_raw        TEXT,                  -- help text verbatim, kept when it will not parse
    deprecated_in_version_id INTEGER REFERENCES fm_versions (id),
    removed_in_version_id    INTEGER REFERENCES fm_versions (id)
);

CREATE TABLE script_step_localizations (
    script_step_id INTEGER NOT NULL REFERENCES script_steps (id),
    locale         TEXT NOT NULL,
    name           TEXT NOT NULL,
    purpose        TEXT,                            -- the one-line summary under the title
    help_page_id   INTEGER REFERENCES help_pages (id),
    PRIMARY KEY (script_step_id, locale)
);

-- Every h2 section of a step page, losslessly: 'description', 'options', 'notes', ...
CREATE TABLE script_step_sections (
    script_step_id INTEGER NOT NULL REFERENCES script_steps (id),
    locale         TEXT NOT NULL,
    position       INTEGER NOT NULL,                -- order on the page; keys can repeat (several examples)
    section_key    TEXT NOT NULL,                   -- from the heading's CSS class, e.g. 'ref-desc'
    heading        TEXT NOT NULL,
    body_text      TEXT NOT NULL,
    PRIMARY KEY (script_step_id, locale, position)
);

CREATE TABLE step_examples (
    id             INTEGER PRIMARY KEY,
    script_step_id INTEGER NOT NULL REFERENCES script_steps (id),
    locale         TEXT NOT NULL,
    position       INTEGER NOT NULL,
    title          TEXT,
    description    TEXT,
    body           TEXT NOT NULL,
    UNIQUE (script_step_id, locale, position)
);

CREATE TABLE step_compatibility (
    script_step_id INTEGER NOT NULL REFERENCES script_steps (id),
    product        TEXT NOT NULL,                   -- 'Pro', 'Go', 'WebD', 'Server', ... (help's own keys)
    supported      TEXT NOT NULL,                   -- 'Yes' | 'No' | 'Partial' (help's own values)
    PRIMARY KEY (script_step_id, product)
);
