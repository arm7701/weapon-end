-- Replace product range zone columns with unit cost.

CREATE TABLE wing_products_v3 (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    weight_pounds REAL NOT NULL DEFAULT 0.0,
    unit_cost REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

INSERT INTO wing_products_v3 (
    id, scenario_id, product_name, weight_pounds, unit_cost, status, created_at, updated_at
)
SELECT
    id, scenario_id, product_name, weight_pounds, 0.0, status, created_at, updated_at
FROM wing_products;

DROP TABLE wing_products;
ALTER TABLE wing_products_v3 RENAME TO wing_products;
