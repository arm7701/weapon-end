-- Archive legacy logistics organization records that duplicate wing_data defaults.
UPDATE organizations
SET status = 'archived', updated_at = CURRENT_TIMESTAMP
WHERE status = 'active'
  AND name = 'กองบิน 1'
  AND map_lat BETWEEN 16.8120 AND 16.8130
  AND map_lng BETWEEN 100.1230 AND 100.1240;
