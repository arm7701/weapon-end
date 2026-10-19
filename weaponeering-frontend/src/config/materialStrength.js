/** Material strength parameters per structure type and typical RC strength per target type. */

const num = (key, label, unit, defaultValue = null) => ({ key, label, unit, type: 'number', defaultValue })
const text = (key, label, defaultValue = '') => ({ key, label, unit: '', type: 'text', defaultValue })

export const MATERIAL_STRENGTH = {
  คอนกรีตเสริมเหล็ก: {
    isRc: true,
    params: [
      num('fc_mpa', "f'c", 'MPa', 28),
      num('fy_mpa', 'fy', 'MPa', 400),
      num('as_mm2_per_m', 'As', 'mm²/m'),
      num('thickness_mm', 'ความหนา', 'มม.'),
    ],
    example: "f'c = 28 MPa, fy = 400 MPa",
    summary: (v) => (v.fc_mpa ? `RC: ${v.fc_mpa} MPa${v.fy_mpa ? ` / ${v.fy_mpa} MPa` : ''}` : 'RC'),
  },
  คอนกรีต: {
    isRc: false,
    params: [
      num('fc_mpa', "f'c", 'MPa', 24),
      num('thickness_mm', 'ความหนา', 'มม.'),
      num('density_kg_m3', 'Density', 'kg/m³', 2400),
    ],
    example: "f'c = 24–28 MPa",
    summary: (v) => (v.fc_mpa ? `Concrete: ${v.fc_mpa} MPa` : 'Concrete: 24–28 MPa'),
  },
  โครงเหล็ก: {
    isRc: false,
    params: [
      num('fy_mpa', 'Fy', 'MPa', 250),
      num('fu_mpa', 'Fu', 'MPa', 400),
      num('e_gpa', 'E', 'GPa', 200),
      text('section', 'หน้าตัด'),
    ],
    example: 'Fy ≈ 250–355 MPa',
    summary: (v) => (v.fy_mpa ? `Steel: Fy = ${v.fy_mpa} MPa` : 'Steel: Fy = 250–355 MPa'),
  },
  ไม้: {
    isRc: false,
    params: [num('fb_mpa', 'Fb', 'MPa'), num('fc_mpa', 'Fc', 'MPa'), num('e_gpa', 'E', 'GPa')],
    example: 'ขึ้นกับชนิด/เกรดไม้',
    summary: () => 'ไม่มีค่า RC',
  },
  ดิน: {
    isRc: false,
    params: [
      num('c_kpa', 'c', 'kPa'),
      num('phi_deg', 'φ', '°'),
      num('gamma_kn_m3', 'γ', 'kN/m³'),
      num('bearing_kpa', 'Bearing Capacity', 'kPa'),
      num('cbr_pct', 'CBR', '%'),
    ],
    example: 'ขึ้นกับผลทดสอบดิน',
    summary: () => 'ไม่มีค่า RC',
  },
  อื่นๆ: {
    isRc: false,
    params: [text('material_name', 'วัสดุ'), num('strength_mpa', 'ค่าความแข็งแรง', 'MPa')],
    example: 'Manual Input',
    summary: (v) =>
      v.material_name || v.strength_mpa
        ? `Custom: ${[v.material_name, v.strength_mpa ? `${v.strength_mpa} MPa` : ''].filter(Boolean).join(' ')}`
        : 'Custom',
  },
}

export const TARGET_TYPE_RC = {
  อาคาร: { system: 'RC Frame / Wall', fcMin: 21, fcMax: 40, keyParams: 'เสา คาน พื้น เหล็กเสริม', material: 'คอนกรีตเสริมเหล็ก' },
  สะพาน: { system: 'RC / Prestressed RC', fcMin: 28, fcMax: 60, keyParams: 'Girder, Pier, Deck, Bearing', material: 'คอนกรีตเสริมเหล็ก' },
  บังเกอร์: { system: 'Heavy RC', fcMin: 35, fcMax: 60, openEnded: true, keyParams: 'ความหนา RC, reinforcement, detailing', material: 'คอนกรีตเสริมเหล็ก' },
  คูเลน: { system: 'RC + Soil', fcMin: 21, fcMax: 35, keyParams: 'ผนัง ความหนาดิน แรงดันดิน', material: 'คอนกรีตเสริมเหล็ก' },
  รันเวย์: { system: 'PCC (คอนกรีตล้วน)', fcMin: 28, fcMax: 45, keyParams: 'ความหนาพื้น, flexural strength, subgrade', material: 'คอนกรีต' },
  โรงเก็บเครื่องบิน: { system: 'Steel + RC', fcMin: 28, fcMax: 40, keyParams: 'เสา ฐานราก truss และ connection', material: 'คอนกรีตเสริมเหล็ก' },
  เรือ: { system: 'Steel เป็นหลัก', fcMin: null, fcMax: null, keyParams: 'plate thickness, Fy, stiffener', material: 'โครงเหล็ก' },
  เรดาร์: { system: 'RC Foundation', fcMin: 28, fcMax: 40, keyParams: 'Foundation, anchor, overturning', material: 'คอนกรีตเสริมเหล็ก' },
  คลังอาวุธ: { system: 'RC / Steel', fcMin: 28, fcMax: 50, keyParams: 'ผนัง หลังคา เสา และ fire protection', material: 'คอนกรีตเสริมเหล็ก' },
  คลังเชื้อเพลิง: { system: 'RC containment + Steel tank', fcMin: 28, fcMax: 40, keyParams: 'tank shell, foundation, bund wall, fire resistance', material: 'คอนกรีตเสริมเหล็ก' },
}

export function targetRcRangeText(info) {
  if (!info || info.fcMin == null) return 'RC ไม่ใช่ตัวแปรหลัก'
  return `${info.fcMin}–${info.fcMax}${info.openEnded ? '+' : ''} MPa`
}

/** Quick-pick f'c values for a target type: low / mid / high of its typical range. */
export function targetRcChoices(info) {
  if (!info || info.fcMin == null) return []
  const mid = Math.round((info.fcMin + info.fcMax) / 2)
  return [...new Set([info.fcMin, mid, info.fcMax])]
}

export function defaultMaterialStrength(structureType, targetType) {
  const spec = MATERIAL_STRENGTH[structureType]
  if (!spec) return {}
  const values = {}
  spec.params.forEach((p) => {
    if (p.defaultValue !== null && p.defaultValue !== '') values[p.key] = p.defaultValue
  })
  const rc = TARGET_TYPE_RC[targetType]
  if ('fc_mpa' in values && rc?.fcMin != null && (structureType === 'คอนกรีตเสริมเหล็ก' || structureType === 'คอนกรีต')) {
    values.fc_mpa = targetRcChoices(rc)[1] ?? values.fc_mpa
  }
  return values
}

export function materialStrengthSummary(structureType, values) {
  const spec = MATERIAL_STRENGTH[structureType]
  if (!spec) return ''
  return spec.summary(values || {})
}

/** Keep only the parameters of the current material, numbers as numbers. */
export function cleanMaterialStrength(structureType, values) {
  const spec = MATERIAL_STRENGTH[structureType]
  if (!spec || !values) return {}
  const out = {}
  spec.params.forEach((p) => {
    const v = values[p.key]
    if (v === null || v === undefined || v === '') return
    if (p.type === 'number') {
      const n = Number(v)
      if (Number.isFinite(n)) out[p.key] = n
    } else {
      out[p.key] = String(v).trim().slice(0, 120)
    }
  })
  return out
}
