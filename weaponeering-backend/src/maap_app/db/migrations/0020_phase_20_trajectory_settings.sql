ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN cruise_speed_kt REAL NOT NULL DEFAULT 300;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN climb_speed_kt REAL NOT NULL DEFAULT 250;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN descent_speed_kt REAL NOT NULL DEFAULT 280;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN ingress_speed_kt REAL NOT NULL DEFAULT 220;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN bank_angle_deg REAL NOT NULL DEFAULT 25;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN turn_mode TEXT NOT NULL DEFAULT 'fly_by';
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN auto_toc_tod INTEGER NOT NULL DEFAULT 1;
