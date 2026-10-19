CREATE TABLE IF NOT EXISTS abstract_weaponeering_options (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    option_label TEXT NOT NULL,
    effect_category TEXT NOT NULL DEFAULT 'abstract_support',
    required_capability_band TEXT NOT NULL DEFAULT 'medium',
    resource_token_type TEXT NOT NULL DEFAULT '',
    estimated_effect_score INTEGER NOT NULL DEFAULT 50,
    risk_score INTEGER NOT NULL DEFAULT 50,
    logistics_demand_score INTEGER NOT NULL DEFAULT 50,
    source_module TEXT NOT NULL DEFAULT 'manual',
    review_status TEXT NOT NULL DEFAULT 'draft',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS target_weaponeering_assessments (
    id TEXT PRIMARY KEY,
    target_card_id TEXT NOT NULL,
    abstract_weaponeering_option_id TEXT NOT NULL,
    suitability_score INTEGER NOT NULL DEFAULT 50,
    feasibility_score INTEGER NOT NULL DEFAULT 50,
    risk_score INTEGER NOT NULL DEFAULT 50,
    rationale TEXT NOT NULL DEFAULT '',
    generated_by TEXT NOT NULL DEFAULT 'user',
    review_status TEXT NOT NULL DEFAULT 'requires_review',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (abstract_weaponeering_option_id) REFERENCES abstract_weaponeering_options(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weaponeering_import_batches (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    source_reference TEXT NOT NULL DEFAULT '',
    import_status TEXT NOT NULL DEFAULT 'pending',
    validation_summary TEXT NOT NULL DEFAULT '',
    imported_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    created_by TEXT NOT NULL DEFAULT 'local_user',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scoring_profiles (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    name TEXT NOT NULL,
    ruleset_version TEXT NOT NULL DEFAULT 'phase-1-baseline',
    priority_weight INTEGER NOT NULL DEFAULT 20,
    weaponeering_weight INTEGER NOT NULL DEFAULT 20,
    logistics_weight INTEGER NOT NULL DEFAULT 20,
    readiness_weight INTEGER NOT NULL DEFAULT 15,
    risk_weight INTEGER NOT NULL DEFAULT 15,
    resource_balance_weight INTEGER NOT NULL DEFAULT 10,
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ranking_runs (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    ruleset_version TEXT NOT NULL DEFAULT 'phase-1-baseline',
    scoring_profile_id TEXT,
    generated_by TEXT NOT NULL DEFAULT 'local_user',
    run_status TEXT NOT NULL DEFAULT 'draft',
    summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (scoring_profile_id) REFERENCES scoring_profiles(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ranking_items (
    id TEXT PRIMARY KEY,
    ranking_run_id TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'target_card',
    entity_id TEXT NOT NULL,
    rank_order INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    confidence_score INTEGER NOT NULL DEFAULT 50,
    rationale TEXT NOT NULL DEFAULT '',
    breakdown_json TEXT NOT NULL DEFAULT '{}',
    review_status TEXT NOT NULL DEFAULT 'requires_review',
    override_rank_order INTEGER,
    override_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ranking_run_id) REFERENCES ranking_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plan_options (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    planning_horizon TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    generated_by TEXT NOT NULL DEFAULT 'user',
    review_status TEXT NOT NULL DEFAULT 'draft',
    rank_order INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plan_assignments (
    id TEXT PRIMARY KEY,
    plan_option_id TEXT NOT NULL,
    target_card_id TEXT,
    simulated_platform_id TEXT,
    abstract_weaponeering_option_id TEXT,
    depot_id TEXT,
    route_segment_id TEXT,
    assigned_resource_quantity INTEGER NOT NULL DEFAULT 0,
    assignment_score INTEGER NOT NULL DEFAULT 50,
    review_status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_option_id) REFERENCES plan_options(id) ON DELETE CASCADE,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE SET NULL,
    FOREIGN KEY (abstract_weaponeering_option_id) REFERENCES abstract_weaponeering_options(id) ON DELETE SET NULL
);
