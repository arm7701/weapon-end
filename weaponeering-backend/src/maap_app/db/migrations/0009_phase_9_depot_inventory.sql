CREATE TABLE wing_depots_v2 (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_id TEXT NOT NULL,
    depot_name TEXT NOT NULL,
    map_lat REAL,
    map_lng REAL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE
);

INSERT INTO wing_depots_v2 (
    id, scenario_id, wing_id, depot_name, map_lat, map_lng, status, created_at, updated_at
)
SELECT id, scenario_id, wing_id, depot_name, map_lat, map_lng, status, created_at, updated_at
FROM wing_depots;

DROP TABLE wing_depots;
ALTER TABLE wing_depots_v2 RENAME TO wing_depots;

CREATE TABLE wing_products_v2 (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    weight_pounds REAL NOT NULL DEFAULT 0.0,
    range_red_km REAL NOT NULL DEFAULT 0.0,
    range_orange_km REAL NOT NULL DEFAULT 0.0,
    range_yellow_dark_km REAL NOT NULL DEFAULT 0.0,
    range_yellow_light_km REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

INSERT INTO wing_products_v2 (
    id, scenario_id, product_name, weight_pounds,
    range_red_km, range_orange_km, range_yellow_dark_km, range_yellow_light_km,
    status, created_at, updated_at
)
SELECT
    id, scenario_id, product_name, weight_pounds,
    range_red_km, range_orange_km, range_yellow_dark_km, range_yellow_light_km,
    status, created_at, updated_at
FROM wing_products;

DROP TABLE wing_products;
ALTER TABLE wing_products_v2 RENAME TO wing_products;

CREATE TABLE IF NOT EXISTS wing_depot_inventory (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    depot_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (depot_id, product_id),
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (depot_id) REFERENCES wing_depots(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES wing_products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wing_depot_transfers (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    from_depot_id TEXT NOT NULL,
    to_depot_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES wing_products(id) ON DELETE CASCADE,
    FOREIGN KEY (from_depot_id) REFERENCES wing_depots(id) ON DELETE CASCADE,
    FOREIGN KEY (to_depot_id) REFERENCES wing_depots(id) ON DELETE CASCADE
);
