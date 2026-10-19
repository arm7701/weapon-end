ALTER TABLE wing_products ADD COLUMN description TEXT NOT NULL DEFAULT '';

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'MK 15 (High-Drag Bomb)',
    500.0,
    0.0,
    'ระเบิดติดตั้งหางหน่วงแรงกังหัน (หางเตะ) สำหรับการทิ้งระเบิดในระยะต่ำ เพื่อให้เครื่องบินรบสามารถบินพ้นรัศมีแรงระเบิด โดยระเบิดจะตกทำมุมชันเกือบ 90 องศา',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1
    FROM wing_products p
    WHERE p.scenario_id = s.id
      AND p.status = 'active'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk15%'
);
