ALTER TABLE scenario_team_markers
    ADD COLUMN unit_type TEXT NOT NULL DEFAULT 'generic'
    CHECK (unit_type IN (
        'generic',
        'radar',
        'tank',
        'small_arms',
        'artillery',
        'anti_air'
    ));
