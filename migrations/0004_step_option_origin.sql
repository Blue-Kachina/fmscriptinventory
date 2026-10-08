-- 0004: where a step_options row came from, so provisional rows can be found and reviewed.
-- 'display_map' rows are imported once from display_map.yaml by import_sample.py (one option per top-level
-- XML element). Q5 found that grain too coarse for 31 options, which curation will split.

ALTER TABLE step_options ADD COLUMN origin TEXT NOT NULL DEFAULT 'curated';  -- 'display_map' | 'help' | 'curated'
