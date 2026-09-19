PRAGMA foreign_keys = ON;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE chapters (
    chapter_number TEXT PRIMARY KEY,
    chapter_order INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL
);

CREATE TABLE scenes (
    scene_number INTEGER PRIMARY KEY,
    chapter_number TEXT NOT NULL REFERENCES chapters(chapter_number),
    scene_order_in_chapter INTEGER NOT NULL,
    title TEXT NOT NULL,
    UNIQUE (chapter_number, scene_order_in_chapter)
);

CREATE TABLE units (
    unit_id TEXT PRIMARY KEY,
    chapter_number TEXT NOT NULL REFERENCES chapters(chapter_number),
    scene_number INTEGER NOT NULL REFERENCES scenes(scene_number),
    scene_order INTEGER NOT NULL,
    global_order INTEGER NOT NULL UNIQUE,
    reference_raw TEXT NOT NULL,
    segmentation_weight INTEGER NOT NULL CHECK(segmentation_weight > 0),
    primary_reference TEXT,
    UNIQUE (scene_number, scene_order)
);

CREATE TABLE source_editions (
    source_edition_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    version TEXT,
    language_code TEXT NOT NULL,
    repository_path TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE unit_witnesses (
    witness_id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL REFERENCES units(unit_id) ON DELETE CASCADE,
    witness_order INTEGER NOT NULL,
    reference_component TEXT NOT NULL,
    book_code TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse_start INTEGER NOT NULL,
    verse_end INTEGER NOT NULL,
    segment_suffix TEXT,
    greek_text TEXT,
    source_edition_id TEXT NOT NULL REFERENCES source_editions(source_edition_id),
    source_passage_ids_json TEXT NOT NULL,
    source_token_ids_json TEXT NOT NULL,
    derivation_method TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    source_status TEXT NOT NULL,
    UNIQUE (unit_id, witness_order)
);

CREATE TABLE editions (
    edition_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL,
    language_code TEXT NOT NULL,
    locale TEXT,
    title TEXT NOT NULL,
    edition_role TEXT NOT NULL,
    version TEXT NOT NULL,
    derivation_policy TEXT NOT NULL,
    source_edition_id TEXT REFERENCES source_editions(source_edition_id),
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE unit_texts (
    edition_id TEXT NOT NULL REFERENCES editions(edition_id) ON DELETE CASCADE,
    unit_id TEXT NOT NULL REFERENCES units(unit_id) ON DELETE CASCADE,
    text TEXT,
    source_witness_id TEXT REFERENCES unit_witnesses(witness_id),
    derivation_method TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (edition_id, unit_id)
);

CREATE TABLE validation_issues (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    unit_id TEXT,
    reference_component TEXT,
    message TEXT NOT NULL
);

CREATE TABLE build_stats (
    metric TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX idx_units_scene ON units(scene_number, scene_order);
CREATE INDEX idx_witnesses_unit ON unit_witnesses(unit_id, witness_order);
CREATE INDEX idx_witnesses_ref ON unit_witnesses(reference_component);
CREATE INDEX idx_unit_texts_unit ON unit_texts(unit_id);

CREATE VIEW scene_texts AS
SELECT scene_number, edition_id, group_concat(text, ' ') AS text
FROM (
    SELECT u.scene_number, ut.edition_id, ut.text
    FROM units u
    JOIN unit_texts ut ON ut.unit_id = u.unit_id
    ORDER BY u.scene_number, u.scene_order
)
GROUP BY scene_number, edition_id;

CREATE VIEW chapter_texts AS
SELECT chapter_number, edition_id, group_concat(text, ' ') AS text
FROM (
    SELECT u.chapter_number, ut.edition_id, ut.text
    FROM units u
    JOIN unit_texts ut ON ut.unit_id = u.unit_id
    ORDER BY u.global_order
)
GROUP BY chapter_number, edition_id;

CREATE VIEW book_texts AS
SELECT edition_id, group_concat(text, ' ') AS text
FROM (
    SELECT ut.edition_id, ut.text
    FROM units u
    JOIN unit_texts ut ON ut.unit_id = u.unit_id
    ORDER BY u.global_order
)
GROUP BY edition_id;
