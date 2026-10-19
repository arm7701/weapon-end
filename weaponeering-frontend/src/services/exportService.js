import { buildTargetExportPayload } from '../utils/reportExportMapper'
import { PRIORITY_LABELS } from '../utils/reportData'

export { buildTargetExportPayload }

const reportFontFamily = "'TH Sarabun New', 'Sarabun', 'Leelawadee UI', Tahoma, sans-serif"
const wordFont = 'TH Sarabun New'
const wordBlue = '174EA6'
const wordText = '111827'
const wordMuted = '5F6B7A'
const wordBorder = 'B8C2D0'
const wordLabelFill = 'E8EEF8'
const wordTotalFill = 'F1F4F9'

const PDF_WIDTH_PX = 1120
const PDF_MARGIN_MM = 10
const PDF_FOOTER_MM = 6
const DOCX_CONTENT_DXA = 15360

const MAIN_HEADERS = [
  'TGT',
  'ชื่อเป้าหมาย',
  'PRI',
  'พิกัด',
  'ความสูง (MSL)\n(ft)',
  'รายละเอียดเป้าหมาย',
  'ผลลัพธ์ที่ต้องการ',
  'อาวุธที่ใช้',
]
const MAIN_WIDTHS = [1400, 1900, 1300, 2200, 1800, 2600, 2300, 2200]

const escapeHtml = value => String(value ?? '')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;')

const hasImagePreview = value => typeof value === 'string' && value.startsWith('data:image/')

const imageTypeFromDataUrl = dataUrl => {
  const match = String(dataUrl || '').match(/^data:image\/(png|jpe?g|gif|bmp);/i)
  if (!match) return 'png'
  return match[1].toLowerCase() === 'jpeg' ? 'jpg' : match[1].toLowerCase()
}

const dataUrlToUint8Array = dataUrl => {
  const [, base64 = ''] = String(dataUrl).split(',')
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes
}

const isNum = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
const fmtInt = value => (isNum(value) ? Math.round(Number(value)).toLocaleString('en-US') : '-')
const fmtMoney = value => (isNum(value) ? Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 }) : '-')
const fmtPct = value => (isNum(value) ? `${(Number(value) * 100).toFixed(1)}%` : '-')

function normalizeExportData(data) {
  if (data?.mainRow && data?.extraRows) return data
  return buildTargetExportPayload({
    formData: data?.targetInfo || data?.formData || {},
    recommendations: data?.recommendations || [],
    analysisText: data?.analysisText || '',
    priority: data?.priority || data?.targetInfo?.priority,
    mapImagePreview: data?.images?.map || data?.mapImagePreview || '',
  })
}

/** Column spec → table block. `footer` is passed to each column's `total()` to build a totals row. */
function tableBlock(columns, rows, { footer = null, emptyText = '' } = {}) {
  return {
    type: 'table',
    headers: columns.map(c => c.header),
    widths: columns.map(c => c.width || 1),
    align: columns.map(c => c.align || 'left'),
    rows: rows.map(row => columns.map(c => String(c.value(row) ?? '-'))),
    footer: footer ? columns.map(c => (c.total ? String(c.total(footer) ?? '') : '')) : null,
    emptyText,
  }
}

const textBlock = text => ({ type: 'text', text: String(text || '') })

// ---------------------------------------------------------------- report content

function allocationStatus(a) {
  return [
    a.confirmed ? 'เลือกแล้ว' : 'แนะนำ (JMEM)',
    a.overridden ? `ปรับจาก JMEM ${a.nJmem}` : '',
    a.laser ? 'ต้องชี้เป้าเลเซอร์' : '',
  ].filter(Boolean).join('\n')
}

function allocationBlocks(report) {
  const allocations = report.allocations || []
  if (!allocations.length) {
    const fallback = report.metrics?.weaponDetail && report.metrics.weaponDetail !== '-'
      ? `${report.mainRow?.weapon || '-'} (${report.metrics.weaponDetail})`
      : 'ยังไม่มีสินค้าใน Scenario สำหรับคำนวณ JMEM'
    return [textBlock(fallback)]
  }
  const showCost = allocations.some(a => a.unitCost > 0)
  const totals = report.allocationTotals || {}
  const columns = [
    { header: 'จุดเล็ง', width: 1.1, align: 'center', value: a => `${a.aimPoint}${a.isPrimary && allocations.length > 1 ? ' (หลัก)' : ''}`, total: () => 'รวม' },
    { header: 'สินค้า / อาวุธ', width: 2.6, value: a => a.productName },
    { header: 'น้ำหนัก/ลูก (lb)', width: 1.3, align: 'right', value: a => fmtInt(a.weightLb) },
    { header: 'จำนวน (ลูก)', width: 1.2, align: 'center', value: a => fmtInt(a.quantity), total: t => fmtInt(t.quantity) },
    { header: 'Pk ต่อลูก', width: 1.1, align: 'center', value: a => fmtPct(a.pkSingle) },
    { header: 'Pk(N)', width: 1.1, align: 'center', value: a => fmtPct(a.pkN) },
    ...(showCost
      ? [
          { header: 'ราคา/หน่วย', width: 1.4, align: 'right', value: a => fmtMoney(a.unitCost) },
          { header: 'ราคารวม', width: 1.5, align: 'right', value: a => fmtMoney(a.totalCost), total: t => fmtMoney(t.cost) },
        ]
      : []),
    { header: 'น้ำหนักรวม (lb)', width: 1.4, align: 'right', value: a => fmtInt(a.totalWeightLb), total: t => fmtInt(t.weightLb) },
    { header: 'สถานะ', width: 1.8, value: allocationStatus },
  ]
  const blocks = [tableBlock(columns, allocations, { footer: totals })]
  if (allocations.some(a => !a.confirmed)) {
    blocks.push({ type: 'note', text: '"แนะนำ (JMEM)" = ยังไม่ได้ยืนยันการเลือกสินค้า ระบบใช้สินค้าอันดับ 1 จาก JMEM ในการคำนวณ' })
  }
  return blocks
}

function missionRows(mission) {
  return [
    ['CEP', `${fmtInt(mission.cep_ft)} ft`],
    ['TLE', `${fmtInt(mission.tle_ft)} ft`],
    ['มุมตกกระทบ', `${fmtInt(mission.impact_angle_deg)}°`],
    ['การฝังตัว (Burial)', `${fmtInt(mission.burial_pct)}%`],
    ['ขนาดเป้าหมาย (ย×ก)', `${fmtInt(mission.target_length_ft)} × ${fmtInt(mission.target_width_ft)} ft`],
    ['Pk ที่ต้องการ', fmtPct(mission.pk_desired)],
    ['P(reliability)', fmtPct(mission.p_rel)],
    ['P(weapon)', fmtPct(mission.p_wpn)],
  ]
}

function targetReportBlocks(report) {
  const { mainRow, images = {}, generatedDate } = report
  const blocks = [
    { type: 'title', text: 'รายงานผลการวิเคราะห์ Weaponeering', subtitle: 'Weaponeering Analysis Report' },
    {
      type: 'meta',
      items: [
        ['Scenario', report.scenarioName],
        ['TGT', mainRow.tgt],
        ['วันที่จัดทำ', generatedDate],
      ].filter(([, value]) => value && value !== '-'),
    },
  ]

  if (hasImagePreview(images.target) || hasImagePreview(images.map)) {
    blocks.push({
      type: 'images',
      items: [
        { src: images.target, alt: 'ภาพเป้าหมาย' },
        { src: images.map, alt: 'แผนที่ปฏิบัติการ' },
      ],
    })
  }

  blocks.push({
    type: 'table',
    headers: MAIN_HEADERS,
    widths: MAIN_WIDTHS,
    align: MAIN_HEADERS.map(() => 'center'),
    rows: [[
      mainRow.tgt,
      mainRow.name,
      mainRow.pri,
      mainRow.coordinates,
      mainRow.elevation,
      mainRow.details,
      mainRow.desiredEffect,
      mainRow.weapon,
    ].map(v => String(v ?? '-'))],
  })

  if (report.targetRows?.length) {
    blocks.push({ type: 'heading', text: 'ข้อมูลเป้าหมาย' }, { type: 'kv', rows: report.targetRows, columns: 2 })
  }

  blocks.push({ type: 'heading', text: 'อาวุธที่เลือกใช้และจำนวน' }, ...allocationBlocks(report))

  if (report.mission) {
    blocks.push({ type: 'heading', text: 'ข้อมูลภารกิจ (JMEM)' }, { type: 'kv', rows: missionRows(report.mission), columns: 2 })
  }

  if (report.effectZones?.length) {
    blocks.push(
      { type: 'heading', text: 'รัศมีผลกระทบ (สินค้าอันดับ 1)' },
      tableBlock(
        [
          { header: 'โซน', width: 3, value: z => z.label_th || z.zone },
          { header: 'รัศมี (ม.)', width: 1.5, align: 'right', value: z => fmtInt(z.radius_m) },
          { header: 'รัศมี (ft)', width: 1.5, align: 'right', value: z => fmtInt(z.radius_ft) },
        ],
        report.effectZones,
      ),
    )
  }

  if (report.rankedProducts?.length) {
    const showCost = report.rankedProducts.some(p => p.unitCost > 0)
    blocks.push(
      { type: 'heading', text: 'สินค้าทางเลือก (จัดอันดับ JMEM)' },
      tableBlock(
        [
          { header: 'อันดับ', width: 0.8, align: 'center', value: p => p.rank },
          { header: 'สินค้า / อาวุธ', width: 2.6, value: p => `${p.productName}${p.selected ? ' ✓' : ''}` },
          { header: 'น้ำหนัก (lb)', width: 1.2, align: 'right', value: p => fmtInt(p.weightLb) },
          { header: 'Pd', width: 1, align: 'center', value: p => fmtPct(p.pd) },
          { header: 'Pk ต่อลูก', width: 1, align: 'center', value: p => fmtPct(p.pkSingle) },
          { header: 'จำนวน (N)', width: 1, align: 'center', value: p => fmtInt(p.quantity) },
          { header: 'Pk(N)', width: 1, align: 'center', value: p => fmtPct(p.pkN) },
          ...(showCost ? [{ header: 'ราคารวม', width: 1.4, align: 'right', value: p => fmtMoney(p.unitCost * p.quantity) }] : []),
        ],
        report.rankedProducts,
      ),
    )
  }

  if (report.warnings?.length) {
    blocks.push({ type: 'heading', text: 'หมายเหตุ / ข้อควรระวัง' }, textBlock(report.warnings.map(w => `• ${w}`).join('\n')))
  }

  if (!report.targetRows?.length && report.extraRows?.length) {
    const legacyRows = report.extraRows.filter(([label]) => label !== 'ผลการวิเคราะห์ AI')
    blocks.push({ type: 'heading', text: 'ข้อมูลเพิ่มเติม' }, { type: 'kv', rows: legacyRows, columns: 1 })
  }

  if (report.analysisText) {
    blocks.push({ type: 'heading', text: 'ผลการวิเคราะห์ AI' }, textBlock(report.analysisText))
  }

  return blocks
}

function scenarioReportBlocks(summary) {
  const { totals, products, targets } = summary
  const showCost = products.some(p => p.unitCost > 0)
  const priorityText = Object.entries(PRIORITY_LABELS)
    .map(([key, label]) => `${label} ${summary.priorityCounts[key] || 0}`)
    .join(' · ')
  const typeText = summary.typeCounts.map(([type, count]) => `${type} ${count}`).join(' · ') || '-'
  const recommendedOnly = summary.targetCount - summary.confirmedTargets - summary.targetsWithoutWeapon

  const blocks = [
    { type: 'title', text: 'รายงานภาพรวมการใช้อาวุธ Scenario', subtitle: 'Scenario Weapon Usage Summary' },
    { type: 'meta', items: [['Scenario', summary.scenarioName], ['วันที่จัดทำ', summary.generatedDate]] },
  ]
  if (summary.scenarioDescription) blocks.push(textBlock(summary.scenarioDescription))

  blocks.push({
    type: 'stats',
    items: [
      { label: 'เป้าหมาย', value: fmtInt(summary.targetCount) },
      { label: 'จุดเล็ง (DMPI)', value: fmtInt(summary.aimPointCount) },
      { label: 'อาวุธรวม (ลูก)', value: fmtInt(totals.quantity) },
      { label: 'ชนิดสินค้าที่ใช้', value: fmtInt(products.length) },
      ...(showCost ? [{ label: 'ค่าใช้จ่ายรวม', value: fmtMoney(totals.cost) }] : []),
      { label: 'น้ำหนักรวม (lb)', value: fmtInt(totals.weightLb) },
    ],
  })

  blocks.push({
    type: 'kv',
    columns: 1,
    rows: [
      ['ความสำคัญเป้าหมาย', priorityText],
      ['ประเภทเป้าหมาย', typeText],
      ['สถานะการเลือกสินค้า', `ยืนยันครบทุกจุดเล็ง ${summary.confirmedTargets} · ยังใช้ค่าแนะนำ JMEM (ทั้งหมด/บางจุด) ${recommendedOnly} · ยังไม่มีสินค้า ${summary.targetsWithoutWeapon} เป้าหมาย`],
    ],
  })

  blocks.push(
    { type: 'heading', text: 'สรุปการใช้อาวุธ/สินค้าทั้ง Scenario' },
    tableBlock(
      [
        { header: 'ที่', width: 0.6, align: 'center', value: p => products.indexOf(p) + 1, total: () => '' },
        { header: 'สินค้า / อาวุธ', width: 2.5, value: p => p.productName, total: () => 'รวมทั้งหมด' },
        { header: 'น้ำหนัก/ลูก (lb)', width: 1.2, align: 'right', value: p => fmtInt(p.weightLb) },
        { header: 'จำนวนที่ใช้ (ลูก)', width: 1.3, align: 'center', value: p => fmtInt(p.quantity), total: t => fmtInt(t.quantity) },
        { header: 'เป้าหมาย', width: 1.1, align: 'center', value: p => fmtInt(p.targetCount) },
        { header: 'จุดเล็ง', width: 0.9, align: 'center', value: p => fmtInt(p.aimPoints) },
        ...(showCost
          ? [
              { header: 'ราคา/หน่วย', width: 1.3, align: 'right', value: p => fmtMoney(p.unitCost) },
              { header: 'ราคารวม', width: 1.5, align: 'right', value: p => fmtMoney(p.totalCost), total: t => fmtMoney(t.cost) },
            ]
          : []),
        { header: 'น้ำหนักรวม (lb)', width: 1.4, align: 'right', value: p => fmtInt(p.totalWeightLb), total: t => fmtInt(t.weightLb) },
        ...(summary.hasInventory
          ? [
              { header: 'คงคลัง', width: 1, align: 'center', value: p => fmtInt(p.stock) },
              { header: 'คงเหลือหลังใช้', width: 1.2, align: 'center', value: p => (p.remaining < 0 ? `${fmtInt(p.remaining)} (ไม่พอ)` : fmtInt(p.remaining)) },
            ]
          : []),
      ],
      products,
      { footer: totals, emptyText: 'ยังไม่มีการใช้อาวุธใน Scenario นี้' },
    ),
  )

  if (summary.hasInventory && products.some(p => p.remaining < 0)) {
    blocks.push({ type: 'note', text: 'มีสินค้าบางรายการที่จำนวนคงคลังไม่พอสำหรับแผนนี้ (ค่าคงเหลือติดลบ)' })
  }

  const weaponLines = t => (t.allocations.length > 1
    ? t.allocations.map(a => `${a.aimPoint}: ${a.productName} × ${a.quantity}`).join('\n')
    : t.weapons)
  const pkLines = t => t.allocations.map(a => (t.allocations.length > 1 ? `${a.aimPoint}: ${fmtPct(a.pkN)}` : fmtPct(a.pkN))).join('\n') || '-'
  const statusText = t => ({
    none: 'ยังไม่มีสินค้า',
    confirmed: 'เลือกแล้ว',
    partial: 'เลือกบางจุด',
  }[t.selection] || 'แนะนำ (JMEM)')

  blocks.push(
    { type: 'heading', text: 'รายละเอียดการใช้อาวุธรายเป้าหมาย' },
    tableBlock(
      [
        { header: 'ที่', width: 0.55, align: 'center', value: t => targets.indexOf(t) + 1, total: () => '' },
        { header: 'เป้าหมาย', width: 1.4, value: t => t.label, total: () => 'รวม' },
        { header: 'PRI', width: 1.1, align: 'center', value: t => PRIORITY_LABELS[t.priority] || '-' },
        { header: 'ประเภท', width: 1.2, align: 'center', value: t => t.type },
        { header: 'พิกัด', width: 2.4, value: t => t.coordinates },
        { header: 'ผลลัพธ์ / Pk ที่ต้องการ', width: 1.9, value: t => `${t.desiredEffect}\nPk ${fmtPct(t.pkDesired)}` },
        { header: 'อาวุธที่ใช้', width: 1.9, value: weaponLines },
        { header: 'จำนวน (ลูก)', width: 0.9, align: 'center', value: t => fmtInt(t.quantity), total: x => fmtInt(x.quantity) },
        { header: 'Pk(N)', width: 1, align: 'center', value: pkLines },
        ...(showCost ? [{ header: 'ราคารวม', width: 1.3, align: 'right', value: t => fmtMoney(t.cost), total: x => fmtMoney(x.cost) }] : []),
        { header: 'สถานะ', width: 1.1, align: 'center', value: statusText },
      ],
      targets,
      { footer: totals, emptyText: 'ยังไม่มีเป้าหมายใน Scenario นี้' },
    ),
    { type: 'note', text: '"แนะนำ (JMEM)" = ยังไม่ได้ยืนยันการเลือกสินค้า ระบบใช้สินค้าอันดับ 1 จาก JMEM · จำนวนรวมนับทุกจุดเล็งของทุกเป้าหมายใน Scenario (ไม่ขึ้นกับตัวกรองหน้ารายงาน)' },
  )

  return blocks
}

// ---------------------------------------------------------------- PDF (HTML → canvas)

const PDF_CSS = `
  .pdf-report {
    width: ${PDF_WIDTH_PX}px;
    background: #ffffff;
    color: #${wordText};
    font-family: ${reportFontFamily};
    font-size: 19px;
    line-height: 1.35;
  }
  .pdf-report * { box-sizing: border-box; font-family: ${reportFontFamily}; }
  .pdf-report .pdf-block { margin: 0 0 12px; }
  .pdf-report .r-title h1 { margin: 0; color: #${wordBlue}; font-size: 34px; font-weight: 700; line-height: 1.2; }
  .pdf-report .r-title .r-subtitle { color: #${wordMuted}; font-size: 18px; }
  .pdf-report .r-meta { display: flex; flex-wrap: wrap; gap: 4px 22px; color: #${wordMuted}; font-size: 18px; }
  .pdf-report .r-meta b { color: #${wordText}; }
  .pdf-report .r-heading {
    margin: 18px 0 6px; padding-bottom: 3px;
    border-bottom: 2px solid #${wordBlue};
    color: #${wordBlue}; font-size: 24px; font-weight: 700;
  }
  .pdf-report table { width: 100%; border-collapse: collapse; table-layout: fixed; }
  .pdf-report th, .pdf-report td {
    border: 1px solid #${wordBorder};
    padding: 5px 7px;
    vertical-align: middle;
    font-size: 17px;
    word-break: break-word;
    white-space: pre-line;
  }
  .pdf-report .r-table thead th { background: #${wordBlue}; color: #ffffff; font-weight: 700; text-align: center; }
  .pdf-report .r-table tfoot td { background: #${wordTotalFill}; font-weight: 700; }
  .pdf-report .r-table .empty { color: #${wordMuted}; text-align: center; }
  .pdf-report .r-kv th { background: #${wordLabelFill}; color: #${wordText}; font-weight: 700; text-align: left; }
  .pdf-report .r-images td { height: 230px; padding: 0; text-align: center; }
  .pdf-report .r-images img { display: block; width: 100%; max-height: 230px; object-fit: contain; background: #f8fafc; }
  .pdf-report .image-placeholder { display: grid; place-items: center; min-height: 230px; color: #${wordMuted}; background: #f8fafc; font-size: 16px; }
  .pdf-report .r-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
  .pdf-report .r-stats div { padding: 8px 10px; border: 1px solid #${wordBorder}; border-top: 4px solid #${wordBlue}; }
  .pdf-report .r-stats strong { display: block; color: #${wordBlue}; font-size: 28px; line-height: 1.1; }
  .pdf-report .r-stats span { color: #${wordMuted}; font-size: 16px; }
  .pdf-report .r-text { padding: 8px 12px; border: 1px solid #${wordBorder}; }
  .pdf-report .pdf-line { min-height: 1.35em; white-space: pre-wrap; }
  .pdf-report .r-note { margin-top: -6px; color: #${wordMuted}; font-size: 16px; }
`

const PDF_BREAK_SELECTOR = '.pdf-block:not(.r-heading), tbody > tr, tfoot > tr, .pdf-line'

const cellHtml = value => escapeHtml(value ?? '-')

function colgroupHtml(widths) {
  const sum = widths.reduce((total, w) => total + w, 0) || 1
  return `<colgroup>${widths.map(w => `<col style="width:${((w / sum) * 100).toFixed(2)}%">`).join('')}</colgroup>`
}

function imageCellHtml(src, alt) {
  if (!hasImagePreview(src)) return `<div class="image-placeholder">${escapeHtml(alt)}</div>`
  return `<img src="${escapeHtml(src)}" alt="${escapeHtml(alt)}" />`
}

function blockToHtml(block) {
  switch (block.type) {
    case 'title':
      return `<header class="pdf-block r-title"><h1>${cellHtml(block.text)}</h1>${block.subtitle ? `<div class="r-subtitle">${cellHtml(block.subtitle)}</div>` : ''}</header>`
    case 'meta':
      return `<div class="pdf-block r-meta">${block.items.map(([label, value]) => `<span><b>${cellHtml(label)}:</b> ${cellHtml(value)}</span>`).join('')}</div>`
    case 'heading':
      return `<h2 class="pdf-block r-heading">${cellHtml(block.text)}</h2>`
    case 'note':
      return `<div class="pdf-block r-note">${cellHtml(block.text)}</div>`
    case 'text':
      return `<div class="pdf-block r-text">${block.text.split('\n').map(line => `<div class="pdf-line">${escapeHtml(line)}</div>`).join('')}</div>`
    case 'stats':
      return `<div class="pdf-block r-stats">${block.items.map(item => `<div><strong>${cellHtml(item.value)}</strong><span>${cellHtml(item.label)}</span></div>`).join('')}</div>`
    case 'images':
      return `<table class="pdf-block r-images"><tbody><tr>${block.items.map(item => `<td>${imageCellHtml(item.src, item.alt)}</td>`).join('')}</tr></tbody></table>`
    case 'kv': {
      const columns = block.columns || 1
      const widths = Array.from({ length: columns }, () => [1, columns === 1 ? 3.2 : 1.6]).flat()
      const rows = []
      for (let i = 0; i < block.rows.length; i += columns) {
        const pairs = block.rows.slice(i, i + columns)
        while (pairs.length < columns) pairs.push(['', ''])
        rows.push(`<tr>${pairs.map(([label, value]) => `<th>${cellHtml(label)}</th><td>${cellHtml(value)}</td>`).join('')}</tr>`)
      }
      return `<table class="pdf-block r-kv">${colgroupHtml(widths)}<tbody>${rows.join('')}</tbody></table>`
    }
    case 'table': {
      const td = (value, index) => `<td style="text-align:${block.align[index] || 'left'}">${cellHtml(value)}</td>`
      const body = block.rows.length
        ? block.rows.map(row => `<tr>${row.map(td).join('')}</tr>`).join('')
        : `<tr><td class="empty" colspan="${block.headers.length}">${cellHtml(block.emptyText || '-')}</td></tr>`
      const foot = block.footer && block.rows.length ? `<tfoot><tr>${block.footer.map(td).join('')}</tr></tfoot>` : ''
      return `<table class="pdf-block r-table">${colgroupHtml(block.widths)}<thead><tr>${block.headers.map(h => `<th>${cellHtml(h)}</th>`).join('')}</tr></thead><tbody>${body}</tbody>${foot}</table>`
    }
    default:
      return ''
  }
}

const waitForFonts = async () => {
  if (typeof document !== 'undefined' && document.fonts?.ready) {
    try {
      await document.fonts.ready
    } catch (_) {
      // ignore
    }
  }
}

const waitForImages = root => Promise.all(
  [...root.querySelectorAll('img')].map(img => (img.complete
    ? Promise.resolve()
    : new Promise(resolve => { img.onload = resolve; img.onerror = resolve }))),
)

/**
 * Split [0, total] into page slices, cutting only at row/block boundaries when possible.
 * A slice that starts inside a table body gets that table's header (`head`) repeated on top.
 */
function paginate(total, breaks, pageHeight, tables = []) {
  const candidates = [...new Set(breaks.map(b => Math.round(b)))]
    .filter(b => b > 0 && b < total)
    .sort((a, b) => a - b)
  const slices = []
  let start = 0
  while (total - start > 1) {
    const head = start > 0
      ? tables.find(t => start >= t.headBottom - 0.5 && start < t.bottom - 1) || null
      : null
    const available = pageHeight - (head ? head.headBottom - head.headTop : 0)
    const limit = start + available
    if (limit >= total) {
      slices.push({ start, end: total, head })
      break
    }
    let end = limit
    for (let i = candidates.length - 1; i >= 0; i -= 1) {
      const b = candidates[i]
      if (b <= limit && b > start + available * 0.25) {
        end = b
        break
      }
    }
    slices.push({ start, end, head })
    start = end
  }
  return slices
}

async function blocksToPdf(blocks, filename) {
  const { jsPDF } = await import('jspdf')
  const { default: html2canvas } = await import('html2canvas')

  const container = document.createElement('div')
  container.innerHTML = `<style>${PDF_CSS}</style><article class="pdf-report">${blocks.map(blockToHtml).join('')}</article>`
  Object.assign(container.style, {
    position: 'absolute',
    left: '0',
    top: '0',
    width: `${PDF_WIDTH_PX}px`,
    background: '#ffffff',
    pointerEvents: 'none',
    zIndex: '-1',
  })
  document.body.appendChild(container)

  try {
    await waitForFonts()
    await waitForImages(container)
    const article = container.querySelector('.pdf-report')
    const articleRect = article.getBoundingClientRect()
    const totalHeight = articleRect.height
    const breaks = [...article.querySelectorAll(PDF_BREAK_SELECTOR)]
      .map(el => el.getBoundingClientRect().bottom - articleRect.top)
    const tables = [...article.querySelectorAll('table.r-table')]
      .filter(table => table.tHead)
      .map((table) => {
        const head = table.tHead.getBoundingClientRect()
        return {
          headTop: head.top - articleRect.top,
          headBottom: head.bottom - articleRect.top,
          bottom: table.getBoundingClientRect().bottom - articleRect.top,
        }
      })

    const scale = Math.max(0.75, Math.min(2, 30000 / totalHeight))
    const canvas = await html2canvas(article, {
      scale,
      backgroundColor: '#ffffff',
      useCORS: true,
      logging: false,
      windowWidth: PDF_WIDTH_PX,
    })
    const ratio = canvas.height / totalHeight

    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const contentWidth = pageWidth - PDF_MARGIN_MM * 2
    const mmPerPx = contentWidth / PDF_WIDTH_PX
    const pageHeightPx = (pageHeight - PDF_MARGIN_MM * 2 - PDF_FOOTER_MM) / mmPerPx
    const slices = paginate(totalHeight, breaks, pageHeightPx, tables)

    const band = (from, to) => {
      const sy = Math.floor(from * ratio)
      return { sy, sh: Math.max(1, Math.min(canvas.height - sy, Math.ceil((to - from) * ratio))) }
    }

    slices.forEach(({ start, end, head }, index) => {
      if (index > 0) doc.addPage()
      const parts = [...(head ? [band(head.headTop, head.headBottom)] : []), band(start, end)]
      const slice = document.createElement('canvas')
      slice.width = canvas.width
      slice.height = parts.reduce((sum, part) => sum + part.sh, 0)
      const context = slice.getContext('2d')
      let dy = 0
      parts.forEach(({ sy, sh }) => {
        context.drawImage(canvas, 0, sy, canvas.width, sh, 0, dy, canvas.width, sh)
        dy += sh
      })
      doc.addImage(slice.toDataURL('image/jpeg', 0.92), 'JPEG', PDF_MARGIN_MM, PDF_MARGIN_MM, contentWidth, (slice.height / ratio) * mmPerPx)
      doc.setFontSize(9)
      doc.setTextColor(120)
      doc.text(`${index + 1} / ${slices.length}`, pageWidth - PDF_MARGIN_MM, pageHeight - PDF_MARGIN_MM / 2, { align: 'right' })
    })

    doc.save(filename)
  } finally {
    container.remove()
  }
}

// ---------------------------------------------------------------- Word (docx)

async function blocksToDocx(blocks, filename) {
  const {
    AlignmentType,
    BorderStyle,
    Document,
    Footer,
    ImageRun,
    Packer,
    PageNumber,
    Paragraph,
    Table,
    TableCell,
    TableLayoutType,
    TableRow,
    TextRun,
    VerticalAlign,
    WidthType,
  } = await import('docx')

  const line = { style: BorderStyle.SINGLE, size: 1, color: wordBorder }
  const tableBorders = { top: line, bottom: line, left: line, right: line, insideHorizontal: line, insideVertical: line }
  const alignOf = value => ({ center: AlignmentType.CENTER, right: AlignmentType.RIGHT }[value] || AlignmentType.LEFT)

  const runs = (text, options = {}) => String(text ?? '-').split('\n').map((part, index) => new TextRun({
    text: part,
    break: index > 0 ? 1 : undefined,
    font: wordFont,
    size: options.size || 28,
    bold: Boolean(options.bold),
    color: options.color || wordText,
  }))

  const paragraph = (text, options = {}) => new Paragraph({
    alignment: alignOf(options.align),
    spacing: options.spacing,
    children: runs(text, options),
  })

  const cell = (text, width, options = {}) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: options.fill ? { fill: options.fill } : undefined,
    columnSpan: options.span,
    margins: { top: 50, bottom: 50, left: 100, right: 100 },
    verticalAlign: VerticalAlign.CENTER,
    children: [paragraph(text, options)],
  })

  const scaleWidths = (weights) => {
    const sum = weights.reduce((total, w) => total + w, 0) || 1
    return weights.map(w => Math.round((w / sum) * DOCX_CONTENT_DXA))
  }

  const table = (widths, rows) => new Table({
    width: { size: DOCX_CONTENT_DXA, type: WidthType.DXA },
    columnWidths: widths,
    layout: TableLayoutType.FIXED,
    borders: tableBorders,
    rows,
  })

  const imageParagraph = (src, fallbackText) => {
    if (!hasImagePreview(src)) {
      return paragraph(fallbackText, { align: 'center', size: 22, color: wordMuted })
    }
    return new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new ImageRun({
        type: imageTypeFromDataUrl(src),
        data: dataUrlToUint8Array(src),
        transformation: { width: 320, height: 200 },
      })],
    })
  }

  const spacer = () => new Paragraph({ spacing: { after: 80 } })

  const children = []
  blocks.forEach((block) => {
    switch (block.type) {
      case 'title':
        children.push(paragraph(block.text, { bold: true, color: wordBlue, size: 40 }))
        if (block.subtitle) children.push(paragraph(block.subtitle, { color: wordMuted, size: 24 }))
        break
      case 'meta':
        children.push(paragraph(block.items.map(([label, value]) => `${label}: ${value}`).join('     '), {
          color: wordMuted,
          size: 24,
          spacing: { after: 120 },
        }))
        break
      case 'heading':
        children.push(paragraph(block.text, { bold: true, color: wordBlue, size: 32, spacing: { before: 240, after: 80 } }))
        break
      case 'note':
        children.push(paragraph(block.text, { color: wordMuted, size: 22, spacing: { before: 40, after: 80 } }))
        break
      case 'text':
        children.push(table([DOCX_CONTENT_DXA], [new TableRow({ children: [cell(block.text, DOCX_CONTENT_DXA)] })]), spacer())
        break
      case 'stats': {
        const widths = scaleWidths(block.items.map(() => 1))
        children.push(table(widths, [new TableRow({
          children: block.items.map((item, index) => new TableCell({
            width: { size: widths[index], type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [
              paragraph(item.value, { bold: true, color: wordBlue, size: 40, align: 'center' }),
              paragraph(item.label, { color: wordMuted, size: 24, align: 'center' }),
            ],
          })),
        })]), spacer())
        break
      }
      case 'images': {
        const widths = scaleWidths(block.items.map(() => 1))
        children.push(table(widths, [new TableRow({
          height: { value: 4700, rule: 'exact' },
          children: block.items.map((item, index) => new TableCell({
            width: { size: widths[index], type: WidthType.DXA },
            verticalAlign: VerticalAlign.CENTER,
            children: [imageParagraph(item.src, item.alt)],
          })),
        })]), spacer())
        break
      }
      case 'kv': {
        const columns = block.columns || 1
        const widths = scaleWidths(Array.from({ length: columns }, () => [1, columns === 1 ? 3.2 : 1.6]).flat())
        const rows = []
        for (let i = 0; i < block.rows.length; i += columns) {
          const pairs = block.rows.slice(i, i + columns)
          while (pairs.length < columns) pairs.push(['', ''])
          rows.push(new TableRow({
            children: pairs.flatMap(([label, value], index) => [
              cell(label, widths[index * 2], { bold: true, fill: wordLabelFill }),
              cell(value, widths[index * 2 + 1]),
            ]),
          }))
        }
        children.push(table(widths, rows), spacer())
        break
      }
      case 'table': {
        const widths = scaleWidths(block.widths)
        const rows = [new TableRow({
          tableHeader: true,
          children: block.headers.map((header, index) => cell(header, widths[index], {
            bold: true,
            color: 'FFFFFF',
            fill: wordBlue,
            align: 'center',
          })),
        })]
        if (block.rows.length) {
          block.rows.forEach((row) => {
            rows.push(new TableRow({
              cantSplit: true,
              children: row.map((value, index) => cell(value, widths[index], { align: block.align[index] })),
            }))
          })
          if (block.footer) {
            rows.push(new TableRow({
              cantSplit: true,
              children: block.footer.map((value, index) => cell(value, widths[index], {
                bold: true,
                fill: wordTotalFill,
                align: block.align[index],
              })),
            }))
          }
        } else {
          rows.push(new TableRow({
            children: [cell(block.emptyText || '-', DOCX_CONTENT_DXA, { span: block.headers.length, align: 'center', color: wordMuted })],
          }))
        }
        children.push(table(widths, rows), spacer())
        break
      }
      default:
        break
    }
  })

  const doc = new Document({
    styles: { default: { document: { run: { font: wordFont, size: 28 } } } },
    sections: [{
      properties: {
        page: {
          size: { orientation: 'landscape' },
          margin: { top: 720, right: 720, bottom: 720, left: 720 },
        },
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [new TextRun({
              children: ['หน้า ', PageNumber.CURRENT, ' / ', PageNumber.TOTAL_PAGES],
              font: wordFont,
              size: 22,
              color: wordMuted,
            })],
          })],
        }),
      },
      children,
    }],
  })

  const blob = await Packer.toBlob(doc)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function runExport(label, task) {
  try {
    await task()
    return true
  } catch (error) {
    console.error(`${label} Export Error:`, error)
    throw new Error(`ไม่สามารถส่งออก ${label}: ${error.message}`)
  }
}

export const exportService = {
  buildTargetExportPayload,

  exportToPDF(data, filename = 'weaponeering_analysis.pdf') {
    return runExport('PDF', () => blocksToPdf(targetReportBlocks(normalizeExportData(data)), filename))
  },

  exportToWord(data, filename = 'weaponeering_analysis.docx') {
    return runExport('Word', () => blocksToDocx(targetReportBlocks(normalizeExportData(data)), filename))
  },

  /** summary: output of buildScenarioSummary() */
  exportScenarioToPDF(summary, filename = 'scenario_summary.pdf') {
    return runExport('PDF', () => blocksToPdf(scenarioReportBlocks(summary), filename))
  },

  exportScenarioToWord(summary, filename = 'scenario_summary.docx') {
    return runExport('Word', () => blocksToDocx(scenarioReportBlocks(summary), filename))
  },
}
