/** Map desktop/API target fields ↔ Analysis sidebar form labels (Thai UI). */

import { cleanMaterialStrength } from '../config/materialStrength'

const TARGET_TYPE_TO_TH = {
  BUILDING: 'อาคาร',
  BRIDGE: 'สะพาน',
  BUNKER: 'บังเกอร์',
  CULVERT: 'คูเลน',
  RUNWAY: 'รันเวย์',
  HANGAR: 'โรงเก็บเครื่องบิน',
  SHIP: 'เรือ',
  RADAR: 'เรดาร์',
  WEAPONS_DEPOT: 'คลังอาวุธ',
  FUEL_DEPOT: 'คลังเชื้อเพลิง',
  AIRCRAFT_SHELTER: 'โรงเก็บเครื่องบิน',
}

const TARGET_TYPE_FROM_TH = Object.fromEntries(
  Object.entries(TARGET_TYPE_TO_TH).map(([k, v]) => [v, k]),
)

const MATERIAL_TO_TH = {
  'REINFORCED CONCRETE': 'คอนกรีตเสริมเหล็ก',
  CONCRETE: 'คอนกรีต',
  STEEL: 'โครงเหล็ก',
  WOOD: 'ไม้',
  EARTH: 'ดิน',
  MIXED: 'อื่นๆ',
  UNKNOWN: 'อื่นๆ',
  OTHER: 'อื่นๆ',
}

const EFFECT_TO_TH = {
  DESTROY: 'สิ้นสภาพ (Destroy)',
  'LOSS OF CONTROL': 'สูญเสียการควบคุม',
  'STRUCTURAL FAILURE': 'พังทลาย',
  'PARTIAL DAMAGE': 'เสียหายบางส่วน',
}

const SOURCE_TO_TH = {
  joint: 'เป้าหมายร่วม',
  rtaf: 'เป้าหมาย ทอ.',
  suranaree: 'เป้าหมาย กกล.สุรนารี',
  deep: 'เป้าหมายทางลึก',
  manual: 'อื่นๆ',
  other: 'อื่นๆ',
}

function pickClosest(options, value) {
  if (!value) return ''
  const raw = String(value).trim()
  if (!raw) return ''
  if (options.includes(raw)) return raw
  const upper = raw.toUpperCase()
  const hit = options.find((opt) => opt.toUpperCase() === upper)
  if (hit) return hit
  const partial = options.find(
    (opt) => upper.includes(opt.toUpperCase()) || opt.toUpperCase().includes(upper),
  )
  return partial || ''
}

function priorityFromScore(score) {
  const n = Number(score)
  if (!Number.isFinite(n)) return ''
  if (n >= 4) return 'red'
  if (n === 3) return 'orange'
  return 'green'
}

/**
 * Convert GET /targets/{id} payload (+ optional map marker) into Sidebar form draft.
 */
export function targetApiToFormDraft(card, marker = null) {
  if (!card) return null

  const primary =
    (card.coordinates || []).find((c) => c.is_primary) ||
    (card.coordinates || [])[0] ||
    null

  const lat = marker?.lat ?? primary?.map_lat ?? null
  const lng = marker?.lng ?? primary?.map_lng ?? null

  const targetTypeTh =
    TARGET_TYPE_TO_TH[String(card.target_type || '').toUpperCase()] ||
    pickClosest(Object.values(TARGET_TYPE_TO_TH), card.target_subtype) ||
    pickClosest(Object.values(TARGET_TYPE_TO_TH), card.target_type) ||
    ''

  const structureTh =
    MATERIAL_TO_TH[String(card.material_class || '').toUpperCase()] ||
    pickClosest(Object.values(MATERIAL_TO_TH), card.material_class) ||
    ''

  const effectTh =
    EFFECT_TO_TH[String(card.desired_model_result || '').toUpperCase()] ||
    pickClosest(Object.values(EFFECT_TO_TH), card.desired_model_result) ||
    ''

  const sourceKey = String(card.data_source || 'manual').toLowerCase()
  const sourceTh = SOURCE_TO_TH[sourceKey] || 'อื่นๆ'

  const sizeBits = []
  if (card.width_m != null) sizeBits.push(`กว้าง ${card.width_m} ม.`)
  if (card.length_m != null) sizeBits.push(`ยาว ${card.length_m} ม.`)
  if (card.height_m != null) sizeBits.push(`สูง ${card.height_m} ม.`)
  if (card.heading_deg != null) sizeBits.push(`ทิศแกนยาว ${card.heading_deg}°`)
  if (card.floor_count) sizeBits.push(`ชั้น ${card.floor_count}`)

  const detailParts = [
    card.label ? `ชื่อ: ${card.label}` : '',
    card.target_description || '',
    card.target_subtype && card.target_subtype !== 'UNKNOWN'
      ? `ชนิดย่อย: ${card.target_subtype}`
      : '',
    sizeBits.length ? `ขนาด: ${sizeBits.join(' · ')}` : '',
    card.coordinate_error_m != null ? `ERR: ${card.coordinate_error_m} ม.` : '',
  ].filter(Boolean)

  return {
    id: card.id,
    label: card.label || '',
    selectedTargetSource: sourceTh,
    targetPriority: priorityFromScore(card.priority_score),
    targetType: targetTypeTh,
    structureType: structureTh,
    materialStrength: { ...(card.material_strength || {}) },
    latitude: lat != null ? Number(lat) : null,
    longitude: lng != null ? Number(lng) : null,
    targetDetails: detailParts.join('\n'),
    desiredEffect: effectTh,
    pk: card.target_pk ?? card.reference_pk ?? null,
    cep: card.cep ?? null,
    width_m: card.width_m ?? null,
    length_m: card.length_m ?? null,
    height_m: card.height_m ?? null,
    heading_deg: card.heading_deg ?? null,
    coordinate_error_m: card.coordinate_error_m ?? null,
    target_type_api: card.target_type || '',
    material_class_api: card.material_class || '',
  }
}

/**
 * Map JMEM product ranking → RightPanel recommendation rows.
 */
export function jmemProductsToRecommendations(products = []) {
  return (products || []).slice(0, 5).map((p, index) => ({
    id: p.product_id || index + 1,
    item: p.product_name || '—',
    size: `${Math.round(Number(p.weight_pounds) || 0)} ปอนด์`,
    qty: Number(p.n_required) || 0,
    pd: Number(p.pd_base) || 0,
    pk: Number(p.pk_n) || 0,
  }))
}

function fixedOrDash(value, digits) {
  const n = Number(value)
  return value != null && value !== '' && Number.isFinite(n) ? n.toFixed(digits) : '—'
}

function percentOrDash(value) {
  const n = Number(value)
  return value != null && value !== '' && Number.isFinite(n) ? `${Math.round(n * 1000) / 10}%` : '—'
}

export function buildJmemAnalysisText(draft, jmem) {
  const top = jmem?.products?.[0]
  const lines = [
    `ผลการวิเคราะห์เป้าหมาย: ${draft?.label || jmem?.label || '—'}`,
    '',
    `ประเภท: ${draft?.targetType || jmem?.target_element || '—'}`,
    `พิกัด: ${fixedOrDash(draft?.latitude, 6)}, ${fixedOrDash(draft?.longitude, 6)}`,
    `Pk เป้าหมาย: ${percentOrDash(draft?.pk ?? jmem?.mission?.pk_desired)}`,
    `CEP: ${draft?.cep ?? jmem?.mission?.cep_ft ?? '—'} ft`,
    '',
  ]
  if (top) {
    lines.push(
      `สินค้าแนะนำ (JMEM #1): ${top.product_name}`,
      `  - Pd: ${(Number(top.pd_base) * 100).toFixed(1)}%`,
      `  - N required: ${top.n_required}${top.quantity_overridden ? ` (ปรับจาก JMEM ${top.n_jmem})` : ''}`,
      `  - Pk(N): ${(Number(top.pk_n) * 100).toFixed(1)}%`,
      `  - น้ำหนัก: ${Math.round(top.weight_pounds)} lb`,
    )
  } else {
    lines.push('ยังไม่มีสินค้าใน scenario สำหรับจัดอันดับ JMEM')
  }
  if (jmem?.warnings?.length) {
    lines.push('', 'หมายเหตุ:')
    jmem.warnings.forEach((w) => lines.push(`  - ${w}`))
  }
  return lines.join('\n')
}

const MATERIAL_FROM_TH = Object.fromEntries(
  Object.entries(MATERIAL_TO_TH).map(([k, v]) => [v, k]),
)
const EFFECT_FROM_TH = Object.fromEntries(
  Object.entries(EFFECT_TO_TH).map(([k, v]) => [v, k]),
)
const SOURCE_FROM_TH = Object.fromEntries(
  Object.entries(SOURCE_TO_TH).map(([k, v]) => [v, k]),
)

function priorityToScore(priority) {
  if (priority === 'red') return 5
  if (priority === 'orange') return 3
  if (priority === 'green') return 2
  return undefined
}

function extractDescription(details, label) {
  const text = String(details || '').trim()
  if (!text) return ''
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean)
  const skipPrefixes = ['ชื่อ:', 'ชนิดย่อย:', 'ขนาด:', 'ERR:']
  const kept = lines.filter((line) => {
    if (label && line === `ชื่อ: ${label}`) return false
    return !skipPrefixes.some((p) => line.startsWith(p))
  })
  return kept.join('\n').trim() || text
}

/**
 * Convert Sidebar form values → PATCH /targets/{id} body.
 * Pass loadedCard to preserve coordinates when updating lat/lng.
 */
export function formDraftToTargetUpdate(form, loadedCard = null) {
  if (!form) return null

  const targetType =
    TARGET_TYPE_FROM_TH[form.targetType] ||
    form.target_type_api ||
    'BUILDING'
  const material =
    MATERIAL_FROM_TH[form.structureType] ||
    form.material_class_api ||
    'UNKNOWN'
  const effect =
    EFFECT_FROM_TH[form.desiredEffect] ||
    'STRUCTURAL FAILURE'
  const source =
    SOURCE_FROM_TH[form.selectedTargetSource] ||
    'manual'

  const body = {
    target_type: targetType,
    material_class: material,
    material_strength: cleanMaterialStrength(form.structureType, form.materialStrength),
    desired_model_result: effect,
    data_source: source,
  }

  if (form.label) body.label = form.label
  const priority = priorityToScore(form.targetPriority)
  if (priority != null) body.priority_score = priority
  if (form.pk != null && form.pk !== '') body.target_pk = Number(form.pk)
  if (form.cep != null && form.cep !== '') body.cep = Number(form.cep)
  if (form.width_m != null && form.width_m !== '') body.width_m = Number(form.width_m)
  if (form.length_m != null && form.length_m !== '') body.length_m = Number(form.length_m)
  if (form.height_m != null && form.height_m !== '') body.height_m = Number(form.height_m)
  if (form.heading_deg != null && form.heading_deg !== '') {
    body.heading_deg = ((Number(form.heading_deg) % 360) + 360) % 360
  }
  if (form.coordinate_error_m != null && form.coordinate_error_m !== '') {
    body.coordinate_error_m = Number(form.coordinate_error_m)
  }

  const desc = extractDescription(form.targetDetails, form.label)
  if (desc !== undefined) body.target_description = desc

  const lat = form.latitude != null && form.latitude !== '' ? Number(form.latitude) : null
  const lng = form.longitude != null && form.longitude !== '' ? Number(form.longitude) : null
  if (loadedCard?.coordinates?.length && Number.isFinite(lat) && Number.isFinite(lng)) {
    body.coordinates = loadedCard.coordinates.map((c) => ({
      id: c.id,
      label: c.label || '',
      map_lat: c.is_primary ? lat : c.map_lat,
      map_lng: c.is_primary ? lng : c.map_lng,
      is_primary: !!c.is_primary,
      selected_product_id: c.selected_product_id ?? null,
    }))
    // If no primary flagged, update first point
    if (!body.coordinates.some((c) => c.is_primary) && body.coordinates[0]) {
      body.coordinates[0].map_lat = lat
      body.coordinates[0].map_lng = lng
      body.coordinates[0].is_primary = true
    }
  } else if (Number.isFinite(lat) && Number.isFinite(lng) && !loadedCard?.coordinates?.length) {
    body.coordinates = [
      {
        label: form.label || 'Primary',
        map_lat: lat,
        map_lng: lng,
        is_primary: true,
      },
    ]
  }

  return body
}

export { TARGET_TYPE_FROM_TH, TARGET_TYPE_TO_TH, MATERIAL_FROM_TH, MATERIAL_TO_TH, SOURCE_FROM_TH, SOURCE_TO_TH }
