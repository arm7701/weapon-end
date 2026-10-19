PRAGMA foreign_keys = OFF;

CREATE TABLE IF NOT EXISTS target_weaponeering_deployment_aircraft (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    aircraft_id TEXT NOT NULL,
    aircraft_count INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES target_weaponeering_deployment_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (aircraft_id) REFERENCES wing_aircraft(id) ON DELETE CASCADE,
    UNIQUE(plan_id, aircraft_id)
);

INSERT INTO target_weaponeering_deployment_aircraft (
    id, plan_id, aircraft_id, aircraft_count, sort_order
)
SELECT
    'dpl-' || id || '-0',
    id,
    aircraft_id,
    aircraft_count,
    0
FROM target_weaponeering_deployment_plans
WHERE aircraft_id IS NOT NULL AND aircraft_id != '';

CREATE TABLE target_weaponeering_deployment_plans_v16 (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    target_card_id TEXT NOT NULL UNIQUE,
    wing_id TEXT NOT NULL,
    flying_unit_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE,
    FOREIGN KEY (flying_unit_id) REFERENCES wing_flying_units(id) ON DELETE CASCADE
);

INSERT INTO target_weaponeering_deployment_plans_v16 (
    id, scenario_id, target_card_id, wing_id, flying_unit_id, created_at, updated_at
)
SELECT id, scenario_id, target_card_id, wing_id, flying_unit_id, created_at, updated_at
FROM target_weaponeering_deployment_plans;

DROP TABLE target_weaponeering_deployment_plans;

ALTER TABLE target_weaponeering_deployment_plans_v16
    RENAME TO target_weaponeering_deployment_plans;

PRAGMA foreign_keys = ON;
