import { apiJson, listResource } from './api'
import { targetApiToFormDraft } from '../utils/targetFormMapper'
import { buildScenarioSummary } from '../utils/reportData'

const FETCH_CONCURRENCY = 6

async function mapLimit(items, limit, fn) {
  const results = new Array(items.length)
  let next = 0
  const worker = async () => {
    while (next < items.length) {
      const index = next
      next += 1
      results[index] = await fn(items[index], index)
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker))
  return results
}

/** Full target card + JMEM ranking (selected product / quantity per aim point). */
export async function fetchTargetReportData(targetId) {
  const [card, jmem] = await Promise.all([
    apiJson(`/targets/${targetId}`),
    apiJson(`/jmem/targets/${targetId}`).catch(() => null),
  ])
  return { card, jmem }
}

export async function fetchScenarioInfo(scenarioId) {
  return apiJson(`/scenarios/${scenarioId}`).catch(() => null)
}

/** [{ card, draft, jmem }] for every active target in the scenario. */
export async function fetchScenarioReportItems(scenarioId) {
  const list = (await listResource('/targets', { scenario_id: scenarioId, status: 'active' })) || []
  return mapLimit(list, FETCH_CONCURRENCY, async (item) => {
    const { card, jmem } = await fetchTargetReportData(item.id).catch(() => ({ card: item, jmem: null }))
    return { card, draft: targetApiToFormDraft(card), jmem }
  })
}

/** Scenario-wide weapon usage summary; pass already-loaded `items` to skip refetching targets. */
export async function fetchScenarioSummary(scenarioId, items = null) {
  const [scenario, inventory, rows] = await Promise.all([
    fetchScenarioInfo(scenarioId),
    listResource('/wing-depot-inventory/details', { scenario_id: scenarioId }).catch(() => null),
    items || fetchScenarioReportItems(scenarioId),
  ])
  return buildScenarioSummary({ scenario, items: rows, inventory })
}
