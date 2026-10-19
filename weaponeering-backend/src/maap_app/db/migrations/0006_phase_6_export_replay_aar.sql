CREATE TABLE IF NOT EXISTS export_packages (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    export_type TEXT NOT NULL,
    export_status TEXT NOT NULL DEFAULT 'ready',
    destination_path TEXT NOT NULL DEFAULT '',
    blocked_reason TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT 'local_user',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS aar_action_items (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'aar',
    source_reference TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_export_packages_scenario
    ON export_packages(scenario_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_aar_action_items_scenario
    ON aar_action_items(scenario_id, status);
