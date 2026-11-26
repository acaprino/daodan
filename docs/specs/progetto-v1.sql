-- Daodan project file, schema 1. Initialize an empty database only.
PRAGMA foreign_keys = ON;
BEGIN;
PRAGMA application_id = 0x44414F44; -- "DAOD"
PRAGMA user_version = 1;

CREATE TABLE source_snapshots (
    source_id INTEGER PRIMARY KEY,
    repository_uri TEXT,
    git_commit TEXT,
    git_committed_at TEXT,
    tree_sha256 TEXT,
    inventory_policy TEXT,
    CHECK (git_commit IS NOT NULL OR tree_sha256 IS NOT NULL),
    CHECK (git_committed_at IS NULL OR git_commit IS NOT NULL),
    CHECK (tree_sha256 IS NULL OR
           (length(tree_sha256) = 64 AND tree_sha256 NOT GLOB '*[^0-9a-f]*'
            AND inventory_policy IS NOT NULL))
) STRICT;
CREATE TABLE analyses (
    analysis_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES source_snapshots,
    daodan_version TEXT NOT NULL,
    config_json TEXT NOT NULL CHECK (json_type(config_json) = 'object'),
    started_at TEXT NOT NULL
) STRICT;
CREATE TABLE revisions (
    rev INTEGER PRIMARY KEY,
    revision_uuid TEXT NOT NULL UNIQUE,
    parent_rev INTEGER REFERENCES revisions,
    analysis_id INTEGER NOT NULL REFERENCES analyses,
    kind TEXT NOT NULL CHECK (kind IN ('analysis','manual','resolution','import')),
    author TEXT NOT NULL,
    created_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    CHECK ((rev = 1 AND parent_rev IS NULL) OR
           (rev > 1 AND parent_rev IS NOT NULL AND parent_rev = rev - 1))
) STRICT;
CREATE TABLE project (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    project_uuid TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    head_rev INTEGER NOT NULL REFERENCES revisions
) STRICT;

-- Identities are never recycled. Intervals are [from_rev, until_rev).
CREATE TABLE objects (
    object_id TEXT PRIMARY KEY NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('node','edge','flow','variant','step','gap','record'))
) STRICT;
CREATE TABLE versions (
    version_id INTEGER PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects,
    from_rev INTEGER NOT NULL REFERENCES revisions,
    until_rev INTEGER REFERENCES revisions,
    provenance TEXT NOT NULL,
    UNIQUE (object_id, from_rev),
    CHECK (until_rev IS NULL OR from_rev < until_rev)
) STRICT;
CREATE UNIQUE INDEX one_open_version ON versions(object_id) WHERE until_rev IS NULL;
CREATE INDEX versions_ending ON versions(until_rev) WHERE until_rev IS NOT NULL;
CREATE INDEX versions_starting ON versions(from_rev);

CREATE TABLE nodes (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    parent_id TEXT REFERENCES objects,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    position TEXT NOT NULL CHECK (position IN ('interno','esterno','non visto')),
    status TEXT NOT NULL CHECK (status IN ('confermato','dedotto','incompleto')),
    abstraction TEXT NOT NULL CHECK (abstraction IN ('concreto','astratto')),
    catalog_id TEXT,
    attributes_json TEXT NOT NULL DEFAULT '{}' CHECK (json_type(attributes_json) = 'object')
) STRICT;
CREATE INDEX node_children ON nodes(parent_id);
CREATE TABLE edges (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    source_id TEXT NOT NULL REFERENCES objects,
    target_id TEXT NOT NULL REFERENCES objects,
    kind TEXT NOT NULL,
    grade TEXT NOT NULL CHECK (length(grade) > 0),
    profile TEXT,
    attributes_json TEXT NOT NULL DEFAULT '{}' CHECK (json_type(attributes_json) = 'object')
) STRICT;
CREATE INDEX edge_out ON edges(source_id, kind);
CREATE INDEX edge_in ON edges(target_id, kind);

CREATE TABLE flows (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    name TEXT NOT NULL,
    feature_id TEXT REFERENCES objects,
    attributes_json TEXT NOT NULL DEFAULT '{}' CHECK (json_type(attributes_json) = 'object')
) STRICT;
CREATE TABLE variants (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    flow_id TEXT NOT NULL REFERENCES objects,
    name TEXT NOT NULL,
    profile TEXT,
    condition TEXT
) STRICT;
CREATE INDEX variants_by_flow ON variants(flow_id, profile);
CREATE TABLE variant_endpoints (
    variant_version INTEGER NOT NULL REFERENCES variants(version_id),
    role TEXT NOT NULL CHECK (role IN ('entry','outcome')),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    node_id TEXT NOT NULL REFERENCES objects,
    description TEXT,
    PRIMARY KEY (variant_version, role, ordinal)
) STRICT;
CREATE TABLE steps (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    variant_id TEXT NOT NULL REFERENCES objects,
    display_order INTEGER NOT NULL CHECK (display_order >= 0),
    label TEXT NOT NULL
) STRICT;
CREATE INDEX steps_by_variant ON steps(variant_id, display_order);
CREATE TABLE step_edges (
    step_version INTEGER NOT NULL REFERENCES steps(version_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    edge_id TEXT NOT NULL REFERENCES objects,
    PRIMARY KEY (step_version, ordinal)
) STRICT;
CREATE INDEX steps_using_edge ON step_edges(edge_id);
CREATE TABLE step_transitions (
    from_step_version INTEGER NOT NULL REFERENCES steps(version_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    to_step_id TEXT NOT NULL REFERENCES objects,
    condition TEXT,
    PRIMARY KEY (from_step_version, ordinal)
) STRICT;

CREATE TABLE technical_records (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json))
) STRICT;
CREATE TABLE gaps (
    version_id INTEGER PRIMARY KEY REFERENCES versions,
    subject_id TEXT REFERENCES objects,
    description TEXT NOT NULL,
    cause TEXT NOT NULL,
    remedy TEXT
) STRICT;
CREATE TABLE evidence (
    evidence_id INTEGER PRIMARY KEY,
    analysis_id INTEGER NOT NULL REFERENCES analyses,
    kind TEXT NOT NULL CHECK (kind IN ('source','artifact')),
    locator TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    symbol TEXT,
    blob_ref TEXT,
    record_version INTEGER REFERENCES technical_records(version_id),
    CHECK (start_line IS NULL OR start_line >= 1),
    CHECK (end_line IS NULL OR (start_line IS NOT NULL AND end_line >= start_line)),
    CHECK (kind <> 'artifact' OR record_version IS NOT NULL)
) STRICT;
CREATE TABLE version_evidence (
    version_id INTEGER NOT NULL REFERENCES versions,
    evidence_id INTEGER NOT NULL REFERENCES evidence,
    PRIMARY KEY (version_id, evidence_id)
) STRICT;
CREATE INDEX versions_by_evidence ON version_evidence(evidence_id);

-- Values are JSON envelopes: {"present":false} or {"present":true,"value":...}.
CREATE TABLE manual_edits (
    edit_id INTEGER PRIMARY KEY,
    rev INTEGER NOT NULL REFERENCES revisions,
    base_rev INTEGER NOT NULL REFERENCES revisions,
    object_id TEXT NOT NULL REFERENCES objects,
    field_path TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('set','release')),
    base_json TEXT NOT NULL CHECK (json_valid(base_json)),
    value_json TEXT NOT NULL CHECK (json_valid(value_json)),
    UNIQUE (rev, object_id, field_path),
    CHECK (base_rev < rev)
) STRICT;
CREATE INDEX edits_by_field ON manual_edits(object_id, field_path, rev);
CREATE TABLE conflicts (
    conflict_id INTEGER PRIMARY KEY,
    detected_rev INTEGER NOT NULL REFERENCES revisions,
    edit_id INTEGER NOT NULL REFERENCES manual_edits,
    incoming_json TEXT NOT NULL CHECK (json_valid(incoming_json)),
    incoming_provenance TEXT NOT NULL,
    resolved_rev INTEGER REFERENCES revisions,
    UNIQUE (detected_rev, edit_id),
    CHECK (resolved_rev IS NULL OR resolved_rev > detected_rev)
) STRICT;
CREATE TABLE conflict_evidence (
    conflict_id INTEGER NOT NULL REFERENCES conflicts,
    evidence_id INTEGER NOT NULL REFERENCES evidence,
    PRIMARY KEY (conflict_id, evidence_id)
) STRICT;
COMMIT;
