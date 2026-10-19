ALTER TABLE wing_pilots ADD COLUMN squadron TEXT NOT NULL DEFAULT '';

ALTER TABLE wing_depots ADD COLUMN map_lat REAL;
ALTER TABLE wing_depots ADD COLUMN map_lng REAL;

CREATE TABLE IF NOT EXISTS wing_products (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    weight_pounds REAL NOT NULL DEFAULT 0.0,
    range_red_km REAL NOT NULL DEFAULT 0.0,
    range_orange_km REAL NOT NULL DEFAULT 0.0,
    range_yellow_dark_km REAL NOT NULL DEFAULT 0.0,
    range_yellow_light_km REAL NOT NULL DEFAULT 0.0,
    quantity INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);
