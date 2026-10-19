ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN cruise_altitude_ft INTEGER NOT NULL DEFAULT 25000;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN ingress_altitude_ft INTEGER NOT NULL DEFAULT 5000;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN target_altitude_ft INTEGER NOT NULL DEFAULT 1500;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN climb_rate_ft_min INTEGER NOT NULL DEFAULT 3000;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN descent_rate_ft_min INTEGER NOT NULL DEFAULT 2000;
ALTER TABLE target_weaponeering_deployment_plans ADD COLUMN return_enabled INTEGER NOT NULL DEFAULT 1;

ALTER TABLE target_weaponeering_deployment_waypoints ADD COLUMN altitude_ft INTEGER;
