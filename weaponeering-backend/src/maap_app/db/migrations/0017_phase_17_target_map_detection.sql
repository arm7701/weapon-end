CREATE TABLE IF NOT EXISTS target_map_detection_runs (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    target_card_id TEXT NOT NULL UNIQUE,
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
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS target_map_detection_objects (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    target_card_id TEXT NOT NULL,
    map_object_id TEXT NOT NULL,
    object_label TEXT NOT NULL,
    object_type TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    confidence REAL NOT NULL,
    center_lat REAL NOT NULL,
    center_lng REAL NOT NULL,
    polygon_json TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (run_id) REFERENCES target_map_detection_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_target_map_detection_objects_run
    ON target_map_detection_objects(run_id);

CREATE INDEX IF NOT EXISTS idx_target_map_detection_objects_target
    ON target_map_detection_objects(target_card_id);
