import { materialStrengthSummary } from '../config/materialStrength.js'
import { formatAllCoordinates, formatDms } from './coordinateParser.js'
import { allocationTotals, weaponAllocationsFromJmem, weaponSummaryText } from './reportData.js'

const priorityLabels = {
  red: 'สำคัญสูง',
  orange: 'สำคัญ',
  green: 'ทั่วไป',
  key: 'สำคัญสูง',
  medium: 'สำคัญ',
  general: 'ทั่วไป',
}

const priorityAliases = {
  สำคัญสูง: 'red',
  สำคัญ: 'orange',
  ปานกลาง: 'orange',
  ทั่วไป: 'green',
}

function hasValue(value) {
  return value !== undefined && value !== null && String(value).trim() !== ''
}

function displayValue(value, fallback = '-') {
  return hasValue(value) ? String(value).trim() : fallback
}

function formatCoordinates(lat, lng) {
  const la = Number(lat)
  const ln = Number(lng)
  if (!Number.isFinite(la) || !Number.isFinite(ln)) return '-'
  return `${la.toFixed(5)}, ${ln.toFixed(5)}`
}

function formatScore(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '-'
  return number.toFixed(2)
}

function parseElevationFromDetails(details) {
  const text = String(details || '')
  const match = text.match(/ความสูง\s*\(MSL\)\s*:\s*([^\n]+)/i)
  return match ? match[1].trim() : ''
}

function parseNameFromDetails(details, fallback = '') {
  const text = String(details || '')
  const match = text.match(/ชื่อ:\s*([^\n]+)/)
  return match ? match[1].trim() : fallback
}

function cleanRecommendation(value) {
  return String(value ?? '').replace(/\s*บาท\s*$/i, '').trim()
}

function topRecommendation(recommendations = []) {
  if (!Array.isArray(recommendations) || !recommendations.length) return null
  return recommendations[0]
}

function buildWeaponText(top) {
  if (!top) return '-'
  const parts = [cleanRecommendation(top.size), cleanRecommendation(top.item)].filter(hasValue)
  return parts[0] || '-'
}

function buildWeaponDetail(top) {
  if (!top) return '-'
  const qty = hasValue(top.qty) ? top.qty : '-'
  const pd = hasValue(top.pd) ? formatScore(top.pd) : '-'
  return `จำนวน ${qty} / Pd ${pd}`
}

function resolvePriorityLabel(priority, formData = {}) {
  if (hasValue(priority)) {
    return priorityLabels[priority] || String(priority).trim()
  }
  if (hasValue(formData.targetPriority)) {
    return priorityLabels[formData.targetPriority] || formData.targetPriority
  }
  return '-'
}

function formatPercent(value) {
  const number = Number(value)
  if (!hasValue(value) || !Number.isFinite(number)) return '-'
  return `${Math.round(number * 1000) / 10}%`
}

function formatMeters(value) {
  return hasValue(value) && Number.isFinite(Number(value)) ? `${Number(value)} ม.` : '-'
}

function buildTargetInfoRows(formData, card, priorityLabel, allocations) {
  const coords = formatAllCoordinates(formData.latitude, formData.longitude)
  const subtype = card?.target_subtype && card.target_subtype !== 'UNKNOWN' ? card.target_subtype : ''
  const size = ['width_m', 'length_m', 'height_m'].map((key) => (hasValue(formData[key]) ? formData[key] : '-'))
  const aimPoints = Math.max(allocations.length, card?.coordinates?.length || 0)
  return [
    ['ประเภทเป้าหมาย', displayValue(formData.targetType)],
    ['ชนิดย่อย', displayValue(subtype)],
    ['แหล่งที่มา', displayValue(formData.selectedTargetSource)],
    ['ความสำคัญ', priorityLabel],
    ['ชนิดโครงสร้าง', displayValue(formData.structureType)],
    ['ค่าความแข็งแรงวัสดุ', displayValue(materialStrengthSummary(formData.structureType, formData.materialStrength))],
    ['ขนาด ก × ย × ส', size.every((v) => v === '-') ? '-' : `${size.join(' × ')} ม.`],
    ['ทิศแกนยาว', hasValue(formData.heading_deg) ? `${formData.heading_deg}°` : '-'],
    ['จำนวนชั้น', displayValue(card?.floor_count && card.floor_count !== '-' ? card.floor_count : '')],
    ['ERR พิกัด', formatMeters(formData.coordinate_error_m)],
    ['พิกัด WGS84', coords ? coords.DD : '-'],
    ['พิกัด DMS', coords ? formatDms(Number(formData.latitude), Number(formData.longitude)) : '-'],
    ['MGRS', coords ? coords.MGRS : '-'],
    ['UTM', coords ? coords.UTM : '-'],
    ['ผลลัพธ์ที่ต้องการ', displayValue(formData.desiredEffect)],
    ['Pk ที่ต้องการ', formatPercent(formData.pk)],
    ['CEP', hasValue(formData.cep) ? `${formData.cep} ft` : '-'],
    ['จำนวนจุดเล็ง', aimPoints ? String(aimPoints) : '-'],
  ]
}

function rankedProductsFromJmem(jmem) {
  return (jmem?.products || []).slice(0, 5).map((p) => ({
    rank: p.rank,
    productName: p.product_name || '—',
    weightLb: Number(p.weight_pounds) || 0,
    pd: Number(p.pd_base) || 0,
    pkSingle: Number(p.pk_single) || 0,
    quantity: Number(p.n_required) || 0,
    pkN: Number(p.pk_n) || 0,
    unitCost: Number(p.unit_cost) || 0,
    selected: Boolean(p.selected),
  }))
}

/**
 * Build normalized export payload used by PDF/Word renderers.
 * `jmem` (GET /jmem/targets/{id}) adds selected weapons per aim point, mission inputs and ranking;
 * `card` (GET /targets/{id}) adds fields the form draft does not carry (subtype, floors, aim points).
 */
export function buildTargetExportPayload({
  formData = {},
  recommendations = [],
  analysisText = '',
  priority = '',
  mapImagePreview = '',
  jmem = null,
  card = null,
  scenarioName = '',
} = {}) {
  const top = topRecommendation(recommendations)
  const allocations = weaponAllocationsFromJmem(jmem)
  const weaponText = allocations.length ? weaponSummaryText(allocations) : buildWeaponText(top)
  const weaponDetail = allocations.length
    ? allocations
      .map((a) => `${allocations.length > 1 ? `${a.aimPoint}: ` : ''}${a.productName} จำนวน ${a.quantity} ลูก / Pk(N) ${formatPercent(a.pkN)}`)
      .join('\n')
    : buildWeaponDetail(top)
  const priorityLabel = resolvePriorityLabel(priority, formData)
  const label = displayValue(formData.label, '')
  const details = displayValue(formData.targetDetails, '')
  const parsedName = parseNameFromDetails(details, label)
  const tgtCode = label || (formData.id ? `TGT-${String(formData.id).slice(0, 8)}` : '-')
  const elevation =
    parseElevationFromDetails(details) ||
    (hasValue(formData.height_m) ? `${formData.height_m}` : '')

  const payload = {
    generatedDate: new Date().toLocaleString('th-TH'),
    images: {
      target: hasValue(formData.imagePreview) ? formData.imagePreview : '',
      map: hasValue(mapImagePreview) ? mapImagePreview : '',
    },
    mainRow: {
      tgt: tgtCode,
      name: parsedName || label || '-',
      pri: priorityLabel,
      coordinates: formatCoordinates(formData.latitude, formData.longitude),
      elevation: displayValue(elevation),
      details: (card && displayValue(card.target_description, '')) || details || '-',
      desiredEffect: displayValue(formData.desiredEffect),
      weapon: weaponText,
    },
    scenarioName: displayValue(scenarioName, ''),
    targetRows: buildTargetInfoRows(formData, card, priorityLabel, allocations),
    allocations,
    allocationTotals: allocationTotals(allocations),
    mission: jmem?.mission || null,
    effectZones: Array.isArray(jmem?.effect_zones) ? jmem.effect_zones : [],
    rankedProducts: rankedProductsFromJmem(jmem),
    warnings: Array.isArray(jmem?.warnings) ? jmem.warnings : [],
    extraRows: [
      ['ประเภทเป้าหมาย', displayValue(formData.targetType)],
      ['พื้นที่/แหล่งข้อมูล', displayValue(formData.selectedTargetSource)],
      ['ค่าความแข็งแรงวัสดุ', displayValue(materialStrengthSummary(formData.structureType, formData.materialStrength))],
      ['ชื่อไฟล์รูปภาพ', displayValue(formData.imageName)],
      ['AI Confidence', hasValue(formData.aiConfidence) ? `${formData.aiConfidence}%` : '-'],
      ['Pk Value', hasValue(formData.pk) ? formatScore(formData.pk) : '-'],
      ['CEP Value', hasValue(formData.cep) ? displayValue(formData.cep) : '-'],
      ['รายละเอียดอาวุธที่ใช้', weaponDetail],
      ['ผลการวิเคราะห์ AI', displayValue(analysisText, '-')],
    ],
    analysisText: displayValue(analysisText, ''),
    recommendations: Array.isArray(recommendations) ? recommendations.slice(0, 5) : [],
    priority: priorityLabel,
    targetInfo: {
      id: tgtCode,
      name: parsedName || label || '-',
      type: displayValue(formData.targetType),
      structure: displayValue(formData.structureType),
      strength: displayValue(materialStrengthSummary(formData.structureType, formData.materialStrength)),
      area: displayValue(formData.selectedTargetSource),
      details,
      imageName: displayValue(formData.imageName, '-'),
      imagePreview: formData.imagePreview || '',
      latitude: formData.latitude,
      longitude: formData.longitude,
    },
    metrics: {
      confidence: formData.aiConfidence,
      pk: hasValue(formData.pk) ? formatScore(formData.pk) : '',
      cep: formData.cep,
      recommendation: weaponText,
      weaponDetail,
    },
  }

  return payload
}

export function buildReportRecordFromPayload(payload, recorderName = '') {
  const main = payload?.mainRow || {}
  const importanceKey =
    Object.entries(priorityLabels).find(([, label]) => label === main.pri)?.[0] || 'general'

  return {
    id: Date.now(),
    recorderName,
    savedAt: new Date().toISOString(),
    target: main.name || main.tgt || 'เป้าหมาย',
    source: payload?.targetInfo?.area || '-',
    type: payload?.targetInfo?.type || '-',
    importance: ['red', 'orange', 'green'].includes(importanceKey)
      ? importanceKey
      : priorityAliases[main.pri] || 'general',
    status: 'สมบูรณ์',
    date: new Date().toLocaleString('th-TH'),
    dateValue: new Date().toISOString().slice(0, 10),
    exportSnapshot: payload,
  }
}

export function loadSavedReports(storageKey = 'weaponeering_records') {
  try {
    const raw = JSON.parse(window.localStorage.getItem(storageKey) || '[]')
    if (!Array.isArray(raw)) return []
    return raw.map((item, index) => {
      const snapshot = item.exportSnapshot || null
      const main = snapshot?.mainRow || {}
      const savedAt = item.savedAt || new Date().toISOString()
      return {
        id: item.id || index + 1,
        date: item.date || new Date(savedAt).toLocaleString('th-TH'),
        dateValue: item.dateValue || savedAt.slice(0, 10),
        target: item.target || main.name || main.tgt || item.recorderName || 'เป้าหมาย',
        source: item.source || snapshot?.targetInfo?.area || '-',
        type: item.type || snapshot?.targetInfo?.type || '-',
        importance: normalizeImportance(item.importance || 'general'),
        status: item.status || 'สมบูรณ์',
        details: snapshot?.targetInfo?.details || '',
        imageName: snapshot?.targetInfo?.imageName || '',
        imagePreview: snapshot?.images?.target || snapshot?.targetInfo?.imagePreview || '',
        latitude: snapshot?.targetInfo?.latitude,
        longitude: snapshot?.targetInfo?.longitude,
        exportSnapshot: snapshot,
        recorderName: item.recorderName || '',
        savedAt,
        fromApi: false,
      }
    })
  } catch {
    return []
  }
}

function normalizeImportance(value) {
  const key = String(value || '').toLowerCase()
  if (key === 'red' || key === 'key' || key === 'สำคัญสูง') return 'key'
  if (key === 'orange' || key === 'medium' || key === 'สำคัญ' || key === 'ปานกลาง') return 'medium'
  return 'general'
}

function importanceFromPriorityScore(score) {
  const n = Number(score)
  if (!Number.isFinite(n)) return 'general'
  if (n >= 4) return 'key'
  if (n === 3) return 'medium'
  return 'general'
}

/**
 * Build a Reports-table row + export snapshot from API target (+ optional JMEM).
 */
export function targetCardToReportRow(card, jmem = null, formDraft = null, options = {}) {
  if (!card) return null

  const draft = formDraft || {
    id: card.id,
    label: card.label || '',
    selectedTargetSource: card.data_source || 'อื่นๆ',
    targetType: card.target_type || '-',
    targetDetails: card.target_description || '',
    desiredEffect: card.desired_model_result || '',
    pk: card.target_pk ?? card.reference_pk ?? null,
    cep: card.cep ?? null,
    height_m: card.height_m ?? null,
    latitude: card.coordinates?.[0]?.map_lat ?? null,
    longitude: card.coordinates?.[0]?.map_lng ?? null,
  }

  const recommendations = Array.isArray(jmem?.products)
    ? jmem.products.slice(0, 5).map((p, index) => ({
        id: p.product_id || index + 1,
        item: p.product_name || '—',
        size: `${Math.round(Number(p.weight_pounds) || 0)} ปอนด์`,
        qty: Number(p.n_required) || 0,
        pd: Number(p.pd_base) || 0,
        pk: Number(p.pk_n) || 0,
      }))
    : []

  const analysisText = options.analysisText || (() => {
    const top = recommendations[0]
    if (!top) return jmem ? 'ยังไม่มีสินค้าใน scenario สำหรับจัดอันดับ JMEM' : ''
    return [
      `สินค้าแนะนำ (JMEM #1): ${top.item}`,
      `  - Pd: ${(Number(top.pd) * 100).toFixed(1)}%`,
      `  - N required: ${top.qty}`,
      `  - Pk(N): ${(Number(top.pk) * 100).toFixed(1)}%`,
      `  - น้ำหนัก: ${top.size}`,
    ].join('\n')
  })()

  const exportSnapshot = buildTargetExportPayload({
    formData: draft,
    recommendations,
    analysisText,
    priority: draft.targetPriority || importanceFromPriorityScore(card.priority_score),
    jmem,
    card,
    scenarioName: options.scenarioName || '',
  })

  const updatedAt = card.updated_at || card.created_at || new Date().toISOString()
  const importance = normalizeImportance(
    draft.targetPriority || importanceFromPriorityScore(card.priority_score),
  )

  return {
    id: card.id,
    shortId: String(card.id || '').replace(/-/g, '').slice(0, 8).toUpperCase() || '—',
    date: new Date(updatedAt).toLocaleString('th-TH'),
    dateValue: String(updatedAt).slice(0, 10),
    target: draft.label || card.label || 'เป้าหมาย',
    source: draft.selectedTargetSource || exportSnapshot.targetInfo?.area || '-',
    type: draft.targetType || exportSnapshot.targetInfo?.type || '-',
    importance,
    status: 'สมบูรณ์',
    details: draft.targetDetails || '',
    imageName: draft.imageName || '',
    imagePreview: draft.imagePreview || '',
    latitude: draft.latitude,
    longitude: draft.longitude,
    confidence: draft.aiConfidence ?? '',
    recommendation: exportSnapshot.mainRow?.weapon || '-',
    pk: draft.pk != null ? formatScore(draft.pk) : exportSnapshot.metrics?.pk || '-',
    cep: draft.cep != null ? String(draft.cep) : '-',
    effect: draft.desiredEffect || '-',
    analysis: analysisText,
    exportSnapshot,
    fromApi: true,
    savedAt: updatedAt,
  }
}
