/** Parse spreadsheet / table rows into POST /targets payloads (RTAF target list format). */

import * as XLSX from 'xlsx'
import {
  MATERIAL_FROM_TH,
  MATERIAL_TO_TH,
  SOURCE_FROM_TH,
  SOURCE_TO_TH,
  TARGET_TYPE_FROM_TH,
  TARGET_TYPE_TO_TH,
} from './targetFormMapper'
import { parseCoordinateText } from './coordinateParser'

const COLUMN_ALIASES = {
  tgt: ['tgt', 'รหัส', 'หมายเลขเป้าหมาย', 'หมายเลข'],
  name: ['ชื่อเป้าหมาย', 'ชื่อ', 'name', 'targetname', 'target name', 'ชื่อเป้า'],
  pri: ['pri', 'priority', 'ลำดับความสำคัญ', 'ความสำคัญpri'],
  coordinates: [
    'dmpiพิกัดlat/long',
    'dmpiพิกัดlatlong',
    'dmpiพิกัด',
    'dmpi',
    'lat/long',
    'latlong',
    'coordinates',
    'พิกัด',
    'coord',
    'lat long',
  ],
  elevation: ['ความสูง', 'elevation', 'msl', 'ความสูงmsl', 'ความสูงmslft', 'ความสูงmslft'],
  characteristics: ['ลักษณะของเป้าหมาย', 'ลักษณะ', 'characteristics', 'ลักษณะเป้าหมาย'],
  significance: ['ความสำคัญเป้าหมาย', 'ความสำคัญ', 'significance'],
  desiredEffect: ['ผลกระทบที่ต้องการ', 'ผลกระทบ', 'effect', 'desired effect', 'desiredeffect'],
  aaWeapons: ['อาวุธต่อสู้อากาศยาน', 'อาวุธต่อสู้', 'อาวุธ', 'aa', 'aaweapons', 'ปตอ'],
  targetType: ['ประเภทเป้าหมาย', 'targettype', 'target type'],
  targetSubtype: ['ประเภทย่อย', 'ชนิดย่อย', 'subtype'],
  material: ['โครงสร้าง', 'วัสดุโครงสร้าง', 'วัสดุ', 'material', 'structure'],
  floors: ['จำนวนชั้น', 'floors', 'floor count'],
  width: ['ความกว้าง', 'width'],
  length: ['ความยาว', 'length'],
  height: ['ความสูงเป้าหมาย', 'ความสูงอาคาร', 'height'],
  heading: ['ทิศแกนยาว', 'heading'],
  pk: ['pk', 'pkที่ต้องการ', 'desired pk'],
  cep: ['cep'],
  coordinateError: ['err', 'ความคลาดเคลื่อนพิกัด', 'coordinate error'],
  source: ['แหล่งที่มา', 'data source', 'source'],
}

const DEFAULT_COLUMN_ORDER = [
  'tgt',
  'name',
  'pri',
  'coordinates',
  'elevation',
  'characteristics',
  'significance',
  'desiredEffect',
  'aaWeapons',
  'targetType',
  'targetSubtype',
  'material',
  'floors',
  'width',
  'length',
  'height',
  'heading',
  'pk',
  'cep',
  'coordinateError',
  'source',
]

const EFFECT_KEYWORDS = [
  { match: /ทำลาย|destroy|สิ้นสภาพ/i, value: 'DESTROY' },
  { match: /สูญเสียการควบคุม|loss of control/i, value: 'LOSS OF CONTROL' },
  { match: /พังทลาย|structural failure/i, value: 'STRUCTURAL FAILURE' },
  { match: /เสียหายบางส่วน|partial damage/i, value: 'PARTIAL DAMAGE' },
]

function normalizeHeader(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[().:'"′°]/g, '')
    .replace(/ft/g, '')
}

function detectDelimiter(line) {
  if (line.includes('\t')) return '\t'
  if (line.includes('|')) return '|'
  if (line.includes(';')) return ';'
  return ','
}

function splitRow(line, delimiter) {
  if (delimiter === ',') {
    const cells = []
    let current = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i += 1) {
      const ch = line[i]
      if (ch === '"') {
        inQuotes = !inQuotes
        continue
      }
      if (ch === delimiter && !inQuotes) {
        cells.push(current.trim())
        current = ''
        continue
      }
      current += ch
    }
    cells.push(current.trim())
    return cells
  }
  return line.split(delimiter).map((cell) => cell.trim())
}

function headerMatchesField(headerNorm, alias) {
  const aliasNorm = normalizeHeader(alias)
  if (!headerNorm || !aliasNorm) return false
  if (headerNorm === aliasNorm) return true
  if (aliasNorm.length < 3) return false
  return headerNorm.includes(aliasNorm) || aliasNorm.includes(headerNorm)
}

function mapHeaders(headers) {
  const mapping = {}
  headers.forEach((header, index) => {
    const norm = normalizeHeader(header)
    if (!norm) return
    let bestField = null
    let bestScore = 0
    for (const [field, aliases] of Object.entries(COLUMN_ALIASES)) {
      if (mapping[field] != null) continue
      for (const alias of aliases) {
        if (!headerMatchesField(norm, alias)) continue
        const score = normalizeHeader(alias).length
        if (score > bestScore) {
          bestScore = score
          bestField = field
        }
      }
    }
    if (bestField) mapping[bestField] = index
  })
  return mapping
}

function hasHeaderRow(cells) {
  const joined = cells.map(normalizeHeader).join(' ')
  return (
    joined.includes('tgt') ||
    joined.includes('ชื่อเป้าหมาย') ||
    joined.includes('dmpi') ||
    joined.includes('พิกัด') ||
    joined.includes('ลักษณะ')
  )
}

/**
 * Parse DMS like `14° 19.042953'N 105° 10.623967'E` or decimal degrees.
 */
export function parseCoordinatePair(text) {
  const raw = String(text || '').trim()
  if (!raw) return null

  const dmsLat = raw.match(/(\d{1,3})\s*[°º]?\s*(\d{1,2}(?:\.\d+)?)\s*[''′]?\s*([NSns])/i)
  const dmsLng = raw.match(/(\d{1,3})\s*[°º]?\s*(\d{1,2}(?:\.\d+)?)\s*[''′]?\s*([EWew])/i)
  if (dmsLat && dmsLng) {
    const latSign = /^s/i.test(dmsLat[3]) ? -1 : 1
    const lngSign = /^w/i.test(dmsLng[3]) ? -1 : 1
    const lat = latSign * (Number(dmsLat[1]) + Number(dmsLat[2]) / 60)
    const lng = lngSign * (Number(dmsLng[1]) + Number(dmsLng[2]) / 60)
    if (Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
      return { lat, lng }
    }
  }

  const decimal = raw.match(/(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)/)
  if (decimal) {
    const lat = Number(decimal[1])
    const lng = Number(decimal[2])
    if (Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
      return { lat, lng }
    }
  }

  const other = parseCoordinateText(raw)
  return other ? { lat: other.lat, lng: other.lng } : null
}

function parsePriority(value) {
  const raw = String(value || '').trim()
  if (!raw || raw === '-') return 3
  const n = Number(raw)
  if (Number.isFinite(n) && n >= 1 && n <= 5) return Math.round(n)
  if (/สูง|high|h/i.test(raw)) return 5
  if (/กลาง|medium|med|m/i.test(raw)) return 3
  if (/ต่ำ|low|l/i.test(raw)) return 2
  return 3
}

function parseDesiredEffect(value) {
  const raw = String(value || '').trim()
  if (!raw) return 'STRUCTURAL FAILURE'
  for (const rule of EFFECT_KEYWORDS) {
    if (rule.match.test(raw)) return rule.value
  }
  return 'STRUCTURAL FAILURE'
}

function parseNumber(value) {
  const raw = String(value ?? '').replace(/,/g, '').trim()
  if (!raw || raw === '-') return null
  const n = Number(raw.match(/-?\d+(?:\.\d+)?/)?.[0])
  return Number.isFinite(n) ? n : null
}

/** Accept the Thai form label or the API key (e.g. `บังเกอร์` / `BUNKER`). */
function parseEnum(value, fromTh, toTh) {
  const raw = String(value || '').trim()
  if (!raw || raw === '-') return { value: null, invalid: false }
  if (fromTh[raw]) return { value: fromTh[raw], invalid: false }
  const keys = Object.keys(toTh)
  const upper = raw.toUpperCase()
  const key =
    keys.find((k) => k.toUpperCase() === upper) ||
    keys.find((k) => k.toUpperCase() === upper.replace(/[\s-]+/g, '_')) ||
    keys.find((k) => k.toUpperCase() === upper.replace(/_/g, ' '))
  if (key) return { value: key, invalid: false }
  const thai = Object.keys(fromTh).find((label) => raw.includes(label))
  if (thai) return { value: fromTh[thai], invalid: false }
  return { value: null, invalid: true }
}

function parsePk(value) {
  const n = parseNumber(value)
  if (n == null || n <= 0) return null
  const pk = n > 1 ? n / 100 : n
  return pk <= 1 ? pk : null
}

function parseHeading(value) {
  const n = parseNumber(value)
  if (n == null) return null
  return ((n % 360) + 360) % 360
}

function buildDescription(row) {
  const parts = []
  if (row.name) parts.push(`ชื่อ: ${row.name}`)
  if (row.characteristics) parts.push(`ลักษณะ: ${row.characteristics}`)
  if (row.significance) parts.push(`ความสำคัญ: ${row.significance}`)
  if (row.elevation) parts.push(`ความสูง (MSL): ${row.elevation} ft`)
  if (row.aaWeapons) parts.push(`อาวุธต่อสู้อากาศยาน: ${row.aaWeapons}`)
  return parts.join('\n')
}

function pickCell(cells, index) {
  if (index == null || index < 0) return ''
  return String(cells[index] ?? '').trim()
}

function rowFromCells(cells, columnMap, rowNumber) {
  const row = {
    rowNumber,
    tgt: pickCell(cells, columnMap.tgt),
    name: pickCell(cells, columnMap.name),
    pri: pickCell(cells, columnMap.pri),
    coordinatesRaw: pickCell(cells, columnMap.coordinates),
    elevation: pickCell(cells, columnMap.elevation),
    characteristics: pickCell(cells, columnMap.characteristics),
    significance: pickCell(cells, columnMap.significance),
    desiredEffect: pickCell(cells, columnMap.desiredEffect),
    aaWeapons: pickCell(cells, columnMap.aaWeapons),
    targetTypeRaw: pickCell(cells, columnMap.targetType),
    targetSubtype: pickCell(cells, columnMap.targetSubtype),
    materialRaw: pickCell(cells, columnMap.material),
    floors: pickCell(cells, columnMap.floors),
    sourceRaw: pickCell(cells, columnMap.source),
  }

  const errors = []
  const coords = parseCoordinatePair(row.coordinatesRaw)
  if (!coords) errors.push('พิกัด DMPI ไม่ถูกต้อง')

  const label = row.tgt || row.name
  if (!label) errors.push('ต้องมี TGT หรือชื่อเป้าหมาย')

  const targetType = parseEnum(row.targetTypeRaw, TARGET_TYPE_FROM_TH, TARGET_TYPE_TO_TH)
  if (targetType.invalid) errors.push(`ไม่รู้จักประเภทเป้าหมาย "${row.targetTypeRaw}"`)
  const material = parseEnum(row.materialRaw, MATERIAL_FROM_TH, MATERIAL_TO_TH)
  if (material.invalid) errors.push(`ไม่รู้จักโครงสร้าง "${row.materialRaw}"`)
  const source = parseEnum(row.sourceRaw, SOURCE_FROM_TH, SOURCE_TO_TH)

  const profile = {
    targetType: targetType.value,
    material: material.value,
    dataSource: source.value,
    widthM: parseNumber(pickCell(cells, columnMap.width)),
    lengthM: parseNumber(pickCell(cells, columnMap.length)),
    heightM: parseNumber(pickCell(cells, columnMap.height)),
    headingDeg: parseHeading(pickCell(cells, columnMap.heading)),
    pk: parsePk(pickCell(cells, columnMap.pk)),
    cepFt: parseNumber(pickCell(cells, columnMap.cep)),
    coordinateErrorM: parseNumber(pickCell(cells, columnMap.coordinateError)),
  }

  return {
    ...row,
    ...profile,
    coords,
    label: row.tgt || row.name,
    displayName: row.name || row.tgt,
    errors,
    valid: errors.length === 0,
  }
}

/**
 * Parse pasted table / CSV / TSV text into normalized rows.
 */
export function parseTargetImportText(text) {
  const lines = String(text || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)

  if (!lines.length) {
    return { rows: [], columnMap: {}, hasHeaders: false, delimiter: '\t' }
  }

  const delimiter = detectDelimiter(lines[0])
  const firstCells = splitRow(lines[0], delimiter)
  const hasHeaders = hasHeaderRow(firstCells)
  const headers = hasHeaders ? firstCells : []
  const columnMap = hasHeaders
    ? mapHeaders(headers)
    : Object.fromEntries(DEFAULT_COLUMN_ORDER.map((field, index) => [field, index]))

  const dataLines = hasHeaders ? lines.slice(1) : lines
  const rows = dataLines.map((line, index) => {
    const cells = splitRow(line, delimiter)
    return rowFromCells(cells, columnMap, index + 1)
  })

  return { rows, columnMap, hasHeaders, delimiter }
}

export function importRowToCreateBody(row, scenarioId) {
  if (!row?.valid || !scenarioId) return null

  const description = buildDescription(row)
  const effect = parseDesiredEffect(row.desiredEffect)

  const body = {
    scenario_id: scenarioId,
    label: String(row.label).slice(0, 255),
    priority_score: parsePriority(row.pri),
    target_description: description,
    desired_model_result: effect,
    data_source: row.dataSource || 'import',
    coordinates: [
      {
        label: 'DMPI',
        map_lat: row.coords.lat,
        map_lng: row.coords.lng,
        is_primary: true,
      },
    ],
  }
  if (row.targetType) body.target_type = row.targetType
  if (row.targetSubtype) body.target_subtype = row.targetSubtype.slice(0, 128)
  if (row.material) body.material_class = row.material
  if (row.floors && row.floors !== '-') body.floor_count = row.floors.slice(0, 32)
  if (row.widthM != null) body.width_m = row.widthM
  if (row.lengthM != null) body.length_m = row.lengthM
  if (row.heightM != null) body.height_m = row.heightM
  if (row.headingDeg != null) body.heading_deg = row.headingDeg
  if (row.pk != null) body.target_pk = row.pk
  if (row.cepFt != null) body.cep = row.cepFt
  if (row.coordinateErrorM != null) body.coordinate_error_m = row.coordinateErrorM
  return body
}

export async function importTargetsFromRows(rows, scenarioId, createFn) {
  const validRows = (rows || []).filter((row) => row.valid)
  const results = []

  for (const row of validRows) {
    const body = importRowToCreateBody(row, scenarioId)
    if (!body) {
      results.push({ row, ok: false, error: 'ข้อมูลไม่ครบ' })
      continue
    }
    try {
      const created = await createFn('/targets', body)
      results.push({ row, ok: true, target: created })
    } catch (err) {
      results.push({ row, ok: false, error: err?.message || 'สร้างเป้าหมายไม่สำเร็จ' })
    }
  }

  const successCount = results.filter((r) => r.ok).length
  const failCount = results.length - successCount
  return { results, successCount, failCount }
}

export function workbookToImportText(arrayBuffer) {
  const workbook = XLSX.read(arrayBuffer, { type: 'array' })
  const sheetName = workbook.SheetNames[0]
  if (!sheetName) return ''
  const sheet = workbook.Sheets[sheetName]
  return XLSX.utils.sheet_to_csv(sheet, { FS: '\t', RS: '\n' })
}

export const TARGET_IMPORT_SAMPLE = [
  'TGT\tชื่อเป้าหมาย\tPri\tDMPI : พิกัด (Lat/Long)\tความสูง (MSL)(ft.)\tลักษณะของเป้าหมาย\tความสำคัญเป้าหมาย\tผลกระทบที่ต้องการ\tอาวุธต่อสู้อากาศยาน\tประเภทเป้าหมาย\tประเภทย่อย\tโครงสร้าง\tจำนวนชั้น\tความกว้าง (ม.)\tความยาว (ม.)\tความสูงเป้าหมาย (ม.)\tทิศแกนยาว (°)\tPk ที่ต้องการ\tCEP (ft)\tERR (ม.)\tแหล่งที่มา',
  "S1\tกลุ่มที่พัก ทกพ. คูติดต่อ จุดที่ 2 เส้นทางไปเนิน 745\tสูง\t14° 19.042953'N 105° 10.623967'E\t2,027\tที่พัก 6 หลัง, บก., ที่มั่นดัดแปลงแข็งแรง แนวคูติดต่อ\tฐานปฏิบัติการใกล้แนววางกำลัง ฝ่ายเรา ทางไปเนิน 745\tทำลาย ทำให้หมดขีดความสามารถ\tปตอ. 12.7\tอาคาร\tที่พักและ บก. ส่วนหน้า\tไม้\t1\t24\t60\t4\t35\t0.85\t30\t10\tเป้าหมาย กกล.สุรนารี",
].join('\n')
