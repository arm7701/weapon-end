/** Weapon allocations per target and scenario-wide usage totals for PDF/Word reports. */

import { formatAllCoordinates } from './coordinateParser'

export const PRIORITY_LABELS = { red: 'สำคัญสูง', orange: 'สำคัญ', green: 'ทั่วไป' }

const num = (value) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

function pickProduct(products = []) {
  return products.find((p) => p.selected) || products[0] || null
}

function allocationFromProduct(product, { aimPoint, isPrimary, confirmed }) {
  const quantity = Math.max(0, Math.round(num(product.n_required)))
  const unitCost = num(product.unit_cost)
  const weightLb = num(product.weight_pounds)
  return {
    aimPoint,
    isPrimary,
    confirmed,
    productId: String(product.product_id || ''),
    productName: product.product_name || '—',
    weightLb,
    quantity,
    nJmem: Math.round(num(product.n_jmem ?? product.n_required)),
    overridden: Boolean(product.quantity_overridden),
    pd: num(product.pd_base),
    pkSingle: num(product.pk_single),
    pkN: num(product.pk_n),
    unitCost,
    totalCost: unitCost * quantity,
    totalWeightLb: weightLb * quantity,
    laser: Boolean(product.requires_laser_designation),
  }
}

/**
 * One allocation per aim point (DMPI): the selected product, or JMEM rank #1 when nothing is selected yet.
 * `confirmed` is true only when a product was explicitly selected for that aim point / target.
 */
export function weaponAllocationsFromJmem(jmem) {
  if (!jmem) return []
  const coords = Array.isArray(jmem.coordinate_products) ? jmem.coordinate_products : []
  if (coords.length) {
    return coords
      .map((coord, index) => {
        const product = pickProduct(coord.products?.length ? coord.products : jmem.products || [])
        if (!product) return null
        return allocationFromProduct(product, {
          aimPoint: coord.label || `P${index + 1}`,
          isPrimary: Boolean(coord.is_primary),
          confirmed: Boolean(coord.selected_product_id),
        })
      })
      .filter(Boolean)
  }
  const product = pickProduct(jmem.products || [])
  if (!product) return []
  return [
    allocationFromProduct(product, {
      aimPoint: 'P1',
      isPrimary: true,
      confirmed: Boolean(jmem.selected_product_id),
    }),
  ]
}

export function allocationTotals(allocations = []) {
  return allocations.reduce(
    (total, a) => ({
      quantity: total.quantity + a.quantity,
      cost: total.cost + a.totalCost,
      weightLb: total.weightLb + a.totalWeightLb,
    }),
    { quantity: 0, cost: 0, weightLb: 0 },
  )
}

/** "GBU-12 × 2, Mk-82 × 4" */
export function weaponSummaryText(allocations = []) {
  const byProduct = new Map()
  allocations.forEach((a) => {
    byProduct.set(a.productName, (byProduct.get(a.productName) || 0) + a.quantity)
  })
  return [...byProduct.entries()].map(([name, qty]) => `${name} × ${qty}`).join(', ')
}

function priorityKey(draft, card) {
  if (draft?.targetPriority) return draft.targetPriority
  const score = Number(card?.priority_score)
  if (!Number.isFinite(score)) return ''
  if (score >= 4) return 'red'
  if (score === 3) return 'orange'
  return 'green'
}

function coordinateText(draft) {
  const all = formatAllCoordinates(draft?.latitude, draft?.longitude)
  return all ? `${all.DD}\n${all.MGRS}` : '-'
}

/**
 * Roll up every target's allocations into per-product usage for the scenario.
 * items: [{ card, draft, jmem }]; inventory: GET /wing-depot-inventory/details rows (optional).
 */
export function buildScenarioSummary({ scenario = null, items = [], inventory = null } = {}) {
  const productRows = new Map()
  const priorityCounts = { red: 0, orange: 0, green: 0 }
  const typeCounts = new Map()
  const targets = []
  let aimPointCount = 0
  let confirmedTargets = 0
  let targetsWithoutWeapon = 0

  items.forEach(({ card, draft, jmem }) => {
    const allocations = weaponAllocationsFromJmem(jmem)
    const totals = allocationTotals(allocations)
    const priority = priorityKey(draft, card)
    if (priority in priorityCounts) priorityCounts[priority] += 1
    const type = draft?.targetType || card?.target_type || '-'
    typeCounts.set(type, (typeCounts.get(type) || 0) + 1)
    aimPointCount += Math.max(allocations.length, card?.coordinates?.length || 0, 1)
    const confirmedCount = allocations.filter((a) => a.confirmed).length
    const selection = !allocations.length
      ? 'none'
      : confirmedCount === allocations.length ? 'confirmed' : confirmedCount ? 'partial' : 'recommended'
    if (selection === 'none') targetsWithoutWeapon += 1
    else if (selection === 'confirmed') confirmedTargets += 1

    allocations.forEach((a) => {
      const key = a.productId || a.productName
      const row = productRows.get(key) || {
        productId: a.productId,
        productName: a.productName,
        weightLb: a.weightLb,
        unitCost: a.unitCost,
        quantity: 0,
        totalCost: 0,
        totalWeightLb: 0,
        aimPoints: 0,
        targetIds: new Set(),
      }
      row.quantity += a.quantity
      row.totalCost += a.totalCost
      row.totalWeightLb += a.totalWeightLb
      row.aimPoints += 1
      row.targetIds.add(card?.id || draft?.id)
      productRows.set(key, row)
    })

    targets.push({
      id: card?.id || draft?.id,
      label: draft?.label || card?.label || '-',
      priority,
      priorityScore: Number(card?.priority_score) || 0,
      type,
      coordinates: coordinateText(draft),
      desiredEffect: draft?.desiredEffect || '-',
      pkDesired: draft?.pk,
      allocations,
      weapons: weaponSummaryText(allocations) || 'ยังไม่มีสินค้า',
      quantity: totals.quantity,
      cost: totals.cost,
      weightLb: totals.weightLb,
      selection,
    })
  })

  const stockByProduct = new Map()
  const hasInventory = Array.isArray(inventory) && inventory.length > 0
  if (hasInventory) {
    inventory.forEach((row) => {
      const key = String(row.product_id)
      stockByProduct.set(key, (stockByProduct.get(key) || 0) + num(row.quantity))
    })
  }

  const products = [...productRows.values()]
    .map(({ targetIds, ...row }) => {
      const stock = hasInventory ? stockByProduct.get(row.productId) || 0 : null
      return {
        ...row,
        targetCount: targetIds.size,
        stock,
        remaining: stock == null ? null : stock - row.quantity,
      }
    })
    .sort((a, b) => b.quantity - a.quantity || a.productName.localeCompare(b.productName))

  targets.sort((a, b) => b.priorityScore - a.priorityScore || a.label.localeCompare(b.label, 'th', { numeric: true }))

  return {
    scenarioName: scenario?.name || '-',
    scenarioDescription: scenario?.description || '',
    generatedDate: new Date().toLocaleString('th-TH'),
    targetCount: items.length,
    aimPointCount,
    confirmedTargets,
    targetsWithoutWeapon,
    priorityCounts,
    typeCounts: [...typeCounts.entries()].sort((a, b) => b[1] - a[1]),
    products,
    hasInventory,
    totals: allocationTotals(products.map((p) => ({ quantity: p.quantity, totalCost: p.totalCost, totalWeightLb: p.totalWeightLb }))),
    targets,
  }
}
