CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    name TEXT NOT NULL,
    organization_type TEXT NOT NULL DEFAULT 'unit',
    map_lat REAL,
    map_lng REAL,
    location_label TEXT NOT NULL DEFAULT '',
    is_synthetic_location INTEGER NOT NULL DEFAULT 1,
    readiness_summary TEXT NOT NULL DEFAULT 'unknown',
    review_status TEXT NOT NULL DEFAULT 'draft',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS platform_types (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    label TEXT NOT NULL,
    capability_band TEXT NOT NULL DEFAULT 'medium',
    resource_cost_score INTEGER NOT NULL DEFAULT 50,
    support_need_score INTEGER NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulated_platforms (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    organization_id TEXT,
    platform_type_id TEXT,
    label TEXT NOT NULL,
    capability_band TEXT NOT NULL DEFAULT 'medium',
    availability_score INTEGER NOT NULL DEFAULT 3,
    readiness_status TEXT NOT NULL DEFAULT 'unknown',
    readiness_note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL,
    FOREIGN KEY (platform_type_id) REFERENCES platform_types(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS platform_readiness_events (
    id TEXT PRIMARY KEY,
    simulated_platform_id TEXT NOT NULL,
    status TEXT NOT NULL,
    readiness_score INTEGER NOT NULL DEFAULT 50,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulated_platform_id) REFERENCES simulated_platforms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS depots (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    organization_id TEXT,
    name TEXT NOT NULL,
    depot_type TEXT NOT NULL DEFAULT 'abstract_store',
    map_lat REAL,
    map_lng REAL,
    capacity_score INTEGER NOT NULL DEFAULT 50,
    availability_status TEXT NOT NULL DEFAULT 'available',
    review_status TEXT NOT NULL DEFAULT 'draft',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS resource_tokens (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    token_type TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    availability_window TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS depot_inventory (
    id TEXT PRIMARY KEY,
    depot_id TEXT NOT NULL,
    resource_token_id TEXT,
    inventory_category TEXT NOT NULL DEFAULT 'support_token',
    option_label TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    availability_status TEXT NOT NULL DEFAULT 'available',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (depot_id) REFERENCES depots(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_token_id) REFERENCES resource_tokens(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS transport_assets (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    organization_id TEXT,
    label TEXT NOT NULL,
    transport_type TEXT NOT NULL DEFAULT 'ground',
    capacity_score INTEGER NOT NULL DEFAULT 50,
    readiness_status TEXT NOT NULL DEFAULT 'unknown',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS route_segments (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    origin_entity_type TEXT NOT NULL,
    origin_entity_id TEXT NOT NULL,
    destination_entity_type TEXT NOT NULL,
    destination_entity_id TEXT NOT NULL,
    origin_lat REAL,
    origin_lng REAL,
    destination_lat REAL,
    destination_lng REAL,
    distance_score INTEGER NOT NULL DEFAULT 50,
    fuel_stop_score INTEGER NOT NULL DEFAULT 50,
    route_friction_score INTEGER NOT NULL DEFAULT 50,
    availability_status TEXT NOT NULL DEFAULT 'available',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plan_scores (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    route_segment_id TEXT,
    plan_option_id TEXT,
    priority_alignment INTEGER,
    logistics_feasibility INTEGER NOT NULL,
    resource_balance INTEGER,
    risk_indicator INTEGER,
    rationale TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (route_segment_id) REFERENCES route_segments(id) ON DELETE SET NULL
);
