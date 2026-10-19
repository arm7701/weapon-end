CREATE TABLE IF NOT EXISTS ai_interactions (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT '',
    entity_id TEXT NOT NULL DEFAULT '',
    request_type TEXT NOT NULL,
    sanitized_prompt TEXT NOT NULL DEFAULT '',
    sanitized_output TEXT NOT NULL DEFAULT '',
    classifier_result TEXT NOT NULL DEFAULT '',
    validator_result TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL DEFAULT 'requires_review',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ai_interactions_scenario
    ON ai_interactions(scenario_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_interactions_review
    ON ai_interactions(scenario_id, review_status);
