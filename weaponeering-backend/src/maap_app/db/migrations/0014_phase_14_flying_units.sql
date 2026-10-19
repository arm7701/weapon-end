CREATE TABLE IF NOT EXISTS wing_flying_units (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    wing_id TEXT NOT NULL,
    unit_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (wing_id) REFERENCES air_wings(id) ON DELETE CASCADE
);

ALTER TABLE wing_aircraft ADD COLUMN flying_unit_id TEXT
    REFERENCES wing_flying_units(id) ON DELETE SET NULL;

ALTER TABLE wing_pilots ADD COLUMN flying_unit_id TEXT
    REFERENCES wing_flying_units(id) ON DELETE SET NULL;

INSERT INTO wing_flying_units (id, scenario_id, wing_id, unit_name)
SELECT
    'fu-' || wing_id || '-' || hex(randomblob(4)),
    scenario_id,
    wing_id,
    squadron
FROM (
    SELECT DISTINCT scenario_id, wing_id, squadron
    FROM wing_aircraft
    WHERE squadron != '' AND status = 'active'
    UNION
    SELECT DISTINCT scenario_id, wing_id, squadron
    FROM wing_pilots
    WHERE squadron != '' AND status = 'active' AND wing_id IS NOT NULL
);

UPDATE wing_aircraft
SET flying_unit_id = (
    SELECT fu.id
    FROM wing_flying_units fu
    WHERE fu.wing_id = wing_aircraft.wing_id
      AND fu.unit_name = wing_aircraft.squadron
      AND fu.scenario_id = wing_aircraft.scenario_id
      AND fu.status = 'active'
    LIMIT 1
)
WHERE squadron != '';

UPDATE wing_pilots
SET flying_unit_id = (
    SELECT fu.id
    FROM wing_flying_units fu
    WHERE fu.wing_id = wing_pilots.wing_id
      AND fu.unit_name = wing_pilots.squadron
      AND fu.scenario_id = wing_pilots.scenario_id
      AND fu.status = 'active'
    LIMIT 1
)
WHERE squadron != '' AND wing_id IS NOT NULL;
