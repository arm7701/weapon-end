CREATE TABLE IF NOT EXISTS target_cards (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    label TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'training',
    priority_score INTEGER NOT NULL DEFAULT 3,
    complexity_score INTEGER NOT NULL DEFAULT 3,
    map_node_id TEXT,
    review_status TEXT NOT NULL DEFAULT 'draft',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (map_node_id) REFERENCES map_nodes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS target_recognition_results (
    id TEXT PRIMARY KEY,
    target_card_id TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    recognition_summary TEXT NOT NULL DEFAULT '',
    recognition_confidence_score INTEGER NOT NULL DEFAULT 50,
    missing_data_json TEXT NOT NULL DEFAULT '[]',
    generated_by TEXT NOT NULL DEFAULT 'user',
    review_status TEXT NOT NULL DEFAULT 'requires_review',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS human_review_records (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

ALTER TABLE map_nodes ADD COLUMN linked_entity_type TEXT;
ALTER TABLE map_nodes ADD COLUMN linked_entity_id TEXT;
ALTER TABLE map_nodes ADD COLUMN is_synthetic_location INTEGER NOT NULL DEFAULT 1;
