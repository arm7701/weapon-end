ALTER TABLE target_map_detection_runs ADD COLUMN target_coordinate_id TEXT;

UPDATE target_map_detection_runs
SET target_coordinate_id = COALESCE(
    (
        SELECT tc.id
        FROM target_coordinates tc
        WHERE tc.target_card_id = target_map_detection_runs.target_card_id
          AND tc.is_primary = 1
        ORDER BY tc.sort_order ASC
        LIMIT 1
    ),
    'legacy-' || target_card_id
);

CREATE TABLE target_map_detection_runs_new (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    target_card_id TEXT NOT NULL,
    target_coordinate_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_file_name TEXT,
    radius_m INTEGER NOT NULL,
    capture_radius_m INTEGER NOT NULL,
    source_image_name TEXT,
    object_count INTEGER NOT NULL DEFAULT 0,
    detection_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE,
    UNIQUE(target_card_id, target_coordinate_id)
);

INSERT INTO target_map_detection_runs_new (
    id, scenario_id, target_card_id, target_coordinate_id,
    model_name, model_file_name, radius_m, capture_radius_m,
    source_image_name, object_count, detection_message, created_at, updated_at
)
SELECT
    id, scenario_id, target_card_id, target_coordinate_id,
    model_name, model_file_name, radius_m, capture_radius_m,
    source_image_name, object_count, detection_message, created_at, updated_at
FROM target_map_detection_runs;

DROP TABLE target_map_detection_runs;

ALTER TABLE target_map_detection_runs_new RENAME TO target_map_detection_runs;

CREATE INDEX IF NOT EXISTS idx_target_map_detection_runs_coordinate
    ON target_map_detection_runs(target_card_id, target_coordinate_id);
