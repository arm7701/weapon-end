CREATE TABLE IF NOT EXISTS scenario_ground_transports (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    origin_wing_id TEXT NOT NULL,
    destination_wing_id TEXT NOT NULL,
    product_id TEXT,
    vehicle_id TEXT,
    quantity INTEGER NOT NULL DEFAULT 1,
    distance_m REAL NOT NULL,
    duration_min REAL NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (origin_wing_id) REFERENCES air_wings(id) ON DELETE CASCADE,
    FOREIGN KEY (destination_wing_id) REFERENCES air_wings(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scenario_ground_transports_scenario
    ON scenario_ground_transports(scenario_id);
