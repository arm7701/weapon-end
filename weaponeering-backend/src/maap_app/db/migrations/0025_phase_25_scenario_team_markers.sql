CREATE TABLE IF NOT EXISTS scenario_team_markers (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('blue', 'red')),
    label TEXT NOT NULL,
    map_lat REAL NOT NULL,
    map_lng REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scenario_team_markers_scenario
    ON scenario_team_markers(scenario_id);
