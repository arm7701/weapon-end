CREATE TABLE IF NOT EXISTS air_wings (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_name TEXT NOT NULL,
    map_lat REAL,
    map_lng REAL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wing_aircraft (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_id TEXT NOT NULL,
    aircraft_type TEXT NOT NULL DEFAULT 'F-16',
    squadron TEXT NOT NULL DEFAULT '',
    mission_ready TEXT NOT NULL DEFAULT 'not_ready',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wing_pilots (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_id TEXT,
    pilot_name TEXT NOT NULL,
    callsign TEXT NOT NULL DEFAULT '',
    cep_value REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS wing_depots (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_id TEXT NOT NULL,
    depot_name TEXT NOT NULL,
    capacity_pounds REAL NOT NULL DEFAULT 0.0,
    range_red_km REAL NOT NULL DEFAULT 0.0,
    range_orange_km REAL NOT NULL DEFAULT 0.0,
    range_yellow_dark_km REAL NOT NULL DEFAULT 0.0,
    range_yellow_light_km REAL NOT NULL DEFAULT 0.0,
    mission_ready TEXT NOT NULL DEFAULT 'not_ready',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wing_logistics_vehicles (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_id TEXT NOT NULL,
    vehicle_name TEXT NOT NULL,
    fuel_consumption_rate REAL NOT NULL DEFAULT 0.0,
    mission_ready TEXT NOT NULL DEFAULT 'not_ready',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE
);
