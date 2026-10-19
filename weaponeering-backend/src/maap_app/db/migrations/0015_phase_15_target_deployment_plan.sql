CREATE TABLE IF NOT EXISTS target_weaponeering_deployment_plans (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    target_card_id TEXT NOT NULL UNIQUE,
    wing_id TEXT NOT NULL,
    flying_unit_id TEXT NOT NULL,
    aircraft_id TEXT NOT NULL,
    aircraft_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE,
    FOREIGN KEY (flying_unit_id) REFERENCES wing_flying_units(id) ON DELETE CASCADE,
    FOREIGN KEY (aircraft_id) REFERENCES wing_aircraft(id) ON DELETE CASCADE
);
