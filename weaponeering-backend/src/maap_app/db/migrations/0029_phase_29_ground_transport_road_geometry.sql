ALTER TABLE scenario_ground_transports
    ADD COLUMN route_mode TEXT NOT NULL DEFAULT 'direct';

ALTER TABLE scenario_ground_transports
    ADD COLUMN route_geometry_json TEXT;
