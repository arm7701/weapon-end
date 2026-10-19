CREATE TABLE IF NOT EXISTS target_coordinates (
    id TEXT PRIMARY KEY,
    target_card_id TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    map_lat REAL NOT NULL,
    map_lng REAL NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_card_id) REFERENCES target_cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_target_coordinates_card
    ON target_coordinates(target_card_id, sort_order);

INSERT INTO target_coordinates (
    id, target_card_id, label, map_lat, map_lng, sort_order, is_primary
)
SELECT
    'legacy-' || tc.id,
    tc.id,
    COALESCE(mn.label, tc.label, ''),
    mn.map_lat,
    mn.map_lng,
    0,
    1
FROM target_cards tc
INNER JOIN map_nodes mn ON mn.id = tc.map_node_id
WHERE tc.map_node_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM target_coordinates tc2 WHERE tc2.target_card_id = tc.id
  );
