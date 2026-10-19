ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN takeoff_lat REAL;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN takeoff_lng REAL;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN ingress_bearing_deg REAL;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN ingress_offset_m INTEGER NOT NULL DEFAULT 5000;

CREATE TABLE IF NOT EXISTS target_weaponeering_deployment_waypoints (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    waypoint_type TEXT NOT NULL DEFAULT 'fly_through',
    label TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES target_weaponeering_deployment_plans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deployment_waypoints_plan
    ON target_weaponeering_deployment_waypoints(plan_id);
