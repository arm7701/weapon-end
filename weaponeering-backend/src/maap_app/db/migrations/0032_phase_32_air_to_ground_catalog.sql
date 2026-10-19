UPDATE wing_products
SET description = 'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 250 ปอนด์'
WHERE status = 'active'
  AND TRIM(COALESCE(description, '')) = ''
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk81%';

UPDATE wing_products
SET description = 'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 500 ปอนด์ นิยมใช้งานมากที่สุด'
WHERE status = 'active'
  AND TRIM(COALESCE(description, '')) = ''
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk82%'
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') NOT LIKE '%gbu%'
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') NOT LIKE '%snakeye%';

UPDATE wing_products
SET description = 'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 1,000 ปอนด์ นิยมใช้งานมากที่สุด'
WHERE status = 'active'
  AND TRIM(COALESCE(description, '')) = ''
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk83%';

UPDATE wing_products
SET description = 'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 2,000 ปอนด์'
WHERE status = 'active'
  AND TRIM(COALESCE(description, '')) = ''
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk84%'
  AND replace(replace(replace(lower(product_name), ' ', ''), '-', ''), '_', '') NOT LIKE '%gbu%';

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'MK 81 (250 lb)',
    250.0,
    0.0,
    'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 250 ปอนด์',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk81%'
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'MK 82 (500 lb)',
    500.0,
    0.0,
    'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 500 ปอนด์ นิยมใช้งานมากที่สุด',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk82%'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') NOT LIKE '%gbu%'
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'MK 83 (1,000 lb)',
    1000.0,
    0.0,
    'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 1,000 ปอนด์ นิยมใช้งานมากที่สุด',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk83%'
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'MK 84 (2,000 lb)',
    2000.0,
    0.0,
    'ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 2,000 ปอนด์',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%mk84%'
      AND replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') NOT LIKE '%gbu%'
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'CBU-49 / CBU-71 (Cluster Bomb)',
    800.0,
    0.0,
    'ระเบิดพวง/ระเบิดลูกปู บรรจุลูกระเบิดขนาดเล็ก (ลูกน้อยหน่า/ลูกเกลี้ยง) ประมาณ 300 ลูกอยู่ภายใน เมื่อปล่อยจากเครื่องบิน ปลอกนอกจะแยกออกเพื่อกระจายลูกระเบิดเล็กครอบคลุมพื้นที่กว้างเกือบ 2 กิโลเมตร ใช้สำหรับจำกัดการเข้าถึงของข้าศึก (Area Denial) หมายเหตุสำคัญ: ปัจจุบันประเทศไทยได้ลงนามในสนธิสัญญาห้ามใช้ระเบิดพวง (Convention on Cluster Munitions) แล้ว จึงไม่มีการนำมาใช้งานในภารกิจหลัก',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND (
          replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%cbu%'
          OR p.product_name LIKE '%ระเบิดพวง%'
      )
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'GBU-12 (Laser-Guided, MK 82)',
    500.0,
    0.0,
    'ระเบิดนำวิถีเลเซอร์ (Laser-Guided Bomb) ฐานจาก MK 82 ควบคุมการตกด้วยระบบเซ็นเซอร์ตรวจจับลำแสงเลเซอร์',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND (
          replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%gbu12%'
          OR replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%gbu82%'
      )
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'GBU-10 / GBU-16 (Laser-Guided, MK 84)',
    2000.0,
    0.0,
    'ระเบิดนำวิถีเลเซอร์ (Laser-Guided Bomb) ฐานจาก MK 84 เช่น GBU-10 และ GBU-16 ควบคุมการตกด้วยระบบเซ็นเซอร์ตรวจจับลำแสงเลเซอร์',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND (
          replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%gbu10%'
          OR replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%gbu16%'
          OR replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%gbu84%'
      )
);

INSERT INTO wing_products (
    id, scenario_id, product_name, weight_pounds, unit_cost, description, status
)
SELECT
    lower(hex(randomblob(16))),
    s.id,
    'JDAM (Stand-off Weapon)',
    2000.0,
    0.0,
    'ระเบิดติดตั้งชุดหางนำวิถีด้วย GPS / อาวุธปล่อยร่อน (Stand-off Weapon) สามารถร่อนไปทำลายเป้าหมายได้เองจากระยะไกลสูงสุดถึง 100 กิโลเมตร ช่วยให้เครื่องบินปล่อยอาวุธนอกระยะต่อต้านของข้าศึก มีความสามารถเลี้ยวอ้อมสันเขาได้ถึง 180 องศา',
    'active'
FROM scenarios s
WHERE NOT EXISTS (
    SELECT 1 FROM wing_products p
    WHERE p.scenario_id = s.id AND p.status = 'active'
      AND (
          replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%jdam%'
          OR replace(replace(replace(lower(p.product_name), ' ', ''), '-', ''), '_', '') LIKE '%gbu31%'
      )
);
